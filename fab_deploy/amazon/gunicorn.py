import os

from fab_deploy.ubuntu.gunicorn import GunicornInstall, GunicornControl

setup = GunicornInstall()
control = GunicornControl()
