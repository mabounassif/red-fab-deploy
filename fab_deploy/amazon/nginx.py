import os

from fabric.api import sudo, env, local
from fabric.tasks import Task

DEFAULT_NGINX_CONF = "nginx/nginx.conf"


class NginxInstall(Task):
    """
    Install nginx

    Takes one optional argument:

    * **nginx_conf**: the relative path of the nginx config file
                    (that is part of your repo) that you want use
                    as your nginx config. If not provided it will
                    default to nginx/nginx.conf

    Also sets up log rotation
    """

    name = 'setup'

    def run(self, nginx_conf=None, hosts=[]):
        """
        """
        if not nginx_conf:
            nginx_conf = DEFAULT_NGINX_CONF

        self._install_package()
        # self._setup_logging()
        self._setup_dirs()
        self._setup_config(nginx_conf=nginx_conf)

    def _install_package(self):
        sudo("apt-get -y install nginx")

    def _setup_dirs(self):
        sudo('mkdir -p /var/www/cache-tmp')
        sudo('mkdir -p /var/www/cache')
        sudo('chown -R www-data:www-data /var/www')

    def _setup_config(self, nginx_conf=None):
        remote_conv = os.path.join(env.git_working_dir, 'deploy', nginx_conf)
        sudo('ln -sf %s /etc/nginx/nginx.conf' % remote_conv)


setup = NginxInstall()
