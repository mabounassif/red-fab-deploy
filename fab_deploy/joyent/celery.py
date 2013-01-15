from fabric.api import sudo, run, env
from fab_deploy.base import celery as base_celery


class CeleryControl(base_celery.Control):

    def start(self):
        run('svcadm enable %s' % self.name)

    def stop(self):
        run('svcadm disable %s' % self.name)

    def restart(self):
        run('svcadm restart %s' % self.name)


class CeleryInstall(base_celery.CeleryInstall):
    """
    Install Celery and set it up with svcadm.
    """
    name = 'setup_celery'

    def _setup_service(self, env_value=None):
        run('svccfg import /srv/active/deploy/celery/celeryd.xml')
        if env_value:
            run('svccfg -s celeryd setenv %s %s' % (env.project_env_var,
                                               env_value))

    def _start_service(self):
        # start celeryd
        sudo('svcadm enable celeryd')

setup = CeleryInstall()
control = CeleryControl()