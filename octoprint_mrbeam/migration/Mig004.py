import os

from octoprint_mrbeam.migration.migration_base import (
    MigrationBaseClass,
)


class Mig004DisableDebugLogging(MigrationBaseClass):
    """This migration should add logrotate for the buster image and change the
    lorotate for the legacy image."""

    # MIGRATE_LOGROTATE_FOLDER = "files/migrate_logrotate/"
    BEAMOS_VERSION_LOW = "0.14.0"
    BEAMOS_VERSION_HIGH = "0.14.0"

    def __init__(self, plugin):
        super(Mig004DisableDebugLogging, self).__init__(plugin)

    @property
    def id(self):
        return "004"

    def _run(self):
        self._logger.debug("delete logging config file")
        self.exec_cmd("sudo rm /home/pi/.octoprint/logging.yaml", optional=True)

        super(Mig004DisableDebugLogging, self)._run()

    def _rollback(self):
        # no rollback needed
        super(Mig004DisableDebugLogging, self)._rollback()
