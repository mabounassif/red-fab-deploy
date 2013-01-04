from fabric.api import execute, env
from fabric.tasks import Task

from fab_deploy import functions

class FileBasedSync(Task):

    name = None
    serial = True
    task_group = None

    def run(self, section=None):
        update = '%s.update_files' % self.task_group
        single = '%s.sync_single' % self.task_group

        execute(update, section=section, hosts=[])
        if section:
            sections = [section]
        else:
            sections = env.config_object.server_sections()

        task = functions.get_task_instance(update)
        for s in sections:
            hosts = env.config_object.get_list(s,
                                env.config_object.CONNECTIONS)
            if hosts:
                filename = task.get_section_path(s)
                execute(single, filename=filename,
                    hosts=hosts)
