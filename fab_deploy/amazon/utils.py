import sys

import boto

from fabric.api import task, run, env

@task
def get_ip(interface, hosts=[]):
    """
    get IP address
    """
    return run(get_ip_command(interface))


def get_ip_command(interface):
    """
    get IP address
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

    Two security groups will be created.  app-sg and db-sg.

    app-sg will enable access to ports 80 and 22 from everywhere.
    instances belong to this group can access each other freely, because there
    may be other services (for example, cache) require some ports open.

    db-sg has only port 5432 and 6432 open to instances in app-sg and db-sg.

    please use internal ips in your django settings files when specifying
    database settings.
    """

    try:
        app_groups = conn.get_all_security_groups(groupnames=['app-sg'])
        app_grp = app_groups[0]
        print "got security group app-sg"
    except:
        app_grp = conn.create_security_group('app-sg',
                                             'security group for app-server')
        print "creating security group app-sg"
        app_grp.authorize('tcp', 80, 80, '0.0.0.0/0')
        app_grp.authorize('tcp', 22, 22, '0.0.0.0/0')
        app_grp.authorize('tcp', 0, 65535, src_group=app_grp)

    try:
        db_groups = conn.get_all_security_groups(groupnames=['db-sg'])
        db_grp = db_groups[0]
        print "got security group db-sg"
    except:
        db_grp = conn.create_security_group('db-sg',
                                            'security group for db-server')
        print "creating security group db-sg"
        db_grp.authorize('tcp', 22, 22, '0.0.0.0/0')
        #allow access from app and db servers on port 5432 and 6432
        db_grp.authorize('tcp', 5432, 5432, src_group=app_grp)
        db_grp.authorize('tcp', 6432, 6432, src_group=app_grp)
        db_grp.authorize('tcp', 5432, 5432, src_group=db_grp)
        db_grp.authorize('tcp', 6432, 6432, src_group=db_grp)

    if type == 'app_server' or type == 'lb_server':
        return app_grp
    elif type == 'db_server' or type == 'slave_db':
        return db_grp
