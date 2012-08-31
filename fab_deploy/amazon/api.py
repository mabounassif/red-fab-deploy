
import os, sys
import time
import boto
from boto import ec2
from boto.ec2 import elb
from boto.ec2.connection import EC2Connection
from boto.ec2.elb import HealthCheck

from fabric.api import env, execute, local
from fabric.tasks import Task

from fab_deploy import functions

from utils import  get_security_group, select_instance_type


DEFAULT_AMI     = 'ami-5965401c' # ubuntu 12.04 x86_64
DEFAULT_INSTANCE_TYPE = 'm1.medium'
DEFAULT_REGION  = 'us-west-1'


def get_ec2_connection(server_type, **kwargs):
    """
    create a connection to aws.
    aws_access_key and aws_secret_key should be defined in fabfile,
    or given at the command line
    """

    aws_access_key = kwargs.get('aws_access_key', env.get('aws_access_key'))
    aws_secret_key = kwargs.get('aws_secret_key', env.get('aws_secret_key'))

    if not aws_access_key or not aws_secret_key:
        print "You must specify your amazon aws credentials to your env."
        sys.exit()

    region = kwargs.get('region', env.get('region'))
    if not region:
        region = DEFAULT_REGION

    if server_type == 'ec2':
        conn = ec2.connect_to_region(region,
                                          aws_access_key_id=aws_access_key,
                                          aws_secret_access_key=aws_secret_key)
        return conn
    elif server_type == 'elb':
        conn = elb.connect_to_region(region,
                                     aws_access_key_id=aws_access_key,
                                     aws_secret_access_key=aws_secret_key)
        return conn


class CreateKeyPair(Task):
    """
    create an aws key pair

    This key will be stored under  $PROJECT_ROOT/deploy/ directory and
    registered in server.ini file. You will need it to access all the
    instances created with it.

    * **aws_access_key**:  aws access key id
    * **aws_secret_key**:  aws secret key
    """

    name = 'create_key'
    serial = True

    section = 'amazon-aws'

    def run(self, **kwargs):
        conn = get_ec2_connection(server_type='ec2', **kwargs)
        sys.stdout.write("Please give a name to the key: ")

        key_dir = os.path.join(env.project_path, 'deploy')
        while True:
            key_name = raw_input()
            key_file = os.path.join(key_dir, key_name+'.pem')
            key = conn.get_key_pair(key_name)

            if key:
                if os.path.exists(key_file):
                    print ("Looks like key file %s already exists on your "
                           "machine. I will skip creating, and just use it."
                           %key_file)
                    break
                else:
                    print ("Key '%s' already exist on AWS, but I couldn't "
                           "find it at %s. We need to create a new key, please"
                           "give a name to the key: " %(key.name, key_file))
                    continue
            else:
                key = conn.create_key_pair(key_name)
                key.save(key_dir)
                break

        env.config_object.set(self.section,
                              env.config_object.EC2_KEY_NAME, key.name)
        env.config_object.set(self.section,
                              env.config_object.EC2_KEY_FILE, key_file)
        env.config_object.save(env.conf_filename)
        local('ssh-add %s' %key_file)


