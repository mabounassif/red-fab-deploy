
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

        if not env.config_object.has_section(self.section):
            env.config_object.add_section(self.section)
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


class UpdateSecurityGroup(Task):
    """
    create security group if it does not exist

    Two security groups will be created.  app-sg and db-sg.

    app-sg will enable access to ports 80 and 22 from everywhere.
    instances belong to this group can access each other freely, because there
    may be other services (for example, cache) require some ports open.

    db-sg has only port 5432 and 6432 open to instances in app-sg and db-sg.

    please use internal ips in your django settings files when specifying
    database settings.
    """
    name = 'create_sg'
    serial = True

    dict = {
        'app-server':   'app_server',
        'dev-sever':    'dev_server',
        'db-server':    'db_server',
        'slave-db':     'slave_db'
    }

    def _get_lb_sg(self, **kwargs):
        elb_conn = get_ec2_connection(server_type='elb', **kwargs)
        elb = elb_conn.get_all_load_balancers()[0]
        return elb.source_security_group

    def run(self, section=None, **kwargs):
        conf = env.config_object
        conn = get_ec2_connection(server_type='ec2', **kwargs)

        if section:
            sections = [section]
        else:
            sections = conf.sections()

        for section in sections:
            if not self.dict.has_key(section):
                continue

            host_sg = get_security_group(conn, self.dict.get(section))

            open_ports = conf.get_list(section, conf.OPEN_PORTS)
            if open_ports:
                for port in open_ports:
                    try:
                        host_sg.authorize('tcp', port, port, '0.0.0.0/0')
                    except:
                        pass

            restricted_ports = conf.get_list(section, conf.RESTRICTED_PORTS)
            if restricted_ports:
                for s in conf.get_list(section, conf.ALLOWED_SECTIONS):
                    if s == 'load-balancer':
                        guest_sg = self._get_lb_sg(**kwargs)
                    else:
                        guest_sg = get_security_group(conn, self.dict.get(s))

                    for port in restricted_ports:
                        try:
                            if s == 'load-balancer':
                                conn.authorize_security_group(host_sg.name,
                                      src_security_group_name='amazon-elb-sg',
                                      src_security_group_owner_id='amazon-elb',
                                      from_port=port, to_port=port,
                                      ip_protocol='tcp')
                            else:
                                host_sg.authorize('tcp', port, port, src_group=guest_sg)

                        except:
                            pass


create_key = CreateKeyPair()
add_server = New()
update_sg = UpdateSecurityGroup()
