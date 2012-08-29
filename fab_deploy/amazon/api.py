
import os, sys
import time
import boto
from boto.ec2.connection import EC2Connection

from fabric.api import env, execute, local
from fabric.tasks import Task

from fab_deploy import functions

DEFAULT_REGION  = 'us-west-1'
DEFAULT_AMI     = 'ami-5965401c' # ubuntu 12.04 x86_64
DEFAULT_INSTANCE_TYPE = 'm1.medium'


def select_instance_type():
    """
    select a type of AWS EC2 instance
    """

    INSTANCE_TYPES = (
        ('t1.micro',      'Up to 2 ECUs  1 core   613MB',  'Micro'),
        ('m1.small',      '1 ECU         1 core   1.7GB',  'Small'),
        ('m1.medium',     '2 ECUs        1 core   3.7GB',  'Medium'),
        ('m1.large',      '4 ECUs        2 core   7.5GB',  'Large'),
        ('m1.xlarge',     '8 ECUs        4 cores  15GB',   'Extra Large'),
        ('c1.medium',     '5 ECUs        2 cores  1.7GB',  'High-CPU Medium'),
        ('c1.xlarge',     '20 ECUs       8 cores  7 GB',   'High-CPU Extra Large'),
        ('m2.xlarge',     '6.5 ECUs      2 cores  17.1GB', 'High-Memory Extra Large'),
        ('m2.2xlarge',    '13 ECUs       4 cores  34.2GB', 'High-Memory Double Extra Large'),
        ('m2.4xlarge',    '26 ECUs       8 cores  68.4GB', 'High-Memory Quadruple Extra Large'),
    )

    n = len(INSTANCE_TYPES)
    for i in range(n):
        type = INSTANCE_TYPES[i]
        print "[ %d ]:\t%s\t%s\t%s" %(i+1, type[0], type[1], type[2])
    sys.stdout.write("These types of instance are available, which one do you want to create?: ")

    while True:
        try:
            num = int(raw_input())
        except:
            print "Please input a valid number from 0 to %d: " %n
        return INSTANCE_TYPES[num-1][0]


def get_ec2_connection():
        aws_access_key = env.get('aws_access_key')
        aws_secret_key = env.get('aws_secret_key')

        if not aws_access_key or not aws_secret_key:
            print "You must specify your amazon aws credentials to your env."
            sys.exit()

        if not env.get('region'):
            region = DEFAULT_REGION

        conn = boto.ec2.connect_to_region(region,
                                          aws_access_key_id=aws_access_key,
                                          aws_secret_access_key=aws_secret_key)
        return conn


class CreateKeyPair(Task):
    """
    create an aws key pair

    This key will be stored under  $PROJECT_ROOT/deploy/ directory and
    registered in server.ini file. You will need it to access all the
    instances created with it.
    """

    name = 'create_key'
    section = 'amazon-aws'

    def run(self, **kwargs):
        conn = get_ec2_connection()
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


def get_or_create_security_group(conn, type):
    """
    """
    if type == 'app-server' or type == 'lb-server':
        groups = conn.get_all_security_groups(groupnames=['app-sg'])
        if groups:
            return groups[0]
        grp = conn.create_security_group('app-sg', 'security group for app-server')
        grp.authorize('tcp', 80, 80, '0.0.0.0/0')
        grp.authorize('tcp', 22, 22, '0.0.0.0/0')

    elif type == 'db-server' or type == 'slave_db':
        groups = conn.get_all_security_groups(groupnames=['db-sg'])
        if groups:
            return groups[0]
        grp = conn.create_security_group('db-sg', 'security group for db-server')
        grp.authorize('tcp', 22, 22, '0.0.0.0/0')
        # grp.authorize('tcp', 6432, 6432, '0.0.0.0/0')
    return grp


class New(Task):
    """
    Provisions and set up a new amazon aws ec2 instance
    """

    name = 'add_server'
    serial = True

    def run(self, **kwargs):
        assert not env.hosts

        conn = get_ec2_connection()

        type = kwargs.get('type')
        setup_name = 'setup.%s' % type

        instance_type = DEFAULT_INSTANCE_TYPE
        ami_id        = DEFAULT_AMI

        task = functions.get_task_instance(setup_name)
        if task:
            if hasattr(task, 'instance_type'):
                instance_type = task.instance_type
            if hasattr(task, 'ami'):
                ami_id = task.ami
        else:
            print "I don't know how to add a %s server" % type
            sys.exit()

        key_name = env.config_object.get('amazon-aws', env.config_object.EC2_KEY)
        key_file = env.config_object.get('amazon-aws', env.config_object.EC2_KEY_FILE)
        if not key_name:
            print "Sorry. You need to create key pair with create_key first."
            sys.exit()
        elif not os.path.exists(key_file):
            print ("I find key %s in server.ini file, but the key file is not"
                   " on its location %s. There is something wrong. Please fix "
                   "it, or recreate key pair" % (key_name, key_file))
            sys.exit()

        image = conn.get_image(ami_id)
        security_group = get_or_create_security_group(conn, type)
        SERVER = {
            'image_id':         image.id,
            'instance_type':    instance_type,
            'security_groups':  [security_group],
            'key_name':         key_name, }

        reservation = conn.run_instances(**SERVER)
        print reservation

        instance = reservation.instances[0]
        while instance.state != 'running':
            time.sleep(5)
            instance.update()
            print "instance state: %s" % (instance.state)

        static_ip = kwargs.get('static_ip', 'True')
        if static_ip == 'True':
            elastic_ip = conn.allocate_address()
            print "Elastic IP %s allocated" % elastic_ip
            elastic_ip.associate(instance.id)

        print "EC2 instance is successfully created."
        print "Using image %s" % image.name
        print "Added into security group %s" %security_group.name
        print "id: %s" % instance.id
        print "IP: %s" % instance.ip_address

        execute(setup_name, name=name, hosts=[host_strong])


create_key = CreateKeyPair()
add_server = New()
