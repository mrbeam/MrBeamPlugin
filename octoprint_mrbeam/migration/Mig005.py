import os

from octoprint_mrbeam.migration.migration_base import (
    MigrationBaseClass,
    MIGRATION_RESTART,
)


class Mig005InstallNTP(MigrationBaseClass):
    """
    This migration installs NTP on the system for the buster system
    """

    MIGRATE_LOGROTATE_FOLDER = "files/Mig005/"
    BEAMOS_VERSION_LOW = "0.18.0"
    BEAMOS_VERSION_HIGH = "0.20.1"

    def __init__(self, plugin):
        super(Mig005InstallNTP, self).__init__(
            plugin, restart=MIGRATION_RESTART.OCTOPRINT
        )

    @property
    def id(self):
        return "005"

    def _run(self):
        self._logger.debug("install ntp")
        path = os.path.join(__package_path__, self.MIGRATE_LOGROTATE_FOLDER)
        self.exec_cmd(
            "sudo apt install {folder}libopts25_1_5.18.12-4_armhf.deb -y".format(
                folder=path
            )
        )
        self.exec_cmd(
            "sudo apt install {folder}ntp_1_4.2.8p12+dfsg-4_armhf.deb -y".format(
                folder=path
            )
        )
        self.exec_cmd(
            "sudo apt install {folder}sntp_1_4.2.8p12+dfsg-4_armhf.deb -y".format(
                folder=path
            )
        )

        super(Mig005InstallNTP, self)._run()

    def _rollback(self):
        # no rollback needed
        super(Mig005InstallNTP, self)._rollback()
