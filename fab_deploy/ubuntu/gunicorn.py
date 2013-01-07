import os

from fab_deploy.base import gunicorn as base_gunicorn

from fabric.api import run, sudo, env
from fabric.contrib.files import append
from fabric.tasks import Task

class GunicornControl(base_gunicorn.Control):

    def start(self):
        sudo('supervisorctl start %s' % self.get_name())

    def stop(self):
        sudo('supervisorctl stop %s' % self.get_name())

    def restart(self):
        sudo('supervisorctl restart %s' % self.get_name())

class GunicornInstall(base_gunicorn.GunicornInstall):
    """
    Install gunicorn and set it up with svcadm.
    """

    user = 'www-data'
    group = 'www-data'

    def _setup_service(self, env_value=None):
        # we use supervisor to control gunicorn
        sudo('apt-get -y install supervisor')

        conf_file = '/etc/supervisor/supervisord.conf'

        gunicorn_conf = os.path.join(env.git_working_dir, 'deploy',
                                     self.gunicorn_name,
                                     'supervisor_%s.conf' % self.gunicorn_name )

        text = 'files = %s' % gunicorn_conf

        append(conf_file, text, use_sudo=True)
        sudo('supervisorctl update')

    def _setup_rotate(self, path):
        text = [
        "%s {" % path,
        "    copytruncate",
        "    size 1M",
        "    rotate 5",
        "}"]
        sudo('touch /etc/logrotate.d/%s.conf' % self.gunicorn_name)
        for t in text:
            append('/etc/logrotate.d/%s.conf' % self.gunicorn_name,
                                        t, use_sudo=True)
