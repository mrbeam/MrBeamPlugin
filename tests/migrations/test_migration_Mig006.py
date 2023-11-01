import pytest
from mock.mock import patch, mock_open, call, MagicMock

from octoprint_mrbeam.migration.Mig006 import Mig006FixUsageData

OUTPUT_OF_EXEC_CMD = """/home/pi/.octoprint/logs/octoprint.log:2023-10-31 09:28:21,577 - octoprint.plugins.mrbeam.analytics.usage - ERROR - No job time found in {}, returning 0 - {'gantry': {'complete': True, 'job_time': 347.17822551727295}, 'succ_jobs': {'count': 2, 'complete': True}, 'airfilter': {17873: {'prefilter': {'complete': True, 'job_time': 347.17822551727295}, 'carbon_filter': {'complete': True, 'job_time': 347.17822551727295}}}, 'first_write': 1646219798.649828, 'ts': 1698744501.154159, 'prefilter': {'complete': True, 'job_time': 347.17822551727295}, 'compressor': {'complete': True, 'job_time': 347.17822551727295}, 'version': '0.15.0.post0', 'laser_head': {'75c8a85e-3c09-4918-befa-408251da5752': {'complete': True, 'job_time': 79.7521630525589}, 'LHS0030322910': {'complete': True, 'job_time': 142.30512607097626}, 'no_serial': {'complete': True, 'job_time': 0.0}, 'LHS0051021128': {'complete': True, 'job_time': 0.0}, '5078e646-0768-4ea2-9f54-61706de1df2c': {'complete': True, 'job_time': 0}}, 'serial': '000000008025FBB0-2R', 'total': {'complete': True, 'job_time': 1721.17822551727295}, 'carbon_filter': {'complete': True, 'job_time': 347.17822551727295}, 'restored': 1}
/home/pi/.octoprint/logs/octoprint.log:2023-10-31 09:28:26,850 - octoprint.plugins.mrbeam.analytics.usage - ERROR - No job time found in {}, returning 0 - {'gantry': {'complete': True, 'job_time': 347.17822551727295}, 'succ_jobs': {'count': 2, 'complete': True}, 'airfilter': {17873: {'prefilter': {'complete': True, 'job_time': 347.17822551727295}, 'carbon_filter': {'complete': True, 'job_time': 347.17822551727295}}}, 'first_write': 1646219798.649828, 'ts': 1698744506.345606, 'prefilter': {'complete': True, 'job_time': 347.17822551727295}, 'compressor': {'complete': True, 'job_time': 347.17822551727295}, 'version': '0.15.0.post0', 'laser_head': {'75c8a85e-3c09-4918-befa-408251da5752': {'complete': True, 'job_time': 79.7521630525589}, 'LHS0030322910': {'complete': True, 'job_time': 142.30512607097626}, 'no_serial': {'complete': True, 'job_time': 0.0}, 'LHS0051021128': {'complete': True, 'job_time': 0.0}, '5078e646-0768-4ea2-9f54-61706de1df2c': {'complete': True, 'job_time': 0}}, 'serial': '000000008025FBB0-2R', 'total': {'complete': True, 'job_time': 1721.17822551727295}, 'carbon_filter': {'complete': True, 'job_time': 347.17822551727295}, 'restored': 1}
/home/pi/.octoprint/logs/octoprint.log:2023-10-31 09:28:26,900 - octoprint.plugins.mrbeam.analytics.usage - ERROR - No job time found in {}, returning 0 - {'gantry': {'complete': True, 'job_time': 347.17822551727295}, 'succ_jobs': {'count': 2, 'complete': True}, 'airfilter': {17873: {'prefilter': {'complete': True, 'job_time': 347.17822551727295}, 'carbon_filter': {'complete': True, 'job_time': 347.17822551727295}}}, 'first_write': 1646219798.649828, 'ts': 1698744506.345606, 'prefilter': {'complete': True, 'job_time': 347.17822551727295}, 'compressor': {'complete': True, 'job_time': 347.17822551727295}, 'version': '0.15.0.post0', 'laser_head': {'75c8a85e-3c09-4918-befa-408251da5752': {'complete': True, 'job_time': 79.7521630525589}, 'LHS0030322910': {'complete': True, 'job_time': 142.30512607097626}, 'no_serial': {'complete': True, 'job_time': 0.0}, 'LHS0051021128': {'complete': True, 'job_time': 0.0}, '5078e646-0768-4ea2-9f54-61706de1df2c': {'complete': True, 'job_time': 0}}, 'serial': '000000008025FBB0-2R', 'total': {'complete': True, 'job_time': 1721.17822551727295}, 'carbon_filter': {'complete': True, 'job_time': 347.17822551727295}, 'restored': 1}
/home/pi/.octoprint/logs/octoprint.log:2023-10-31 09:28:26,955 - octoprint.plugins.mrbeam.analytics.usage - ERROR - No job time found in {}, returning 0 - {'gantry': {'complete': True, 'job_time': 347.17822551727295}, 'succ_jobs': {'count': 2, 'complete': True}, 'airfilter': {17873: {'prefilter': {'complete': True, 'job_time': 347.17822551727295}, 'carbon_filter': {'complete': True, 'job_time': 347.17822551727295}}}, 'first_write': 1646219798.649828, 'ts': 1698744506.345606, 'prefilter': {'complete': True, 'job_time': 347.17822551727295}, 'compressor': {'complete': True, 'job_time': 347.17822551727295}, 'version': '0.15.0.post0', 'laser_head': {'75c8a85e-3c09-4918-befa-408251da5752': {'complete': True, 'job_time': 79.7521630525589}, 'LHS0030322910': {'complete': True, 'job_time': 142.30512607097626}, 'no_serial': {'complete': True, 'job_time': 0.0}, 'LHS0051021128': {'complete': True, 'job_time': 0.0}, '5078e646-0768-4ea2-9f54-61706de1df2c': {'complete': True, 'job_time': 0}}, 'serial': '000000008025FBB0-2R', 'total': {'complete': True, 'job_time': 1721.17822551727295}, 'carbon_filter': {'complete': True, 'job_time': 347.17822551727295}, 'restored': 1}"""

