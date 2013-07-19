import os

from fab_deploy.base import redis as base_redis
from fab_deploy.base.setup import Control

from fabric.api import run, sudo, env
from fabric.tasks import Task

class RedisControl(Control):
    def start(self):
        run('svcadm enable redis')

    def stop(self):
        run('svcadm disable redis')

    def restart(self):
        run('svcadm restart redis')


class RedisInstall(base_redis.RedisInstall):
    """
    Install redis
    """
    config_location = '/opt/local/etc/redis.conf'

    def _install_package(self):
        sudo('pkg_add redis')

setup = RedisInstall()
control = RedisControl()
