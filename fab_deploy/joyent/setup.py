from fabric.api import run

from fab_deploy.base.setup import *


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

class JLBSetup(JoyentMixin, LBSetup):
    pass

class JAppSetup(AppMixin, AppSetup):
    pass

class JDBSetup(JoyentMixin, DBSetup):
    pass

class JSlaveSetup(JoyentMixin, SlaveSetup):
    pass

class JDevSetup(AppMixin, DevSetup):
    pass

app_server = JAppSetup()
lb_server = JLBSetup()
dev_server = JDevSetup()
db_server = JDBSetup()
slave_db = JSlaveSetup()
