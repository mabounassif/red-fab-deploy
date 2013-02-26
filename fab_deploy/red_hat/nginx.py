import os

from fab_deploy.base import nginx as base_nginx
from fab_deploy.base.setup import Control

from fabric.api import sudo, env, local
from fabric.tasks import Task


class NginxInstall(base_nginx.NginxInstall):
    """
    Install nginx

    Takes one optional argument:

    * **nginx_conf**: the relative path of the nginx config file
                    (that is part of your repo) that you want use
                    as your nginx config. If not provided it will
                    default to nginx/nginx.conf

    Also sets up log rotation
    """

    user = 'nginx'
    group = 'nginx'
    remote_config_path = '/etc/nginx/nginx.conf'

    def _install_package(self):
        sudo("rpm -U --replacepkgs http://nginx.org/packages/rhel/6/noarch/RPMS/nginx-release-rhel-6-0.el6.ngx.noarch.rpm")
        sudo("yum -y install nginx")

    def _setup_logging(self):
        # Done by package
        pass

class NginxControl(Control):
    def start(self):
        sudo('service nginx restart')

    def stop(self):
        sudo('service nginx stop')

    def restart(self):
        sudo('service nginx restart')
