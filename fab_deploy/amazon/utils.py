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


def get_security_group(conn, type):
    """
    Get security group according to server type.
    If not exists, create one and return it
    """

    sg_name = '%s-sg' % type
    try:
        groups = conn.get_all_security_groups(groupnames=[sg_name])
        return groups[0]
    except:
        grp = conn.create_security_group(sg_name,
                                             'security group for app-server')
        grp.authorize('tcp', 22, 22, '0.0.0.0/0')
        return grp
