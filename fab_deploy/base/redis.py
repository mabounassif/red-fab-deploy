import os

from fabric.api import run, sudo, env, local, execute
from fabric.tasks import Task

class RedisInstall(Task):
    """
    Install redis
    """

    name = 'setup'

    config = (
        ('^bind', '#bind 127.0.0.1'),
    )
    config_location = None

    def run(self, master=None, port=6379, hosts=[]):
        self._install_package()
        config = list(self.config)
        if master:
            results = execute('utils.get_ip', None, hosts=[master])
            master_ip = results[master]
            config.append(('# slaveof', "slaveof "))
            config.append(('^slaveof', "slaveof {0} {1}".format(
                                                    master_ip, port)))

        self._setup_config(config)

    def _install_package(self):
        raise NotImplementedError()

    def _setup_config(self, config):
        for k, v in config:
            origin = "%s " % k
            sudo('sed -i "/%s/ c\%s" %s' %(origin, v, self.config_location))
