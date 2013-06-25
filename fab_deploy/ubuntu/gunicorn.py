import os

from fab_deploy.base import gunicorn as base_gunicorn

from fabric.api import run, sudo, env
from fabric.contrib.files import append
from fabric.tasks import Task
from fab_deploy import functions



class GunicornControl(base_gunicorn.Control):

    def start(self):
        sudo('supervisorctl start %s' % self.get_name())

    def stop(self):
        sudo('supervisorctl stop %s' % self.get_name())

    def restart(self):
        sudo('supervisorctl restart %s' % self.get_name())

class GunicornInstall(base_gunicorn.GunicornInstall):
    """
    Install gunicorn and set it up with svcadm.
    """

    user = 'www-data'
    group = 'www-data'

    default_context = {
    'gunicorn_supervisor_startscript':'GUNICORN_SUPERVISOR_STARTSCRIPT',
    'prj_directory':'PRJ_DIRECTORY',
    'gunicorn_startscript' : 'GUNICORN_STARTSCRIPT', 
    'gunicorn_env_exec' : 'GUNICORN_ENV_EXEC',
    'gunicorn_python' : 'GUNICORN_PYTHON',
    'settings_init' : 'SETTINGS_INIT',
    'listen_address' : 'LISTEN_ADDRESS', 
    'num_workers' : 'NUM_WORKERS',
    'gunicorn_log_file' : 'GUINCORN_LOG_FILE',
    }

    def _setup_service(self, env_value=None):

        # we use supervisor to control gunicorn
        sudo('apt-get -y install supervisor')
        conf_file = '/etc/supervisor/supervisord.conf'
        gunicorn_conf = os.path.join(env.git_working_dir, 'deploy',
                                     'gunicorn',
                                     'supervisor_%s.conf' % self.gunicorn_name )
        text = 'files = %s' % gunicorn_conf
        append(conf_file, text, use_sudo=True)
        sudo('supervisorctl update')

        context = dict(self.default_context)
        context.update(env.template_context.get("newrelic", {}))

        dir_path = os.path.join(env.remote_configs, self.gunicorn_name)
        if not os.path.exists(dir_path):
            sudo('mkdir %s' % dir_path)

        functions.render_template('%s/%s.py' % (self.gunicorn_name, self.gunicorn_name),
                                     env.remote_configs, context = context)
        functions.render_template('%s/start_%s.sh' % (self.gunicorn_name, self.gunicorn_name),
                                     env.remote_configs, context = context)
        functions.render_template('%s/supervisor_%s.conf' % (self.gunicorn_name, self.gunicorn_name),
                                     env.remote_configs, context = context)
        functions.render_template('%s/supervisor_start_%s.sh' % (self.gunicorn_name, self.gunicorn_name),
                                     env.remote_configs, context = context)

    def _setup_rotate(self, path):
        text = [
        "%s {" % path,
        "    copytruncate",
        "    size 1M",
        "    rotate 5",
        "}"]
        sudo('touch /etc/logrotate.d/%s.conf' % self.gunicorn_name)
        for t in text:
            append('/etc/logrotate.d/%s.conf' % self.gunicorn_name,
                                        t, use_sudo=True)
