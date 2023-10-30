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

    BEAMOS_VERSION_LOW = "0.18.0"
    BEAMOS_VERSION_HIGH = "0.20.1"
    COMMAND_TO_GET_LOGS = 'grep -r "octoprint.plugins.mrbeam.analytics.usage - ERROR - No job time found in {}" /home/pi/.octoprint/logs/'

    def __init__(self, plugin):
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
            Mig006FixUsageData.COMMAND_TO_GET_LOGS, log=True, shell=True
        )

        if code == 0 and command_output != "":  # TODO
            return True
        else:
            return False

    def _run(self):
        self._logger.debug("fix usage data")
        found_lines = exec_cmd_output(self.COMMAND_TO_GET_LOGS, log=True, shell=True)
        self._logger.debug("found_lines: {}".format(found_lines))
        found_lines = str(found_lines).replace("\\'", "'").replace("\\n", "\n")
        self._logger.debug("found_lines fixed: {}".format(found_lines))
        regex = r"No job time found in {}, returning 0 - {.*'airfilter': {(\d*): {'prefilter': {'[^}]*'job_time': (\d+\.\d+)[^}]*}, 'carbon_filter': {'[^}]*'job_time': (\d+\.\d+)[^}]*}"

        match = re.search(regex, found_lines)
        self._logger.debug("match: {}".format(match))

        if match:
            airfilter_serial = match.group(1)
            carbon_filter_job_time = match.group(2)
            prefilter_job_time = match.group(3)
            self._logger.debug("Airfilter Serial: {}".format(airfilter_serial))
            self._logger.debug(
                "Carbon Filter Job Time: {}".format(carbon_filter_job_time)
            )
            self._logger.debug("Prefilter Job Time: {}".format(prefilter_job_time))

            file_path = "/home/pi/.octoprint/analytics/usage.yaml"
            with open(file_path, "r") as yaml_file:
                yaml_data = yaml.load(yaml_file)

            # Update the job_time in the airfilter prefilter
            if "airfilter" in yaml_data:
                airfilter_data = yaml_data["airfilter"]
                if (
                    airfilter_serial in airfilter_data
                    and ("prefilter" or "carbon_filter")
                    in airfilter_data[airfilter_serial]
                ):
                    airfilter_data[airfilter_serial]["prefilter"][
                        "job_time"
                    ] = prefilter_job_time
                    airfilter_data[airfilter_serial]["carbon_filter"][
                        "job_time"
                    ] = carbon_filter_job_time

            # Save the modified YAML back to the file
            with open(file_path, "w") as yaml_file:
                yaml.safe_dump(yaml_data, yaml_file, default_flow_style=False)

        super(Mig006FixUsageData, self)._run()

    def _rollback(self):
        # no rollback needed
        super(Mig006FixUsageData, self)._rollback()
