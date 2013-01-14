from fabric.api import sudo, run, env
from fabric.tasks import Task

class CeleryInstall(Task):
    """
    Install Celery and set it up with svcadm.
    """
    name = 'setup_celery'

    def _setup_service(self, env_value=None):
        if env_value:
            run('svccfg -s celeryd setenv %s %s' % (env.project_env_var,
                                               env_value))

    def run(self, env_value=None):
        sudo('mkdir -p /var/log/celery')
        sudo('chown -R www:www /var/log/celery')
        run('svccfg import /srv/active/deploy/celery/celeryd.xml')
        self._setup_service(env_value)
        
        # start celeryd
        sudo('svcadm enable celeryd')

setup = CeleryInstall()