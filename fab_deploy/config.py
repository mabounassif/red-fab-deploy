import ConfigParser

class CustomConfig(ConfigParser.ConfigParser):
    """
    Custom Config class that can read and write lists.
    """

    # Config settings
    CONNECTIONS = 'connections'
    INTERNAL_IPS = 'internal-ips'
    OPEN_PORTS = 'open-ports'
    RESTRICTED_PORTS = 'restricted-ports'
    ALLOWED_SECTIONS = 'allowed-sections'
    USERNAME = 'username'
    REPLICATOR = 'replicator'
    REPLICATOR_PASS = 'replicator-password'
    GIT_SYNC = 'git-sync'

    EC2_KEY_NAME = 'ec2-key-name'
    EC2_KEY_FILE = 'ec2-key-file'

    def get_list(self, section, key):
        """
        """
        if not self.has_option(section, key):
            return []

        return [x.strip() for x in self.get(section, key).split(',') if x.strip() ]

    def set_list(self, section, key, slist):
        """
        """
        t = ','.join(slist)
        self.set(section, key, t)

    def save(self, filename):
        """
        """
        fp = open(filename, 'w')
        self.write(fp)
        fp.close()
