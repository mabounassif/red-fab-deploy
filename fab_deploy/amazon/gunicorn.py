import os

from fab_deploy.ubuntu.gunicorn import UGunicornInstall, GunicornControl

setup = UGunicornInstall()
control = GunicornControl()
