from fab_deploy.base import git as base_git
from fabric.api import run, sudo, env

class Install(base_git.Install):
    def _install_package(self):
        sudo("pkg_add scmgit")

setup = Install()
update_hook = base_git.UpdateHook()