OUTPUT_OF_EXEC_CMD_EMPTY = ""

PREVIOUS_YAML_FILE = """
carbon_filter:
  complete: false
  job_time: 889373.3413743973
prefilter:
  complete: false
  job_time: 889373.3413743973
compressor:
  complete: false
  job_time: 889373.3413743973
first_write: 1649453028.697643
gantry:
  complete: false
  job_time: 889373.3413743973
laser_head:
  no_serial:
    complete: false
    job_time: 0.0
restored: 2
serial: 00000000XXXXXX-2Q
succ_jobs:
  complete: false
  count: 620
total:
  complete: false
  job_time: 889373.3413743973
ts: 1698678400.341805
version: 0.15.0.post0
"""

BROKEN_YAML_FILE = """airfilter:
  60745:
    carbon_filter:
      complete: false
      job_time: 889373.3413743973
    prefilter:
      complete: false
      job_time: 889373.3413743973
carbon_filter:
  complete: false
  job_time: 889373.3413743973
prefilter:
  complete: false
  job_time: 889373.3413743973
compressor:
  complete: false
  job_time: 889373.3413743973
first_write: 1649453028.697643
gantry:
  complete: false
  job_time: 889373.3413743973
laser_head:
  no_serial:
    complete: false
    job_time: 0.0
restored: 2
serial: 00000000XXXXXX-2Q
succ_jobs:
  complete: false
  count: 620
total:
  complete: false
  job_time: 1831.3413743973
ts: 1698678400.341805
version: 0.15.0.post0
"""

