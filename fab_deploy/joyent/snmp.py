import os

from fab_deploy import functions
from fab_deploy.config import CustomConfig
from fab_deploy.base import snmp as base_snmp

from fabric.api import run, sudo, env, put, execute, local
from fabric.tasks import Task

class SNMPSingleSync(base_snmp.SNMPSingleSync):
    """
    Sync a snmp config file

    Takes one required argument:

    * **filename**: the full path to the file to sync.
    """

    remote_config_path = '/opt/local/etc/snmpd.conf'
    name = 'sync_single'

    def _add_package(self):
        sudo("mkdir -p /var/net-snmp/mib_indexes")
        sudo("pkg_add net-snmp")
        run('svcadm enable snmp')

    def _restart_service(self):
        run('svcadm restart snmp')


update_files = base_snmp.SNMPUpdate()
sync_single = SNMPSingleSync()
