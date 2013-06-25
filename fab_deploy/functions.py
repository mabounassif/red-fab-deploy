import subprocess
import urlparse
import os
import random

from fabric.api import env, put
from fabric.task_utils import crawl

from jinja2 import Environment, FileSystemLoader

from StringIO import StringIO

def get_answer(prompt):
    """
    """
    result = None
    while result == None:
        r = raw_input(prompt + ' (y or n)')
        if r == 'y':
            result = True
        elif r == 'n':
            result = False
        else:
            print "Please enter y or n"
    return result

def _command(command, shell=False):
    proc = subprocess.Popen(command, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=shell)
    o, e = proc.communicate()
    if proc.returncode > 0:
        raise Exception(e)
    return o

def call_command(*commands):
    """
    """
    return _command(commands)

def call_shell_command(command):
    """
    """
    return _command(command, shell=True)

def gather_remotes():
    """
    """
    raw_remote = call_command('git', 'remote', '-v')
    remotes = {}
    for line in raw_remote.splitlines():
        parts = line.split()
        remotes[parts[0]] = urlparse.urlparse(parts[1]).netloc
    return remotes

def get_remote_name(host, prefix, name=None):
    """
    """
    assert prefix

    if not host in env.git_reverse:
        if name:
            return name

        count = len([x for x in env.git_remotes if x.startswith(prefix)])
        count = count + 1

        while True:
            if not name or name in env.git_remotes:
                count = count + 1
                name = prefix + str(count)
            else:
                env.git_reverse[host] = name
                env.git_remotes[name] = host
                break
    else:
        name = env.git_reverse[host]

    return name

def get_config_filepath(conf, default):
    """
    """
    if not conf:
       conf = default

    if not conf.startswith('/'):
        conf = os.path.join(env.deploy_path,conf)

    return conf

def get_task_instance(name):
    """
    """
    from fabric import state
    return crawl(name, state.commands)

def random_password(bit=12):
    """
    generate a password randomly which include
    numbers, letters and sepcial characters
    """
    numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    small_letters = [chr(i) for i in range(97, 123)]
    cap_letters = [chr(i) for i in range(65, 91)]
    special = ['@', '#', '$', '%', '^', '&', '*', '-']

    passwd = []
    for i in range(bit/4):
        passwd.append(random.choice(numbers))
        passwd.append(random.choice(small_letters))
        passwd.append(random.choice(cap_letters))
        passwd.append(random.choice(special))
    for i in range(bit%4):
        passwd.append(random.choice(numbers))
        passwd.append(random.choice(small_letters))
        passwd.append(random.choice(cap_letters))
        passwd.append(random.choice(special))

    passwd = passwd[:bit]
    random.shuffle(passwd)

    return ''.join(passwd)

def render_templates(filenames, app_name, platform, context=None):

    remote_path = os.path.join(env.git_working_dir, 'deploy',app_name)
    local_path = os.path.join(env.deploy_path, 'templates', app_name)

    redfab_defaults_base = os.path.join(env.configs_dir, 'templates', 'base', app_name)
    redfab_defaults_platform = os.path.join(env.configs_dir, 'templates', platform, app_name)
    search_paths = [local_path, redfab_defaults_platform, redfab_defaults_base]

    envi = Environment(loader=FileSystemLoader(search_paths))

    for filename in filenames:
        dest_path = os.path.join(remote_path, filename)
        template = (envi.get_template(filename)).render(**context or {})
        put(local_path=StringIO(template), remote_path = dest_path, use_sudo = True)