BROKEN_YAML_FILE_TOO_OLD = """airfilter:
  60745:
    carbon_filter:
      complete: false
      job_time: 889373.3413743973
    prefilter:
      complete: false
      job_time: 889373.3413743973
compressor:
  complete: false
  job_time: 889373.3413743973
first_write: 1649453028.697643
gantry:
  complete: false
  job_time: 889373.3413743973
laser_head:
  no_serial:
    complete: false
    job_time: 0.0
restored: 2
serial: 00000000XXXXXX-2Q
succ_jobs:
  complete: false
  count: 620
total:
  complete: false
  job_time: 181831.3413743973
ts: 1698678400.341805
version: 0.15.0.post0
"""

CORRECT_YAML_FILE = """airfilter:
  60745:
    carbon_filter:
      complete: false
      job_time: 889373.3413743973
    prefilter:
      complete: false
      job_time: 889373.3413743973
compressor:
  complete: false
  job_time: 889373.3413743973
first_write: 1649453028.697643
gantry:
  complete: false
  job_time: 889373.3413743973
laser_head:
  no_serial:
    complete: false
    job_time: 0.0
restored: 2
serial: 00000000XXXXXX-2Q
succ_jobs:
  complete: false
  count: 620
total:
  complete: false
  job_time: 889373.3413743973
ts: 1698678400.341805
version: 0.15.0.post0
"""


@pytest.fixture
def migration006():
    return Mig006FixUsageData(None)


@pytest.mark.parametrize(
    "command_output,return_code,should_run",
    [
        (OUTPUT_OF_EXEC_CMD, 0, True),
        (OUTPUT_OF_EXEC_CMD_EMPTY, 0, False),
        ("grep: /home/pi/.octoprint/logs/: No such file or directory", 2, False),
    ],
    ids=["command_output", "command_output_empty", "command_error"],
)
def test_migration_should_run(command_output, return_code, should_run, migration006):
    with patch(
        "octoprint_mrbeam.migration.Mig006.exec_cmd_output",
        return_value=(command_output, return_code),
    ):
        assert migration006.shouldrun(Mig006FixUsageData, "0.14.0") == should_run


def test_migration_id(migration006):
    assert migration006.id == "006"


@pytest.fixture
def mock_yaml_safe_dump():
    with patch("octoprint_mrbeam.migration.Mig006.yaml.safe_dump") as mock_dump:
        yield mock_dump


def test_migration_did_run(migration006, mock_yaml_safe_dump):
    with patch(
        "octoprint_mrbeam.migration.Mig006.exec_cmd_output",
        return_value=(OUTPUT_OF_EXEC_CMD, 0),
    ), patch(
        "__builtin__.open", mock_open(read_data=BROKEN_YAML_FILE)
    ) as mock_open_func:

        # Act
        migration006.run()

        # Assert
        assert mock_yaml_safe_dump.call_args.args[0] == {
            "airfilter": {
                60745: {
                    "carbon_filter": {
                        "complete": False,
                        "job_time": 457.34137439729983,
                    },
                    "prefilter": {"complete": False, "job_time": 457.3413743972999},
                }
            },
            "compressor": {"complete": False, "job_time": 889373.3413743973},
            "first_write": 1649453028.697643,
            "gantry": {"complete": False, "job_time": 889373.3413743973},
            "laser_head": {"no_serial": {"complete": False, "job_time": 0.0}},
            "restored": 2,
            "serial": "00000000XXXXXX-2Q",
            "succ_jobs": {"complete": False, "count": 620},
            "total": {"complete": False, "job_time": 1831.3413743973},
            "ts": 1698678400.341805,
            "version": "0.15.0.post0",
        }


def test_migration_to_old(migration006, mock_yaml_safe_dump):
    with patch(
        "octoprint_mrbeam.migration.Mig006.exec_cmd_output",
        return_value=(OUTPUT_OF_EXEC_CMD, 0),
    ), patch(
        "__builtin__.open", mock_open(read_data=BROKEN_YAML_FILE_TOO_OLD)
    ) as mock_open_func:

        # Act
        migration006.run()

        # Assert
        mock_yaml_safe_dump.assert_not_called()
