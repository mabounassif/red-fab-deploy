from fabric.api import execute, env
from fabric.tasks import Task

from fab_deploy import functions

class FirewallSync(Task):
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
    serial = True
    task_group = 'firewall'

    def run(self, section=None):
        """
        """
        update = '%s.update_files' % self.task_group
        single = '%s.sync_single' % self.task_group

        execute(update, section=section, hosts=[])
        if section:
            sections = [section]
        else:
            sections = env.config_object.server_sections()

        task = functions.get_task_instance(update)
        for s in sections:
            hosts = env.config_object.get_list(s,
                                env.config_object.CONNECTIONS)
            if hosts:
                filename = task.get_section_path(s)
                execute(single, filename=filename,
                    hosts=hosts)


class SNMPSync(FirewallSync):
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
