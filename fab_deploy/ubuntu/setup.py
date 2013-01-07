import sys
from fabric.api import run, sudo, execute, env
from fabric.tasks import Task

from fab_deploy import functions
from fab_deploy.base import setup as base_setup

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

class AppSetup(AppMixin, base_setup.AppSetup):

    def _modify_others(self):
        pass

class DBSetup(UbuntuMixin, base_setup.DBSetup):
    pass

class SlaveSetup(UbuntuMixin, base_setup.SlaveSetup):
    pass

class DevSetup(AppMixin, base_setup.DevSetup):
    pass
