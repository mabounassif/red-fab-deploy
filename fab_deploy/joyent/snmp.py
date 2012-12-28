import os

from fab_deploy import functions
from fab_deploy.config import CustomConfig

from fabric.api import run, sudo, env, put, execute, local
from fabric.tasks import Task

from firewall import FirewallUpdate

class SNMPSingleSync(Task):
    """
    Sync a snmp config file

    Takes one required argument:

    * **filename**: the full path to the file to sync.
    """

    name = 'sync_single'

    def run(self, filename=None):
        """
        """
        assert filename

        put(filename, '/var/tmp/tmpsnmpd.conf')
        sudo("mv /var/tmp/tmpsnmpd.conf /etc/sma/snmp/snmpd.conf")
        sudo("pkg_add net-snmp")
        run('svcadm enable sma')
        run('svcadm restart sma')

class SNMPUpdate(FirewallUpdate):
    """
    Update snmp config file(s)

    Takes one argument:

    * **section**: The name of the section in your server.ini that you
                 would like to update. If section is not provided all
                 sections will be updated.

    Changes made by this task are not commited to your repo, or deployed
    anywhere automatically. You should review any changes and commit and
    deploy as appropriate.

    This is a serial task, that should not be called directly
    with any remote hosts as it performs no remote actions.
    """

    name = 'update_files'
    serial = True
    config_section = 'monitor'
    directory = 'snmp'
    filename = 'snmpd.conf'

    start_line = "## Start Configurable Section ##"
    end_line = "## End Configurable Section ##"

    def _get_lines(self, item):
        section = env.config_object.get(self.config_section, 'community')
        return [ "rocommunity %s %s" % (section, x) for x in \
                env.config_object.get_list(self.config_section,item) ]

    def run(self, section=None):
        """
        """

        if section:
            sections = [section]
        else:
            sections = env.config_object.server_sections()

        lines = [self.start_line]
        lines.extend(self._get_lines(env.config_object.CONNECTIONS))
        lines.extend(self._get_lines(env.config_object.INTERNAL_IPS))
        lines.append(self.end_line)

        for s in sections:
            self._save_to_file(s, lines)

update_files = SNMPUpdate()
sync_single = SNMPSingleSync()
