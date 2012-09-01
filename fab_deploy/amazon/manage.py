from fabric.api import  env
from fabric.tasks import Task

from utils import get_security_group
from api import get_ec2_connection


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

    """
    update security policy based on info from server.ini
    """

    def _get_lb_sg(self, **kwargs):
        elb_conn = get_ec2_connection(server_type='elb', **kwargs)
        elb = elb_conn.get_all_load_balancers()[0]
        return elb.source_security_group

    def run(self, section=None, **kwargs):
        conf = env.config_object
        conn = get_ec2_connection(server_type='ec2', **kwargs)

        if section:
            sections = [section]
        else:
            sections = conf.sections()

        for section in sections:

            open_ports = conf.get_list(section, conf.OPEN_PORTS)
            restricted_ports = conf.get_list(section, conf.RESTRICTED_PORTS)

            if (not open_ports and not restricted_ports
                or section == 'load-balancer'):
                continue

            host_sg = get_security_group(conn, section)
            if open_ports:
                for port in open_ports:
                    try:
                        host_sg.authorize('tcp', port, port, '0.0.0.0/0')
                    except:
                        pass

            if restricted_ports:
                for s in conf.get_list(section, conf.ALLOWED_SECTIONS):
                    if s == 'load-balancer':
                        guest_sg = self._get_lb_sg(**kwargs)
                    else:
                        guest_sg = get_security_group(conn, s)

                    for port in restricted_ports:
                        try:
                            if s == 'load-balancer':
                                conn.authorize_security_group(host_sg.name,
                                      src_security_group_name='amazon-elb-sg',
                                      src_security_group_owner_id='amazon-elb',
                                      from_port=port, to_port=port,
                                      ip_protocol='tcp')
                            else:
                                host_sg.authorize('tcp', port, port,
                                                  src_group=guest_sg)

                        except:
                            pass

firewall_sync = FirewallSync()
