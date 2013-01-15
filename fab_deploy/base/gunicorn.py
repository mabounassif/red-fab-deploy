import os

from fabric.api import run, sudo, env
from fabric.tasks import Task

from fab_deploy.base import setup
from fab_deploy import functions

class Control(setup.Control):

    def get_name(self):
        task = functions.get_task_instance('gunicorn.setup')
        return task.gunicorn_name

class GunicornInstall(Task):
    """
    Install gunicorn and set it up with svcadm.
    """

    name = 'setup'
    user = 'www'
    group = 'www'

    log_dir = '/var/log/gunicorn'

    gunicorn_name = 'gunicorn'
    log_name = 'django.log'

    def _setup_service(self, env_value=None):
        raise NotImplementedError()

    def _setup_logs(self):
        path = os.path.join(self.log_dir, self.log_name)
        sudo('mkdir -p %s' % self.log_dir)
        sudo('touch %s' % path)
        sudo('chown -R %s:%s %s' % (self.user, self.group, self.log_dir))
        sudo('chmod 666 %s' % path)
        return path

    def _setup_rotate(self, path):
        raise NotImplementedError()

    def run(self, env_value=None):
        """
        """
        self._setup_service(env_value)
        path = self._setup_logs()
        self._setup_rotate(path)
