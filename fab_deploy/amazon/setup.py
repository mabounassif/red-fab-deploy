import sys
from fabric.api import run, sudo, execute, env
from fabric.tasks import Task

from fab_deploy import functions

from api import get_ec2_connection
import utils


class BaseSetup(Task):
    """
    Base server setup.

    Sets up ssh so root cannot login and other logins must
    be key based.
    """

    # Because setup tasks modify the config file
    # they should always be run serially.
    serial = True

    def _update_config(self, config_section):
        if not env.host_string:
            print "env.host_string is None, please specify a host by -H "
            sys.exit(1)
        added = False
        cons = env.config_object.get_list(config_section,
                                          env.config_object.CONNECTIONS)
        if not env.host_string in cons:
            added = True
            cons.append(env.host_string)
            env.config_object.set_list(config_section,
                                       env.config_object.CONNECTIONS, cons)

            ips = env.config_object.get_list(config_section,
                                             env.config_object.INTERNAL_IPS)
            internal_ip = run(utils.get_ip_command('eth0'))
            ips.append(internal_ip)

            env.config_object.set_list(config_section,
                                       env.config_object.INTERNAL_IPS, ips)
        return added

    def _save_config(self):
        env.config_object.save(env.conf_filename)

    def _secure_ssh(self):
        # Change disable root and password
        # logins in /etc/ssh/sshd_config
        sudo('sed -ie "s/^PermitRootLogin.*/PermitRootLogin no/g" /etc/ssh/sshd_config')
        sudo('sed -ie "s/^PasswordAuthentication.*/PasswordAuthentication no/g" /etc/ssh/sshd_config')
        sudo('service ssh restart')

    def _update_apt(self):
        #update apt repository so installation of packages can be smooth
        sudo('apt-get update')


class AppSetup(BaseSetup):
    """
    Setup an app-server

    After base setup installs nginx setups a git repo. Then
    calls the deploy task.

    Also installs gunicorn, python, and other base packages.
    Runs the scripts/setup.sh script.

    Once finished it add the new instance into load balancer

    This is a serial task as it modifies local config files.
    """

    name = 'app_server'

    config_section = 'app-server'

    nginx_conf = 'nginx/nginx.conf'

    git_branch = 'master'
    git_hook = None

    def _add_remote(self, name=None):
        if not env.host_string in env.git_reverse:
            name = functions.get_remote_name(env.host_string,
                                             self.config_section, name=name)
            execute('local.git.add_remote', remote_name=name,
                                    user_and_host=env.host_string)
        return name

    def _transfer_files(self):
        execute('git.setup', branch=self.git_branch, hook=self.git_hook)
        execute('local.git.push', branch=self.git_branch)

    def _modify_others(self):
        execute('setup.lb_server', section=self.config_section)

    def _install_packages(self):
        sudo('apt-get -y install python-psycopg2')
        sudo('apt-get -y install python-setuptools')
        sudo('apt-get -y install python-imaging')
        sudo('apt-get -y install python-pip')
        self._install_venv()

    def _install_venv(self):
        sudo('pip install virtualenv')
        run('sh %s/scripts/setup.sh production' % env.git_working_dir)

    def _setup_services(self):
        execute('nginx.setup', nginx_conf=self.nginx_conf)
        sudo('service nginx restart')
        execute('gunicorn.setup')
        sudo('supervisorctl start gunicorn')

    def run(self, name=None):
        self._update_apt()
        self._update_config(self.config_section)

        self._add_remote(name=name)

        # Transfer files first so all configs are in place.
        self._transfer_files()

        self._secure_ssh()
        self._install_packages()
        self._setup_services()
        self._save_config()

        execute('deploy', branch=self.git_branch)

        self._modify_others()


class DBSetup(BaseSetup):
    """
    Setup a database server
    """
    name = 'db_server'
    config_section = 'db-server'

    def run(self, name=None):
        self._update_apt()
        self._update_config(self.config_section)
        self._secure_ssh()
        execute('postgres.master_setup', save_config=False,
                section=self.config_section)
        self._save_config()


