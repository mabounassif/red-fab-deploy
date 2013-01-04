import os

from fab_deploy import functions
from fab_deploy.config import CustomConfig

from fabric.api import run, sudo, env, put, execute, local
from fabric.tasks import Task

class BaseUpdateFiles(Task):
    name = 'update_files'
    serial = True
    directory = None
    filename = None

    def _get_project_config_filepath(self, section):
        return os.path.join(self.directory, "%s.conf" % section)

    def get_section_path(self, section):

        file_path = functions.get_config_filepath(
                        self._get_project_config_filepath(section),
                        os.path.join(self.directory, self.filename)
        )

        if not os.path.exists(file_path):
            path = os.path.dirname(file_path)
            local('mkdir -p %s' % path)

            org = os.path.join(env.configs_dir, self.filename)
            local('cp %s %s' % (org, file_path))

        return file_path

    def _save_to_file(self, section, lines):
        file_path = self.get_section_path(section)

        new_path = file_path + '.bak'
        cmd = "awk '{\
                tmp = match($0, \"%s\"); \
                if (tmp) { \
                    print \"%s\"; \
                    while(getline>0){tmp2 = match($0, \"%s\"); if (tmp2) break;} \
                    next;} \
                {print $0}}' %s > %s" %(lines[0], '\\n'.join(lines), lines[-1],
                                        file_path, new_path)
        local(cmd)
        local('mv %s %s' %(new_path, file_path))
        return file_path
