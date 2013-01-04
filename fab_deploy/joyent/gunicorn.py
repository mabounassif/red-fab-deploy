import os

from fab_deploy.base.gunicorn import GunicornInstall, Control

from fabric.api import run, sudo, env
from fabric.tasks import Task

class GunicornControl(Control):

    def start(self):
        run('svcadm enable %s' % self.get_name())

    def stop(self):
        run('svcadm disable %s' % self.get_name())

    def restart(self):
        run('svcadm restart %s' % self.get_name())

class JGunicornInstall(GunicornInstall):
    """
    Install gunicorn and set it up with svcadm.
    """

    def _setup_service(self, env_value=None):
        path = os.path.join(env.git_working_dir, 'deploy',
                            self.gunicorn_name,
                            '%s.xml' % self.gunicorn_name)

        run('svccfg import %s' % path)
        if env_value:
            run('svccfg -s %s setenv %s %s' % (gunicorn_name,
                                               env.project_env_var,
                                               env_value))

    def _setup_rotate(self, path):
        sudo('logadm -C 3 -p1d -c -w %s -z 1' % path)


setup = JGunicornInstall()
control = GunicornControl()
