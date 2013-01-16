import os, time
from fabric.api import run, sudo, local, env, put
from fabric.tasks import Task
from fab_deploy.base.setup import Control


class SolrControl(Control):
    def start(self):
        run('svcadm enable tomcat')

    def stop(self):
        run('svcadm disable tomcat')

    def restart(self):
        run('svcadm restart tomcat')


class SolrInstall(Task):
    """
    Install solr and tomcat.
    """

    name = 'setup_solr'

    def run(self):
        self._getPackages()
        self._configSolr()
        self._configTomcat()
        run('svcadm enable tomcat')
        run('echo Tomcat by default runs on port 8080. To change, edit /opt/local/share/tomcat/conf/server.xml')


    def _getPackages(self):
        #download all packages necessary for solr and tomcat
        #sudo('wget http://apache.claz.org/lucene/solr/3.6.1/apache-solr-3.6.1.tgz')
        sudo('wget http://apache.tradebit.com/pub/lucene/solr/3.6.1/apache-solr-3.6.1.tgz') # Alternate download link
        
        sudo('pkg_add sun-jre6')
        sudo('pkg_add sun-jdk6')
        sudo('pkg_add apache-ant')
        sudo('pkg_add apache-ivy')
        sudo('pkg_add py27-cElementTree')
        sudo('pkg_add apache-tomcat')

    def _configSolr(self):
        #all ant build stuff and config setup
        run('tar xf apache-solr-3.6.1.tgz')
        sudo('mv apache-solr-3.6.1 /opt/')
        sudo('cp /opt/apache-solr-3.6.1/dist/apache-solr-3.6.1.war /opt/apache-solr-3.6.1/example/webapps/')
        sudo('mv /opt/apache-solr-3.6.1/example/webapps/solr.war /opt/apache-solr-3.6.1/example/webapps/example.war')
        sudo('cp /opt/apache-solr-3.6.1/example/webapps/apache-solr-3.6.1.war /opt/apache-solr-3.6.1/example/webapps/solr.war')
        sudo('cp -r /opt/apache-solr-3.6.1/example/ /opt/solr/')
        sudo('cp /opt/solr/webapps/solr.war /opt/solr/')


    def _configTomcat(self):
        #setup tomcat config files to point to solr setup

        sudo("sed -ie 's,solr.data.dir\:,solr.data.dir\:/opt/solr/solr/data,g' /opt/solr/solr/conf/solrconfig.xml")
        sudo('cp /opt/solr/solr.war /opt/local/share/tomcat/webapps/')
        sudo('bash /opt/local/share/tomcat/bin/startup.sh')
        time.sleep(5) # need to wait for files to get made by startup script.
        sudo("sed -ie 's,/put/your/solr/home/here,/opt/solr/solr,g' /opt/local/share/tomcat/webapps/solr/WEB-INF/web.xml")
        sudo("sed -ie '36d;42d' /opt/local/share/tomcat/webapps/solr/WEB-INF/web.xml")
        sudo('bash /opt/local/share/tomcat/bin/shutdown.sh')


class SyncSchema(Task):
    """
    Generate solr schema locally and sync with remote solr.
    """

    name = 'sync_schema'

    def run(self):
        run('svcadm disable tomcat')
        project_path = os.path.join(env.project_path, 'project')
        manage_path = os.path.join(project_path, 'manage.py')
        schema_path = os.path.join(project_path, 'schema.xml')

        local('python %s build_solr_schema > %s' % (manage_path, schema_path))
        put(local_path=schema_path, remote_path='/opt/solr/solr/conf/schema.xml', use_sudo=True)
        run('svcadm enable tomcat')



setup = SolrInstall()
control = SolrControl()
sync = SyncSchema()
