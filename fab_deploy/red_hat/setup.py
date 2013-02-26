import sys
from fabric.api import run, sudo, execute, env
from fabric.tasks import Task
from fabric.context_managers import settings
from fabric.contrib.files import append

from fab_deploy import functions
from fab_deploy.base import setup as base_setup

class RHMixin(object):
    setup_firewall = False
    setup_snmp = False

    def _ssh_restart(self):
        sudo('apt-get update')
        sudo('service sshd restart')

class AppMixin(RHMixin):
    rpm_urls = [
        'http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm',
        'http://yum.postgresql.org/9.1/redhat/rhel-6-x86_64/pgdg-redhat91-9.1-5.noarch.rpm'
    ]

    packages = ['python-setuptools', 'python-pip',
                'python-devel', 'postgresql91-devel',
                'postgresql91-libs', 'python-psycopg2',
                'zlib', 'zlib-devel',
                'libjpeg', 'libjpeg-devel',
                'freetype', 'freetype-devel',
                'libpng', 'libpng-devel',
                'python-imaging'
    ]

    def _install_packages(self):
        for url in self.rpm_urls:
            sudo('rpm -Uvh --replacepkgs %s' % url)
        sudo('ln -sf /usr/bin/pip-python /usr/bin/pip')
        append('/etc/ld.so.conf.d/postgresql91.conf', '/usr/pgsql-9.1/lib', use_sudo=True)
        sudo('ldconfig')
        for package in self.packages:
            sudo('yum -y install  %s' % package)
        self._install_venv()

class AppSetup(AppMixin, base_setup.AppSetup):
    pass

class DBSetup(RHMixin, base_setup.DBSetup):
    pass

class SlaveSetup(RHMixin, base_setup.SlaveSetup):
    pass

class DevSetup(AppMixin, base_setup.DevSetup):
    pass
