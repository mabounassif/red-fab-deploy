import os

from fab_deploy.base.nginx import NginxInstall
from fab_deploy.base.setup import Control

from fabric.api import run, sudo, env, local
from fabric.tasks import Task


class NginxControl(Control):
    def start(self):
        run('svcadm enable nginx')

    def stop(self):
        run('svcadm disable nginx')

    def restart(self):
        run('svcadm restart nginx')


class JNginxInstall(NginxInstall):
    """
    Install nginx

    Takes one optional argument:

    * **nginx_conf**: the relative path of the nginx config file
                    (that is part of your repo) that you want use
                    as your nginx config. If not provided it will
                    default to nginx/nginx.conf

    Also sets up log rotation
    """

    def _install_package(self):
        sudo("pkg_add nginx")

    def _setup_logging(self):
        sudo('sed -ie "s/^#nginx\(.*\)/nginx\\1/g" /etc/logadm.conf')
        sudo('logadm')


class UpdateAppServers(Task):
    """
    Build app servers list in your load balancer nginx config.

    Finds your load banlancer nginx config by looking up
    the attribute on the task and rebuilds the list of
    app servers.

    Changes made by this task are not commited to your repo, or deployed
    anywhere automatically. You should review any changes and commit and
    deploy as appropriate.

    This is a serial task, that should not be called directly
    with any remote hosts as it performs no remote actions.
    """

    START_DELM = "## Start App Servers ##"
    END_DELM = "## End App Servers ##"
    LINE = "server   %s:8000 max_fails=5  fail_timeout=60s;"
    START = None
    END = None

    name = 'update_app_servers'
    serial = True

    def _update_file(self, nginx_conf, section):
        file_path = os.path.join(env.deploy_path, nginx_conf)
        text = [self.START_DELM]
        if self.START:
            text.append(self.START)

        for ip in env.config_object.get_list(section, env.config_object.INTERNAL_IPS):
            text.append(self.LINE % ip)

        if self.END:
            text.append(self.END)
        text.append(self.END_DELM)

        txt = "\\n".join(text)
        new_path = file_path + '.bak'
        cmd = "awk '{\
                tmp = match($0, \"%s\"); \
                if (tmp) { \
                    print \"%s\"; \
                    while(getline>0){tmp2 = match($0, \"%s\"); if (tmp2) break;} \
                    next;} \
                {print $0}}' %s > %s" %(self.START_DELM, txt, self.END_DELM,
                                        file_path, new_path)
        local(cmd)
        local('mv %s %s' %(new_path, file_path))

    def run(self, section=None, nginx_conf=None):
        assert section and nginx_conf
        self._update_file(nginx_conf, section)

class UpdateAllowedIPs(UpdateAppServers):
    """
    Build allowed servers list in your app server nginx config.

    Finds your app server nginx config by looking up
    the attribute on the task and rebuilds the list of
    app servers.

    Changes made by this task are not commited to your repo, or deployed
    anywhere automatically. You should review any changes and commit and
    deploy as appropriate.

    This is a serial task, that should not be called directly
    with any remote hosts as it performs no remote actions.
    """

    START_DELM = "## Start Allowed IPs ##"
    END_DELM = "## End Allowed IPs ##"
    LINE = "set_real_ip_from  %s;"
    END = "real_ip_header    X-Cluster-Client-Ip;"

    name = 'update_allowed_ips'

update_app_servers = UpdateAppServers()
update_allowed_ips = UpdateAllowedIPs()
setup = JNginxInstall()
control = NginxControl()
