import os

from fabric.api import env

from fab_deploy import *

# if using joyent
from fab_deploy.joyent import *

# if using amazon aws, uncomment the following
# from fab_deploy.amazon import *

## You may choose to pass aws credentials from command line
# env.aws_access_key =  'xxx'
# env.aws_secret_key =  'xxx'
setup_env(os.path.abspath(os.path.dirname(__file__)))