import sys
from fabric.api import run, sudo, execute, env
from fabric.tasks import Task

from fab_deploy import functions
from fab_deploy.base.setup import *

class UbuntuMixin(object):
    serial = True
    setup_firewall = False
    setup_snmp = False

    def _ssh_restart(self):
        sudo('apt-get update')
        sudo('service ssh restart')

class AppMixin(UbuntuMixin):
    packages = ['python-psycopg2', 'python-setuptools', 'python-imaging',
                'python-pip']

    def _install_packages(self):
        for package in self.packages:
            sudo('apt-get -y install  %s' % package)
        self._install_venv()

class UAppSetup(AppMixin, AppSetup):

    def _modify_others(self):
        pass

class UDBSetup(UbuntuMixin, DBSetup):
    pass

class USlaveSetup(UbuntuMixin, SlaveSetup):
    pass

class UDevSetup(AppMixin, DevSetup):
    pass
