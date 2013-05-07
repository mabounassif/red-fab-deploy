from fabric.api import run, sudo
from fabric.contrib.files import append

from fab_deploy.base import setup as base_setup


class JoyentMixin(object):

    def _set_profile(self):
        append('/etc/profile', 'CC="gcc -m64"; export CC', use_sudo=True)
        append('/etc/profile', 'LDSHARED="gcc -m64 -G"; export LDSHARED', use_sudo=True)

    def _ssh_restart(self):
        run('svcadm restart ssh')

class AppMixin(JoyentMixin):
    packages = ['python27', 'py27-psycopg2', 'py27-setuptools',
                'py27-imaging', 'py27-expat']

    def _install_packages(self):
        for package in self.packages:
            sudo('pkg_add %s' % package)
        sudo('easy_install-2.7 pip')
        self._install_venv()

class LBSetup(JoyentMixin, base_setup.LBSetup):
    pass

class AppSetup(AppMixin, base_setup.AppSetup):
    pass

class DBSetup(JoyentMixin, base_setup.DBSetup):
    pass

class SlaveSetup(JoyentMixin, base_setup.SlaveSetup):
    pass

class DevSetup(AppMixin, base_setup.DevSetup):
    pass

app_server = AppSetup()
lb_server = LBSetup()
dev_server = DevSetup()
db_server = DBSetup()
slave_db = SlaveSetup()
