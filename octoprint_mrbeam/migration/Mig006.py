from datetime import date

import yaml
from aspy.yaml import OrderedLoader

from octoprint_mrbeam import mrb_logger
from octoprint_mrbeam.migration.migration_base import (
    MigrationBaseClass,
    MIGRATION_RESTART,
)


class Mig006FixUsageData(MigrationBaseClass):
    """
    This migration fix the usage data that was lost during v0.15.0 and 0.15.0post0 updates
    """

    COMMAND_TO_GET_LOGS = 'grep -r "octoprint.plugins.mrbeam.analytics.usage - ERROR - No job time found in {}" /home/pi/.octoprint/logs/'
    COMMAND_TO_CHECK_IF_VERSION_WAS_PRESENT = 'grep -a -e "Mr Beam Laser Cutter (0.15.0.post0) = /home/pi/oprint/local/lib/python2.7/site-packages/octoprint_mrbeam" -e "Mr Beam Laser Cutter (0.15.0) = /home/pi/oprint/local/lib/python2.7/site-packages/octoprint_mrbeam" /home/pi/.octoprint/logs/*'
    USAGE_DATA_FILE_PATH = "/home/pi/.octoprint/analytics/usage.yaml"
    USAGE_DATA_FILE_PATH_BACKUP = "/home/pi/.octoprint/analytics/usage_bak.yaml"

    def __init__(self, plugin):
        self._backup_usage_data = None
        super(Mig006FixUsageData, self).__init__(
            plugin, restart=MIGRATION_RESTART.OCTOPRINT
        )

    @property
    def id(self):
        return "006"

    @staticmethod
    def shouldrun(cls, beamos_version):
        """Checks if this Miration should run.

        overrides the current behaviour as this migration should run if the log file contains the "octoprint.plugins.mrbeam.analytics.usage - ERROR - No job time found in {}, returning 0" error
        """
        with open(cls.USAGE_DATA_FILE_PATH, "r") as yaml_file:
            yaml_data = yaml.load(yaml_file, Loader=OrderedLoader)
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
                + date.today().strftime("%Y_%m_%d_%H_%M_%S"),
            )
        )
        super(Mig006FixUsageData, self)._run()

    def _rollback(self):
        super(Mig006FixUsageData, self)._rollback()
