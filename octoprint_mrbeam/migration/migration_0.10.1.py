from octoprint_mrbeam.migration.migration_base import (
    MigrationBaseClass,
)


class Migrate_0_10_1(MigrationBaseClass):
    def __init__(self, plugin):
        super(Migrate_0_10_1, self).__init__(plugin, version="0.10.1-hotfix")

    def _run(self):
        # TODO migrate netconnectd debug stuff
        self.exec_cmd("sudo truncate -s 0 /etc/default/netconnectd")
        # remove existing netconnectd file or purge content
        self.exec_cmd("sudo truncate -s 0 /var/log/netconnectd.log")
        # make sure what happens with <.log.x> files => these are not on the new image as logrotate is not enabled there
        super(Migrate_0_10_1, self)._run()

    def _rollback(self):
        super(Migrate_0_10_1, self)._rollback()
