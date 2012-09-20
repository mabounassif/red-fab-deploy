import os

from fabric.api import sudo, env
from fabric.contrib.files import append
from fabric.tasks import Task


class GunicornInstall(Task):
    """
    Set up gunicorn, and set up supervisor to control it.
    """

    name = 'setup'

    def run(self):
        """
        """

        sudo('mkdir -p /var/log/gunicorn')
        sudo('chown -R www-data:www-data /var/log/gunicorn')

        # we use supervisor to control gunicorn
        sudo('apt-get -y install supervisor')

        conf_file = '/etc/supervisor/supervisord.conf'

        gunicorn_conf = os.path.join(env.git_working_dir, 'deploy',
                                     'gunicorn', 'supervisor_gunicorn.conf')
        text = 'files = %s' % gunicorn_conf

        append(conf_file, text, use_sudo=True)
        sudo('supervisorctl update')

setup = GunicornInstall()
