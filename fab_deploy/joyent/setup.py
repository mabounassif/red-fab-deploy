from fabric.api import run

from fab_deploy.base import setup as base_setup


class JoyentMixin(object):

    def _ssh_restart(self):
        run('svcadm restart ssh')

class AppMixin(JoyentMixin):
    packages = ['python27', 'py27-psycopg2', 'py27-setuptools',
                'py27-imaging']

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
