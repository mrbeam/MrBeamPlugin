import os
import re

import yaml

from octoprint_mrbeam.util.cmd_exec import exec_cmd, exec_cmd_output

from octoprint_mrbeam import mrb_logger
from octoprint_mrbeam.migration.migration_base import (
    MigrationBaseClass,
    MIGRATION_RESTART,
)


class Mig006FixUsageData(MigrationBaseClass):
    """
    This migration fix the usage data that was lost during v0.15.0 update
    """

    COMMAND_TO_GET_LOGS = 'grep -r "octoprint.plugins.mrbeam.analytics.usage - ERROR - No job time found in {}" /home/pi/.octoprint/logs/'
    COMMAND_TO_CHECK_IF_VERSION_WAS_PRESENT = 'grep -a -e "Mr Beam Laser Cutter (0.15.0.post0) = /home/pi/oprint/local/lib/python2.7/site-packages/octoprint_mrbeam" -e "Mr Beam Laser Cutter (0.15.0) = /home/pi/oprint/local/lib/python2.7/site-packages/octoprint_mrbeam" /home/pi/.octoprint/logs/*'
    USAGE_DATA_FILE_PATH = "/home/pi/.octoprint/analytics/usage.yaml"

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
        command_output, code = exec_cmd_output(
            Mig006FixUsageData.COMMAND_TO_CHECK_IF_VERSION_WAS_PRESENT,
            log=True,
            shell=True,
        )

        if code == 0 and command_output != "":
            return True
        else:
            return False

    def _run(self):
        self._logger.debug("fix usage data")
        found_lines = exec_cmd_output(self.COMMAND_TO_GET_LOGS, log=True, shell=True)
        found_lines = str(found_lines).replace("\\'", "'").replace("\\n", "\n")

        regex = r"No job time found in {}, returning 0 - {.*'prefilter': {'[^}]*'job_time': (\d+\.\d+)[^}]*}*.+'total': {'[^}]*'job_time': (\d+\.\d+)[^}]*.*'carbon_filter': {'[^}]*'job_time': (\d+\.\d+)[^}]"

        match = re.search(regex, found_lines)
        self._logger.debug("match: {}".format(match))

        if match:
            bug_prefilter_job_time = float(match.group(1))
            bug_total_time = float(match.group(2))
            bug_carbon_filter_job_time = float(match.group(3))
            self._logger.info("total_time: {}".format(bug_total_time))
            self._logger.info(
                "Carbon Filter Job Time: {}".format(bug_carbon_filter_job_time)
            )
            self._logger.info("Prefilter Job Time: {}".format(bug_prefilter_job_time))

            with open(self.USAGE_DATA_FILE_PATH, "r") as yaml_file:
                yaml_data = yaml.load(yaml_file)
                self._backup_usage_data = yaml_data
            if (
                float(yaml_data["total"]["job_time"]) - 180000 < bug_total_time
            ):  # only migrate if the working time difference is less than 50 hours
                # Update the job_time in the airfilter prefilter
                time_since_error = (
                    float(yaml_data["total"]["job_time"]) - bug_total_time
                )
                self._logger.info(
                    "current usage file {} -{}".format(
                        yaml_data, yaml_data.get("airfilter")
                    )
                )
                if "airfilter" in yaml_data:
                    for airfilter_serial, airfilter_data in yaml_data.get(
                        "airfilter"
                    ).items():
                        if ("prefilter" or "carbon_filter") in airfilter_data:
                            yaml_data["airfilter"][airfilter_serial]["prefilter"][
                                "job_time"
                            ] = (bug_prefilter_job_time + time_since_error)
                            yaml_data["airfilter"][airfilter_serial]["carbon_filter"][
                                "job_time"
                            ] = (bug_carbon_filter_job_time + time_since_error)
                self._logger.info(
                    "Data was migrated successfully. {}".format(yaml_data)
                )
                # pop elements of old airfilter structure
                yaml_data.pop("prefilter")
                yaml_data.pop("carbon_filter")

                # Save the modified YAML back to the file
                with open(self.USAGE_DATA_FILE_PATH, "w") as yaml_file:
                    yaml.safe_dump(yaml_data, yaml_file, default_flow_style=False)
            else:
                self._logger.info(
                    "Data will not be migrated as there was already to many working hours time in between."
                )
        else:
            self._logger.warn(
                "Could not find the usage data to recover to in the logs."
            )
        super(Mig006FixUsageData, self)._run()

    def _rollback(self):
        if self._backup_usage_data:
            with open(self.USAGE_DATA_FILE_PATH, "w") as yaml_file:
                yaml.safe_dump(
                    self._backup_usage_data, yaml_file, default_flow_style=False
                )
                return True
        super(Mig006FixUsageData, self)._rollback()
