import os

from fabric.api import sudo, env, local, run
from fabric.tasks import Task
from fabric.context_managers import cd, settings
from fabric.contrib.files import append, exists

class Install(Task):
    name = 'install'

    root = '/var/ftp'
    user = 'sapdata'

    config = '/etc/vsftpd'
    config_file = 'vsftpd.conf'
    password_file = 'ftpd.passwd'

    pam = '/etc/pam.d'

    settings= [
        "listen=YES",
        "anonymous_enable=NO",
        "local_enable=YES",
        "write_enable=YES",
        "local_umask=022",
        "nopriv_user=vsftpd",
        "virtual_use_local_privs=YES",
        "guest_enable=YES",
        "user_sub_token=$USER",
        "chroot_local_user=YES",
        "hide_ids=YES",
        "guest_username=vsftpd",
        "pam_service_name=vsftpd",
        "secure_chroot_dir=/usr/share/empty"
    ]

    def setup_pam(self):
        run('wget http://www.kernel.org/pub/linux/libs/pam/pre/library/Linux-PAM-0.80.tar.gz')
        run('tar -zxvf Linux-PAM-0.80.tar.gz')
        with cd('Linux-PAM-0.80/modules'):
            run('wget http://cpbotha.net/files/pam_pwdfile/pam_pwdfile-0.99.tar.gz')
            run('tar zxvf pam_pwdfile-0.99.tar.gz')
        with cd('Linux-PAM-0.80'):
            run('ln -sf defs/redhat.defs default.defs')
            run('./configure')
        with cd('Linux-PAM-0.80/modules/pam_pwdfile-0.99'):
            run('make all')
        sudo('cp Linux-PAM-0.80/modules/pam_pwdfile-0.99/pam_pwdfile.so /lib64/security')
        run('rm -r Linux-PAM-0.80*')

        password_path = os.path.join(self.config, self.password_file)
        pam_config = os.path.join(self.pam, 'vsftpd')
        sudo('echo "" > %s' % pam_config)
        text = [
            'auth required pam_pwdfile.so pwdfile %s' % password_path,
            'account required pam_permit.so'
        ]
        append(pam_config, text, use_sudo=True)

    def setup_configs(self, root):
        conf = list(self.settings)
        conf.append("local_root=%s" % os.path.join(root, "$USER"))
        conf_path = os.path.join(self.config, self.config_file)
        sudo('echo "" > %s' % conf_path)
        append(conf_path, conf, use_sudo=True)

    def install_package(self):
        sudo('yum -y install vsftpd')

    def create_user(self, root, user):
        with settings(warn_only=True):
            result = sudo('id -u vsftpd')

        if result.failed:
            sudo('useradd --home %s -m --shell /bin/false vsftpd' % root)

        path = os.path.join(root, user)
        sudo('mkdir -p %s' % path)
        sudo('chmod -w+x %s' %root)
        sudo('chown -R vsftpd:vsftpd %s' % root)

        pwpath = os.path.join(self.config, self.password_file)
        if not exists(pwpath, use_sudo=True):
            sudo('yum -y install httpd-tools')
            sudo('htpasswd -c -d %s %s' % (pwpath, user))
            sudo('yum -y erase httpd-tools')

    def run(self, root=None, user=None, **kwargs):
        if not root:
            root = self.root
        if not user:
            user = self.user

        self.install_package()
        self.setup_pam()
        self.setup_configs(root)
        self.create_user(root, user)

        sudo('service vsftpd restart')
