import os

from fab_deploy.ubuntu import gunicorn

class GunicornInstall(gunicorn.GunicornInstall):
	platform = 'amazon'


setup = GunicornInstall()
control = gunicorn.GunicornControl()
