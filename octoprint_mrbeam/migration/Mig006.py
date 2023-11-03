import datetime

import yaml

from octoprint_mrbeam.migration.migration_base import (
    MigrationBaseClass,
)


class Mig006BackupUsageDataBeforeMigration(MigrationBaseClass):
    """
    This migration backups the usage data if it is the old airfilter structure.
    """

    USAGE_DATA_FILE_PATH = "/home/pi/.octoprint/analytics/usage.yaml"

    def __init__(self, plugin):
        self._backup_usage_data = None
        super(Mig006BackupUsageDataBeforeMigration, self).__init__(plugin)

    @property
    def id(self):
        return "006"

    @staticmethod
    def shouldrun(cls, beamos_version):
        """Checks if this Miration should run.

        overrides the current behaviour as this migration should run if the usage file includes the old airfilter structure
        """
        with open(cls.USAGE_DATA_FILE_PATH, "r") as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)
            if "prefilter" in yaml_data or "carbon_filter" in yaml_data:
                return True

        return False

    def _run(self):
        self._logger.debug("save usage data")
        self.exec_cmd(
            "sudo cp {file} {file_new}".format(
                file=self.USAGE_DATA_FILE_PATH,
                file_new=self.USAGE_DATA_FILE_PATH
                + "_"
                + datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S"),
            )
        )
        super(Mig006BackupUsageDataBeforeMigration, self)._run()

    def _rollback(self):
        super(Mig006BackupUsageDataBeforeMigration, self)._rollback()
