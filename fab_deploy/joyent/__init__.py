import utils
import setup
import git
import gunicorn
import nginx
import postgres
import firewall
import manage
import api
import snmp
import celery
import redis
from fabric.api import env

env.platform = 'joyent'