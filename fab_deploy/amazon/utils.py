import sys

import boto

from fabric.api import task, env, run

@task
def get_ip(interface, hosts=[]):
    """
    """
    return run(get_ip_command(interface))

def get_ip_command(interface):
    """
    """
    if not interface:
        interface = 'eth0'
    return 'ifconfig %s | grep Bcast | cut -d ":" -f 2 | cut -d " " -f 1' % interface


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
        print "[ %d ]:\t%s\t%s\t%s" % (i + 1, type[0], type[1], type[2])
    sys.stdout.write("These types of instance are available, "
                     "which one do you want to create?: ")

    while True:
        try:
            num = int(raw_input())
        except:
            print "Please input a valid number from 0 to %d: " % n
        return INSTANCE_TYPES[num - 1][0]


def get_security_group(conn, type):
    """
    create security group if it does not exist
    """
    if type == 'app_server' or type == 'lb_server':
        try:
            groups = conn.get_all_security_groups(groupnames=['app-sg'])
            return groups[0]
        except:
            print "You must create security group first."
            sys.exit()

    elif type == 'db_server' or type == 'slave_db':
        try:
            groups = conn.get_all_security_groups(groupnames=['db-sg'])
            groups[0]
        except:
            print "You must create security group first."
            sys.exit()
