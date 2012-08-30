
import os, sys
import time
import boto
from boto.ec2.connection import EC2Connection

from fabric.api import env, execute, local
from fabric.tasks import Task

from fab_deploy import functions

from utils import get_security_group, select_instance_type


DEFAULT_AMI     = 'ami-5965401c' # ubuntu 12.04 x86_64
DEFAULT_INSTANCE_TYPE = 'm1.medium'
DEFAULT_REGION  = 'us-west-1'


def get_ec2_connection():
    """
    create a connection to aws.
    aws_access_key and aws_secret_key should be defined in fabfile.
    """

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
    serial = True

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


class CreateSecurityGroup(Task):
    """
    Set up security policy
    """

    name = 'create_sg'
    serial = True

    def run(self, **kwargs):
        conn = get_ec2_connection()

        try:
            app_grps = conn.get_all_security_groups(groupnames = ['app-sg'])
            app_grp = app_grps[0]
        except:
            app_grp = conn.create_security_group('app-sg',
                                             'security group for app-server')
            app_grp.authorize('tcp', 80, 80, '0.0.0.0/0')
            app_grp.authorize('tcp', 22, 22, '0.0.0.0/0')
            app_grp.authorize('tcp', 0, 65535, src_group=app_grp)

        try:
            db_grps = conn.get_all_security_groups(groupnames = ['db-sg'])
            db_grp = db_grps[0]
        except:
            db_grp = conn.create_security_group('db-sg',
                                             'security group for db-server')
            db_grp.authorize('tcp', 22, 22, '0.0.0.0/0')
            db_grp.authorize('tcp', 5432, 5432, src_group=app_grp) #native pgsql
            db_grp.authorize('tcp', 6432, 6432, src_group=app_grp) #pgbouncer


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

        select = kwargs.get('select_instance_type')
        if select:
            instance_type = select_instance_type()

        key_name = env.config_object.get('amazon-aws',
                                         env.config_object.EC2_KEY)
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

        elastic_ip = conn.allocate_address()
        print "...Elastic IP %s allocated" % elastic_ip
        elastic_ip.associate(instance.id)

        print "...EC2 instance is successfully created."
        print "..."
        print "...Using image: %s" % image.name
        print "...Added into security group: %s" %security_group.name
        print "...id: %s" % instance.id
        print "...IP: %s" % elastic_ip

        local('ssh ubuntu@%s sudo apt-get update' % elastic_ip)

        # execute(setup_name, name=name, hosts=[host_strong])


create_key = CreateKeyPair()
create_sg = CreateSecurityGroup()
add_server = New()
