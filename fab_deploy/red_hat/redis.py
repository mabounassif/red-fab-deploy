import os

from fab_deploy.base.setup import Control

from fabric.api import sudo, env, local, run
from fabric.tasks import Task
from fabric.context_managers import cd, settings
from fabric.contrib.files import append

CHKHEADER = ["# REDHAT chkconfig header",
"# chkconfig: - 85 15",
"# description: redis",
"### BEGIN INIT INFO",
"# Provides: redis",
"# Required-Start: $network $local_fs $remote_fs",
"# Required-Stop: $network $local_fs $remote_fs",
"# Default-Start: 2 3 4 5",
"# Default-Stop: 0 1 6",
"# Should-Start: $syslog $named",
"# Should-Stop: $syslog $named",
"# Short-Description: start and stop redis",
"# Description: Redis daemon",
"### END INIT INFO"]

class Install(Task):
    """
    Install redis
    """
    version = '2.6.8'
    name = 'install'
    user = 'redis'
    data_dir = '/var/lib/redis'
    config = 'redis.conf'
    config_dir = '/etc/redis'
    log = '/var/log/redis.log'
    port = 6379

    def safe_disable(self, name):
        with settings(warn_only=True):
            sudo('service redis stop')
            sudo('chkconfig redis off')
            sudo('chkconfig --del redis')

    def _setup_config(self, conf):
        sudo('mkdir -p %(config_dir)s' % conf)
        sudo('cp %(source)s/redis.conf %(config)s' % conf)
        sudo("sed -i 's#^daemonize no#daemonize yes#g' %(config)s" % conf)
        sudo("sed -i 's#^logfile .*#logfile %(log)s#g' %(config)s" % conf)
        sudo("sed -i 's#^pidfile .*#pidfile %(pid)s#g' %(config)s" % conf)
        sudo("sed -i 's#^dir .*#dir %(home)s#g' %(config)s" % conf)
        sudo("sed -i 's#^port .*#port %(port)s#g' %(config)s" % conf)

    def _setup_logging(self, conf):
        text = [
        "%(config)s {" % conf,
        "    copytruncate",
        "    size 1M",
        "    rotate 5",
        "}"]
        sudo('touch /etc/logrotate.d/redis.conf')
        sudo('touch %(log)s' % conf)
        sudo('chown %(user)s:%(user)s %(log)s' % conf)
        append('/etc/logrotate.d/redis.conf', text, use_sudo=True)

    def run(self, hosts=[]):
        sudo('yum install -y gcc')
        sudo('yum install -y make')

        self.safe_disable('redis')
        idir = 'redis-%s' % self.version

        conf = {
            'user' : self.user,
            'home' : self.data_dir,
            'config' : os.path.join(self.config_dir, self.config),
            'config_dir' : self.config_dir,
            'port' : self.port,
            'pid' : '%s/redis.pid' % self.data_dir,
            'source' : idir,
            'log' : self.log
        }

        with settings(warn_only=True):
            result = sudo('id -u %(user)s' % conf)

        if result.failed:
            sudo('useradd -s /bin/false -M -r --home-dir %(home)s %(user)s' % conf)
            sudo('mkdir -p %(home)s' % conf)
            sudo('chown -R %(user)s:%(user)s %(home)s' % conf)

        run("wget http://redis.googlecode.com/files/redis-%s.tar.gz" % self.version)
        run("tar xzf redis-%s.tar.gz" % self.version)

        with cd(idir):
            # Run as user
            line = "sudo su %(user)s -s /bin/sh -c " % conf
            run(r"sed -i 's#\\$EXEC \\$CONF#" + line + r'\\"\\$EXEC \\$CONF\\"#g'+"' utils/redis_init_script" )
            run('sed -i "s/^REDISPORT=.*/REDISPORT=%(port)s/g" utils/redis_init_script' %conf)
            run('sed -i "s#^PIDFILE=.*#PIDFILE=%(pid)s#g" utils/redis_init_script' %conf)
            run('sed -i "s#^CONF=.*#CONF=%(config)s#g" utils/redis_init_script' %conf)
            append('chk', CHKHEADER)
            sudo('echo "#!/bin/sh" > /etc/init.d/redis')
            sudo('cat chk utils/redis_init_script >> /etc/init.d/redis')
            sudo('chmod +x /etc/init.d/redis')
            sudo('make && make install')

        self._setup_config(conf)
        self._setup_logging(conf)
        sudo('chkconfig --add redis')
        sudo('chkconfig --level 345 redis on')

class RedisControl(Control):
    def start(self):
        sudo('service redis start')

    def stop(self):
        sudo('service redis stop')

    def restart(self):
        sudo('service redis stop')
        sudo('service redis start')
