from fab_deploy.base.git import Install, UpdateHook
from fabric.api import run, sudo, env

class JoyentInstall(Install):
    def _install_package(self):
        sudo("pkg_add scmgit")

setup = JoyentInstall()
update_hook = UpdateHook()
