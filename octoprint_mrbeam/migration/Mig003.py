import os

from octoprint_mrbeam.migration.migration_base import (
    MigrationBaseClass,
)


class Mig003EnableLogrotateBuster(MigrationBaseClass):
    """
    This migration should add logrotate for the buster image and change the lorotate for the legacy image
    """

    MIGRATE_LOGROTATE_FOLDER = "files/migrate_logrotate/"
    BEAMOS_VERSION_LOW = "0.14.0"
    BEAMOS_VERSION_HIGH = "0.18.2"

    def __init__(self, plugin):
        super(Mig003EnableLogrotateBuster, self).__init__(plugin)

    @property
    def id(self):
        return "003"

    def _run(self):
        self._logger.debug("delete wrong iobeam logrotate")
        self.exec_cmd("sudo rm /etc/logrotate.d/iobeam.logrotate", optional=True)

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
                __package_path__, self.MIGRATE_LOGROTATE_FOLDER, logrotate
            )
            dst = os.path.join("/etc/logrotate.d/" + logrotate)
            self.exec_cmd("sudo cp {src} {dst}".format(src=src, dst=dst))

        self._logger.debug(
            "restarting logrotate in order for the changed config to take effect"
        )

        # needs to be optional for legacy image, as this is returning 1 instead of 0
        self.exec_cmd("sudo logrotate /etc/logrotate.conf", optional=True)
        super(Mig003EnableLogrotateBuster, self)._run()

    def _rollback(self):
        # no rollback needed
        super(Mig003EnableLogrotateBuster, self)._rollback()
