import os

from fabric.api import env

from fab_deploy import *

from fab_deploy.amazon import *

env.aws_access_key =  'xxx'
env.aws_secret_key =  'xxx'
setup_env(os.path.abspath(os.path.dirname(__file__)))
