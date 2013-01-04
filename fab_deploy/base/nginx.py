import os

from fabric.api import run, sudo, env, local
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
    remote_config_path = '/opt/local/etc/nginx/nginx.conf'
    user = 'www'
    group = 'www'

    def run(self, nginx_conf=None, hosts=[]):
        """
        """
        if not nginx_conf:
           nginx_conf = DEFAULT_NGINX_CONF

        self._install_package()
        self._setup_logging()
        self._setup_dirs()
        self._setup_config(nginx_conf=nginx_conf)

    def _install_package(self):
        raise NotImplementedError()

    def _setup_logging(self):
        raise NotImplementedError()

    def _setup_dirs(self):
        sudo('mkdir -p /var/www/cache-tmp')
        sudo('mkdir -p /var/www/cache')
        sudo('chown -R %s:%s /var/www' % (self.user, self.group))

    def _setup_config(self, nginx_conf=None):
        remote_conv = os.path.join(env.git_working_dir, 'deploy', nginx_conf)
        sudo('ln -sf %s %s' % (remote_conv, self.remote_config_path))
