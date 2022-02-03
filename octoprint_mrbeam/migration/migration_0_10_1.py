import os

from octoprint_mrbeam.migration.migration_base import (
    MigrationBaseClass,
)


class Migrate_0_10_1(MigrationBaseClass):
    def __init__(self, plugin):
        super(Migrate_0_10_1, self).__init__(plugin, version="0.10.1-hotfix")

    def _run(self):
        self._logger.debug("stop netconnectd service")
        self.exec_cmd("sudo service netconnectd stop")

        self._logger.debug("disable debug mode of netconnect")
        self.exec_cmd("sudo truncate -s 0 /etc/default/netconnectd")

        self._logger.debug("purge content of netconnectd.log")
        self.exec_cmd("sudo truncate -s 0 /var/log/netconnectd.log")

        self._logger.debug("delete wrong iobeam logrotate")
        self.exec_cmd("sudo rm /etc/logrotate.d/iobeam.logrotate")

        logrotates = [
            "analytics",
            "iobeam",
            "mount_manager",
            "mrb_check",
            "mrbeam_ledstrips",
            "netconnectd",
        ]
        for logrotate in logrotates:
            self._logger.debug("enable logrotate of " + logrotate)
            src = os.path.join(
                __package_path__, self.MIGRATE_FILES_FOLDER, logrotate + ".logrotate"
            )
            dst = "/etc/logrotate.d/" + logrotate
            self.exec_cmd("sudo cp {src} {dst}".format(src=src, dst=dst))

        self._logger.debug("restart netconnectd service")
        self.exec_cmd("sudo service netconnectd restart")
        # make sure what happens with <.log.x> files => these are not on the new image as logrotate is not enabled there
        super(Migrate_0_10_1, self)._run()

    def _rollback(self):
        super(Migrate_0_10_1, self)._rollback()
