import git
import gunicorn
import nginx
import postgres
import setup
import api
import utils
import manage
from fabric.api import env

env.platform = 'amazon'