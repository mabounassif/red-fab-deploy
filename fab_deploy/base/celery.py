from fabric.api import sudo, env
from fabric.tasks import Task
from fab_deploy.base import setup
from fab_deploy import functions


class Control(setup.Control):

    def get_name(self):
        task = functions.get_task_instance('celery.setup')
        return task.celery_name


class CeleryInstall(Task):
    name = 'setup'
    user = 'www'
    group = 'www'

    celery_name = 'celeryd'

    def _setup_service(self, env_value=None):
        raise NotImplementedError()

    def _start_service(self):
        raise NotImplementedError()

    def run(self, env_value=None):
        self._setup_service(env_value)
        self._start_service()