class New(Task):
    """
    Provisions and set up a new amazon AWS EC2 instance

    You may provide the following parameters through command line.

    * **aws_access_key**:  aws access key id
    * **aws_secret_key**:  aws secret key

    * **type**:  Required. server types, can be db_server, app_server,
                 dev_server, or slave_db

    * **ami_id**: AMI ID

    * **select_instance_type**:  'yes' or 'no'
                by default, m1.medium will be used. Use 'yes' to
                select instance type by yourself.

    * **static_ip**: 'yes' or 'no'
            by default, an elastic static ip will be allocated and
            associated with the created instance.  Use 'no' to disable it.

    * **region**:     default is us-west-1
    """

    name = 'add_server'
    serial = True

    def run(self, **kwargs):
        assert not env.hosts
        conn = get_ec2_connection(server_type='ec2', **kwargs)

        type = kwargs.get('type')
        setup_name = 'setup.%s' % type

        if kwargs.get('select_instance_type', '').lower() == 'yes':
            instance_type = select_instance_type()
        else:
            instance_type = DEFAULT_INSTANCE_TYPE

        ami_id = kwargs.get('ami_id')
        if not ami_id:
            ami_id = DEFAULT_AMI

        task = functions.get_task_instance(setup_name)
        if task:
            if hasattr(task, 'instance_type'):
                instance_type = task.instance_type
            if hasattr(task, 'ami'):
                ami_id = task.ami
        else:
            print "I don't know how to add a %s server" % type
            sys.exit()

        key_name = env.config_object.get('amazon-aws',
                                         env.config_object.EC2_KEY_NAME)
        key_file = env.config_object.get('amazon-aws',
                                         env.config_object.EC2_KEY_FILE)
        if not key_name:
            print "Sorry. You need to create key pair with create_key first."
            sys.exit()
        elif not os.path.exists(key_file):
            print ("I find key %s in server.ini file, but the key file is not"
                   " on its location %s. There is something wrong. Please fix "
                   "it, or recreate key pair" % (key_name, key_file))
            sys.exit()

        image = conn.get_image(ami_id)
        security_group = get_security_group(conn, type)

        name = functions.get_remote_name(None, task.config_section,
                                         name=kwargs.get('name'))
        SERVER = {
            'image_id':         image.id,
            'instance_type':    instance_type,
            'security_groups':  [security_group],
            'key_name':         key_name,}

        reservation = conn.run_instances(**SERVER)
        print reservation

        instance = reservation.instances[0]
        while instance.state != 'running':
            time.sleep(5)
            instance.update()
            print "...instance state: %s" % (instance.state)

        conn.create_tags([instance.id], {"Name": name})

        if kwargs.get('static_ip', '').lower() == 'no':
            ip = instance.ip_address
        else:
            elastic_ip = conn.allocate_address()
            print "...Elastic IP %s allocated" % elastic_ip
            elastic_ip.associate(instance.id)
            ip = elastic_ip.public_ip

        print "...EC2 instance is successfully created."
        print "...wait 5 seconds for the server to be ready"
        print "...while waiting, you may want to note down the following info"
        time.sleep(5)
        print "..."
        print "...Instance using image: %s" % image.name
        print "...Added into security group: %s" %security_group.name
        print "...Instance ID: %s" % instance.id
        print "...Public IP: %s" % ip

        host_string = 'ubuntu@%s' % ip
        execute(setup_name, name=name, hosts=[host_string])


class LBSetup(Task):
    """
    Set up a load balancer

    Create a elastic load balancer, read connections info from server.ini,
    get ip address and look for corresponding ec2 instances, and finally
    register the instances with load balancer.

    you may define the following optional arguments:
    * **aws_access_key**:  aws access key id
    * **aws_secret_key**:  aws secret key
    * **lb_name**:    name of load_balancer
    * **listeners**:  listeners of load balancer, a list of tuple
                (lb port, instance port, protocol).
    * **hc_policy**:  a dictionary defining the health check policy, keys can be
                interval, target, healthy_threshold, timeout
                and unhealthy_threshold

    """

    name = 'update_lb'

    hc_policy = {
                'interval': 30,
                'target':   'HTTP:80/index.html', }

    listeners =  [(80, 80, 'http',)]

    def get_instance_id_by_ip(self, ip, **kwargs):
        """
        get ec2 instance id based on ip address
        """
        instances = []
        conn = get_ec2_connection(server_type='ec2', **kwargs)
        reservations = conn.get_all_instances()
        for resv in reservations:
            for instance in resv.instances:
                if instance.ip_address == ip:
                    instances.append(instance.id)
        return instances

    def _get_elb(self, conn, lb_name):
        lbs = conn.get_all_load_balancers()
        for lb in lbs:
            if lb.name == lb_name:
                return lb
        return None

    def run(self, section, **kwargs):
        conn = get_ec2_connection(server_type='ec2', **kwargs)
        elb_conn = get_ec2_connection(server_type='elb', **kwargs)

        zones = [ z.name for z in conn.get_all_zones()]

        lb_name = env.get('lb_name')
        if not lb_name:
            lb_name = env.project_name

        listeners = env.get('listeners')
        if not listeners:
            listeners = self.listeners

        connections = env.config_object.get_list(section,
                                                 env.config_object.CONNECTIONS)
        ips = [ ip.split('@')[-1] for ip in connections]
        for ip in ips:
            instances = self.get_instance_id_by_ip(ip, **kwargs)
            if len(instances) == 0:
                print "Cannot find any ec2 instances match your connections"
                sys.exit()

        elb = self._get_elb(elb_conn, lb_name)
        print "find load balancer %s" %lb_name
        if not elb:
            elb = elb_conn.create_load_balancer(lb_name, zones, listeners)
            print "load balancer %s successfully created" %lb_name

        elb.register_instances(instances)
        print "register instances into load balancer"
        print instances

        hc_policy = env.get('hc_policy')
        if not hc_policy:
            hc_policy = self.hc_policy
        print "Configure load balancer health check policy"
        print hc
        hc = HealthCheck(**hc_policy)
        elb.configure_health_check(hc)


create_key = CreateKeyPair()
add_server = New()
update_lb = LBSetup()
