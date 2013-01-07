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

    name = 'sync_single'

    def _add_package(self):
        sudo("pkg_add net-snmp")
        run('svcadm enable sma')

    def _restart_service(self):
        run('svcadm restart sma')


update_files = base_snmp.SNMPUpdate()
sync_single = SNMPSingleSync()
