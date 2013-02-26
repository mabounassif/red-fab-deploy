import os

from fab_deploy.base import gunicorn as base_gunicorn

from fabric.api import run, sudo, env
from fabric.contrib.files import append
from fabric.tasks import Task
from fabric.context_managers import settings, hide

class GunicornControl(base_gunicorn.Control):

    def start(self):
        with settings(warn_only=True):
            result = sudo('start %s' % self.get_name())

        if result.failed:
            self.restart()

    def stop(self):
        sudo('stop %s' % self.get_name())

    def restart(self):
        sudo('restart %s' % self.get_name())

class GunicornInstall(base_gunicorn.GunicornInstall):
    """
    Install gunicorn and set it up with svcadm.
    """

    user = 'nginx'
    group = 'nginx'

    def _setup_service(self, env_value=None):
        conf = os.path.join(env.git_working_dir, 'deploy',
                                     'gunicorn',
                                     '%s.conf' % self.gunicorn_name )
        # Copy instead of linking so upstart
        # picks up the changes
        sudo('cp %s /etc/init/' % conf)
        sudo('initctl reload-configuration')

    def _setup_rotate(self, path):
        text = [
        "%s {" % path,
        "    copytruncate",
        "    size 1M",
        "    rotate 5",
        "}"]
        sudo('touch /etc/logrotate.d/%s.conf' % self.gunicorn_name)
        append('/etc/logrotate.d/%s.conf' % self.gunicorn_name,
                                    text, use_sudo=True)
