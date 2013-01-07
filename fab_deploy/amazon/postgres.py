from fab_deploy.ubuntu.postgres import PostgresInstall, SlaveSetup, PGBouncerInstall

setup = PostgresInstall()
slave_setup = SlaveSetup()
setup_pgbouncer = PGBouncerInstall()
