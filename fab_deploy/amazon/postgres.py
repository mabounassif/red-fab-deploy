from fab_deploy.ubuntu.postgres import UPostgresInstall, USlaveSetup, PGBouncerInstall

setup = UPostgresInstall()
slave_setup = USlaveSetup()
setup_pgbouncer = PGBouncerInstall()