class SlaveSetup(DBSetup):
    """
    Set up a slave database server with streaming replication
    """
    name = 'slave_db'
    config_section = 'slave-db'

    def _get_master(self):
        cons = env.config_object.get_list('db-server',
                                          env.config_object.CONNECTIONS)
        n = len(cons)
        if n == 0:
            print ('I could not find db server in server.ini.'
                   'Did you set up a master server?')
            sys.exit(1)
        else:
            for i in range(1, n + 1):
                print "[%2d ]: %s" % (i, cons[i - 1])
            while True:
                choice = raw_input('I found %d servers in server.ini. Which '
                                   'one do you want to use as master? ' % n)
                try:
                    choice = int(choice)
                    master = cons[choice - 1]
                    break
                except:
                    print "please input a number between 1 and %d" % n - 1

        return master

    def run(self, name=None):
        """
        """
        master = self._get_master()
        self._update_apt()
        if not env.config_object.has_section(self.config_section):
            env.config_object.add_section(self.config_section)
        self._update_config(self.config_section)
        self._secure_ssh()
        execute('postgres.slave_setup', master=master,
                section=self.config_section)
        self._save_config()


class DevSetup(AppSetup):
    """
    Setup a development server
    """
    name = 'dev_server'
    config_section = 'dev-server'

    def _modify_others(self):
        pass

    def _install_venv(self):
        sudo('pip install virtualenv')
        run('sh %s/scripts/setup.sh production development'
            % env.git_working_dir)

    def _setup_services(self):
        super(DevSetup, self)._setup_services()
        execute('postgres.master_setup', section=self.config_section)


class LBSetup(Task):
    """
    Set up load balancer

    Create an elastic load balancer, read connections info from server.ini,
    get ip address and look for corresponding ec2 instances, and register
    the instances with load balancer.

    you may define the following optional arguments in env:
    * **lb_name**:  name of load_balancer. If not defined, load balancer will
                    be named after the name of your project directory.
    * **listeners**:  listeners of load balancer, a list of tuple
                      (lb port, instance port, protocol).
                      If not provided, only port 80 will be registered.
    * **hc_policy**:  a dictionary defining the health check policy, keys can be
                      interval, target, healthy_threshold, timeout
                      and unhealthy_threshold

                      default value is
                          hc_policy = {
                            'interval': 30,
                            'target':   'HTTP:80/index.html', }
    """

    name = 'lb_server'
    config_section = 'load-balancer'

    hc_policy = {
                'interval': 30,
                'target':   'HTTP:80/index.html', }

    listeners =  [(80, 80, 'http',)]

    def get_instance_id_by_ip(self, ip, **kwargs):
        """
        get ec2 instance id based on ip address
        """
        instances = []
        conn = get_ec2_connection(server_type='ec2', **kwargs)
        reservations = conn.get_all_instances()
        for resv in reservations:
            for instance in resv.instances:
                if instance.ip_address == ip:
                    instances.append(instance.id)
        return instances

    def _get_elb(self, conn, lb_name):
        lbs = conn.get_all_load_balancers()
        for lb in lbs:
            if lb.name == lb_name:
                return lb
        return None

    def run(self, section, **kwargs):
        conn = get_ec2_connection(server_type='ec2', **kwargs)
        elb_conn = get_ec2_connection(server_type='elb', **kwargs)

        zones = [ z.name for z in conn.get_all_zones()]

        lb_name = env.get('lb_name')
        if not lb_name:
            lb_name = env.project_name

        listeners = env.get('listeners')
        if not listeners:
            listeners = self.listeners

        connections = env.config_object.get_list(section,
                                                 env.config_object.CONNECTIONS)
        ips = [ ip.split('@')[-1] for ip in connections]
        for ip in ips:
            instances = self.get_instance_id_by_ip(ip, **kwargs)
            if len(instances) == 0:
                print "Cannot find any ec2 instances match your connections"
                sys.exit(1)

        elb = self._get_elb(elb_conn, lb_name)
        print "find load balancer %s" %lb_name
        if not elb:
            elb = elb_conn.create_load_balancer(lb_name, zones, listeners,
                                                security_groups=['lb_sg'])
            print "load balancer %s successfully created" %lb_name

        elb.register_instances(instances)
        print "register instances into load balancer"
        print instances

        hc_policy = env.get('hc_policy')
        if not hc_policy:
            hc_policy = self.hc_policy
        print "Configure load balancer health check policy"
        print hc
        hc = HealthCheck(**hc_policy)
        elb.configure_health_check(hc)


app_server = AppSetup()
dev_server = DevSetup()
db_server = DBSetup()
slave_db = SlaveSetup()
lb_server = LBSetup()
