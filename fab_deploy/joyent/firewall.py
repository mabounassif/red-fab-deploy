import os

from fab_deploy import functions
from fab_deploy.config import CustomConfig

from fabric.api import run, sudo, env, put, execute, local
from fabric.tasks import Task


class FirewallSingleSync(Task):
    """
    Sync a ipf config file

    Takes one required argument:

    * **filename**: the full path to the file to sync.
    """

    name = 'sync_single'

    def run(self, filename=None):
        """
        """
        assert filename

        put(filename, '/var/tmp/tmpipf.conf')
        sudo("mv /var/tmp/tmpipf.conf /etc/ipf/ipf.conf")
        run('svccfg -s ipfilter:default setprop firewall_config_default/policy = astring: "custom"')
        run('svccfg -s ipfilter:default setprop firewall_config_default/custom_policy_file = astring: "/etc/ipf/ipf.conf"')
        run('svcadm refresh ipfilter:default')
        run('svcadm enable ipfilter')
        run('svcadm restart ipfilter')

class TCPOptions(object):
    internal_interface = 'net1'
    external_interface = 'net0'
    proto = 'tcp'
    group = '200'

    start_line = "## Start Configurable Section ##"
    end_line = "## End Configurable Section ##"

    open_ports = CustomConfig.OPEN_PORTS
    internal_restricted_ports = CustomConfig.RESTRICTED_PORTS
    external_restricted_ports = CustomConfig.EX_RESTRICTED_PORTS

    allowed = CustomConfig.ALLOWED_SECTIONS
    ex_allowed = CustomConfig.EX_ALLOWED_SECTIONS

    def get_line(self, port, interface=None, from_ip='any'):
        if not interface:
            interface = ''
        else:
            interface = ' on ' + interface

        config = {
            'interface' : interface,
            'proto' : self.proto,
            'from_ip' : from_ip,
            'port' : port,
            'group' : self.group
        }

        return "pass in quick%(interface)s proto %(proto)s from %(from_ip)s to any port = %(port)s keep state group %(group)s" % config

    def get_optional_list(self, section, conf, ports_option,
                          allowed_option, ip_option, interface):
        lines = []
        # If we have restricted ports
        restricted_ports = conf.get_list(section, ports_option)
        if restricted_ports:
            # Get all the internals
            ips = []
            for section in conf.get_list(section, allowed_option):
                ips.extend(conf.get_list(section, ip_option))

            # Add a line for each port
            for ip in ips:
                ip = ip.split('@')[-1]
                for port in restricted_ports:
                    line = self.get_line(port, interface, ip)
                    lines.append(line)
        return lines

    def get_config_list(self, section, conf):
        txt = [self.start_line]
        for port in conf.get_list(section, self.open_ports):
            txt.append(self.get_line(port))

        txt.extend(self.get_optional_list(section, conf,
                                self.internal_restricted_ports,
                                self.allowed,
                                conf.INTERNAL_IPS,
                                self.internal_interface))

        txt.extend(self.get_optional_list(section, conf,
                                self.external_restricted_ports,
                                self.ex_allowed,
                                conf.CONNECTIONS,
                                self.external_interface))
        txt.append(self.end_line)
        return txt


class UDPOptions(TCPOptions):
    proto = 'udp'
    group = '300'

    start_line = "## Start UDP Configurable Section ##"
    end_line = "## End UDP Configurable Section ##"

    open_ports = CustomConfig.UDP_OPEN_PORTS
    internal_restricted_ports = CustomConfig.UDP_RESTRICTED_PORTS
    external_restricted_ports = CustomConfig.UDP_EX_RESTRICTED_PORTS

    allowed = CustomConfig.UDP_ALLOWED_SECTIONS
    ex_allowed = CustomConfig.UDP_EX_ALLOWED_SECTIONS

class FirewallUpdate(Task):
    """
    Update ipf config file(s)

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
    directory = 'ipf'
    filename = 'ipf.conf'

    PROCESSORS = (UDPOptions(), TCPOptions())

    def _get_project_config_filepath(self, section):
        return os.path.join(self.directory, "%s.conf" % section)

    def get_section_path(self, section):

        file_path = functions.get_config_filepath(
                        self._get_project_config_filepath(section),
                        os.path.join(self.directory, self.filename)
        )

        if not os.path.exists(file_path):
            path = os.path.dirname(file_path)
            local('mkdir -p %s' % path)

            org = os.path.join(env.configs_dir, self.filename)
            local('cp %s %s' % (org, file_path))

        return file_path

    def _save_to_file(self, section, lines):
        file_path = self.get_section_path(section)

        new_path = file_path + '.bak'
        cmd = "awk '{\
                tmp = match($0, \"%s\"); \
                if (tmp) { \
                    print \"%s\"; \
                    while(getline>0){tmp2 = match($0, \"%s\"); if (tmp2) break;} \
                    next;} \
                {print $0}}' %s > %s" %(lines[0], '\\n'.join(lines), lines[-1],
                                        file_path, new_path)
        local(cmd)
        local('mv %s %s' %(new_path, file_path))
        return file_path

    def run(self, section=None):
        """
        """

        if section:
            sections = [section]
        else:
            sections = env.config_object.server_sections()

        for s in sections:
            for ins in self.PROCESSORS:
                lines = ins.get_config_list(s, env.config_object)
                self._save_to_file(s, lines)

update_files = FirewallUpdate()
sync_single = FirewallSingleSync()
