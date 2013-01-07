from fab_deploy.base import git as base_git

from fabric.api import run, sudo, env, put, execute

class Install(base_git.Install):
    def _install_package(self):
        sudo("apt-get -y install git")
