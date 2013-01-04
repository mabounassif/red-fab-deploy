from fab_deploy.base.git import Install, UpdateHook

from fabric.api import run, sudo, env, put, execute

class UbuntuInstall(Install):
    def _install_package(self):
        sudo("apt-get -y install git")
