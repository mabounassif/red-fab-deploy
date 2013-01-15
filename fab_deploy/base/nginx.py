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

    def run(self, nginx_conf=None, directory=None, hosts=[]):
        """
        """
        if not nginx_conf:
           nginx_conf = DEFAULT_NGINX_CONF

        self._install_package()
        self._setup_logging()
        self._setup_dirs()
        self._setup_config(nginx_conf=nginx_conf, directory=directory)

    def _install_package(self):
        raise NotImplementedError()

    def _setup_logging(self):
        raise NotImplementedError()

    def _setup_dirs(self):
        sudo('mkdir -p /var/www/cache-tmp')
        sudo('mkdir -p /var/www/cache')
        sudo('chown -R %s:%s /var/www' % (self.user, self.group))

    def _setup_config(self, nginx_conf=None, directory=None):
        remote_conv = os.path.join(env.git_working_dir, 'deploy', nginx_conf)
        if directory:
            name = nginx_conf.split('/')[-1]
            remote_config_path = os.path.join(directory, name)
        else:
            remote_config_path = self.remote_config_path
        sudo('ln -sf %s %s' % (remote_conv, remote_config_path))
