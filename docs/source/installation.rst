.. toctree::

Installation
============

IMPORTANT: red-fab-deploy will only work if you install the following packages:

``$ pip install -e git+git://github.com/bitprophet/fabric.git#egg=fabric``

To use the joyent provider you will need smartdc

``$ pip install smartdc``

Deployment and Setup
====================

Fabfile

The first thing you need to do is set up your fabfile. This file should import * from fab_deploy. As well as specify which provider this setup is for. You do this by import * from that package. For example:

``from fab_deploy.joyent import *``

Server Configs

In your projects deploy folder there should be a file named servers.ini. This file keeps track of the different types of servers and any relationships between them. As you add servers using this tool the file will be updated. You also configure firewalls using this file by specifing which ports should be open to which other roles.

Fabric roles are also setup based on the information in this file. So adding -R app-server for example will run your specifed command on all servers in that section of the config file.

Your git remotes will also be scanned so that you can refer to remote servers by their git names. So if you have a git remote named web1 -H web1 will be a valid host.

Overriding behavior

In many cases you will want to customize the behavior of a certain task. For this reason most tasks are implemented as classes. You can inherit from the task that you want to customize, make your changes and then in your fabfile override that task name with your new class.

Tasks

To list the tasks run fab --list. Running fab -d task_name will print the full docstring for the given task.