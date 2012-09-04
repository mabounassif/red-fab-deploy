
import os, sys
import time
from ConfigParser import ConfigParser

import boto
from boto import ec2
from boto.ec2 import elb
from boto.ec2.connection import EC2Connection
from boto.ec2.elb import HealthCheck

from fabric.api import env, execute, local
from fabric.tasks import Task

from fab_deploy import functions

from utils import  get_security_group


DEFAULT_AMI     = 'ami-5965401c' # ubuntu 12.04 x86_64
DEFAULT_INSTANCE_TYPE = 'm1.medium'
DEFAULT_REGION  = 'us-west-1'


def get_ec2_connection(server_type, **kwargs):
    """
    create a connection to aws.

    aws_access_key and aws_secret_key should be defined in $AWS_CREDENTIAL file
    """

    amzn = env.get('AWS_CREDENTIAL',
                   os.path.join(env.deploy_path, 'amazon.ini'))
    if not os.path.exists(amzn):
        print ("Cannot find environment variable AMAZON_CREDENTIALS which should"
               " point to a file with your aws_access_key and aws_secret_key info"
               " inside. You may specify it through your fab env.")
        sys.exit()

    parser = ConfigParser()
    parser.read(amzn)

    aws_access_key = parser.get('amazon-aws', 'aws_access_key')
    aws_secret_key = parser.get('amazon-aws', 'aws_secret_key')

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

    This key will be stored under the same directory as env.AWS_CREDENTIAL and
    registered in env.AWS_CREDENTIAL file. You will need it to access all the
    instances created with it.

    """

    name = 'create_key'
    serial = True

    section = 'amazon-aws'

    def run(self, **kwargs):
        conn = get_ec2_connection(server_type='ec2', **kwargs)
        sys.stdout.write("Please give a name to the key: ")

        amzn = env.get('AWS_CREDENTIAL',
                       os.path.join(env.deploy_path, 'amazon.ini'))
        key_dir = os.path.dirname(amzn)
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

        parser = ConfigParser()
        parser.read(amzn)
        if not parser.has_section(self.section):
            parser.add_section(self.section)
        parser.set(self.section, 'ec2-key-name', key.name)
        parser.set(self.section, 'ec2-key-file', key_file)
        fp = open(amzn, 'w')
        parser.write(fp)
        fp.close()
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
        security_group = get_security_group(conn, task.config_section)

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


create_key = CreateKeyPair()
add_server = New()

