from fabric.api import execute, env
from fabric.tasks import Task

from fab_deploy import functions
from fab_deploy.base.manage import FileBasedSync

class FirewallSync(FileBasedSync):
    """
    Updates the firewall on a live server.

    Calls ``firewall.update_files`` and then updates the
    remote servers using 'firewall.sync_single'

    Takes the same arguments as ``firewall.update_files``

    While this task will deploy any changes it makes they
    are not commited to your repo. You should review any
    changes and commit as appropriate.
    """

    name = 'firewall_sync'
    task_group = 'firewall'


class SNMPSync(FileBasedSync):
    """
    Updates the firewall on a live server.

    Calls ``snmp.update_files`` and then updates the
    remote servers using 'snmp.sync_single'

    Takes the same arguments as ``snmp.update_files``

    While this task will deploy any changes it makes they
    are not commited to your repo. You should review any
    changes and commit as appropriate.
    """
    name = 'snmp_sync'
    task_group = 'snmp'


firewall_sync = FirewallSync()
snmp_sync = SNMPSync()
