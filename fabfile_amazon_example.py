import os

from fabric.api import env

from fab_deploy import *

from fab_deploy.amazon import *

env.AWS_CREDENTIAL = '/path/to/a/file'
setup_env(os.path.abspath(os.path.dirname(__file__)))
