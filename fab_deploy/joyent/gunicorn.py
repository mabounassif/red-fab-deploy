import os

from fab_deploy.base import gunicorn as base_gunicorn

from fabric.api import run, sudo, env
from fabric.tasks import Task

class GunicornControl(base_gunicorn.Control):

    def start(self):
        run('svcadm enable %s' % self.get_name())

    def stop(self):
        run('svcadm disable %s' % self.get_name())

    def restart(self):
        run('svcadm restart %s' % self.get_name())

class GunicornInstall(base_gunicorn.GunicornInstall):
    """
    Install gunicorn and set it up with svcadm.
    """

    def _setup_service(self, env_value=None):
        path = os.path.join(env.git_working_dir, 'deploy',
                            'gunicorn',
                            '%s.xml' % self.gunicorn_name)

        run('svccfg import %s' % path)
        if env_value:
            run('svccfg -s %s setenv %s %s' % (self.gunicorn_name,
                                               env.project_env_var,
                                               env_value))

    def _setup_rotate(self, path):
        sudo('logadm -C 3 -p1d -c -w %s -z 1' % path)


setup = GunicornInstall()
control = GunicornControl()
