import pytest
from mock.mock import patch, mock_open, call

from octoprint_mrbeam.migration.Mig006 import Mig006FixUsageData

OUTPUT_OF_EXEC_CMD = """('/home/pi/.octoprint/logs/octoprint.log.2023-10-06:2023-10-06 15:16:24,252 - octoprint.plugins.mrbeam.analytics.usage - ERROR - No job time found in {}, returning 0 - {'gantry': {'complete': True, 'job_time': 4116.064682483673}, 'succ_jobs': {'count': 11, 'complete': True}, 'airfilter': {60745: {'prefilter': {'pressure': 582, 'job_time': 455.8900738954544}, 'carbon_filter': {'fan_test_rpm': 10243.2, 'pressure': 509, 'job_time': 587.999161362648}}, 16807: {'prefilter': {'job_time': 78.47987282276154}, 'carbon_filter': {'job_time': 31.386178970336914}}}, 'first_write': 1681805878.307062, 'ts': 1696601781.320388, 'prefilter': {'complete': True, 'job_time': 82345.12}, 'compressor': {'complete': True, 'job_time': 4116.064682483673}, 'version': '0+unknown', 'laser_head': {'LHS0300821004': {'complete': True, 'job_time': 0}, 'LHS0030322910': {'complete': True, 'job_time': 0}, '5078e646-0768-4ea2-9f54-61706de1df2c': {'complete': True, 'job_time': 713.5697939395905}, 'no_serial': {'complete': True, 'job_time': 0.0}}, 'serial': '00000000FBC2BE1C-2Q', 'total': {'complete': True, 'job_time': 4116.064682483673}, 'carbon_filter': {'complete': True, 'job_time': 12423.0}, 'restored': 0}
/home/pi/.octoprint/logs/octoprint.log.2023-10-06:2023-10-06 15:16:24,275 - octoprint.plugins.mrbeam.analytics.usage - ERROR - No job time found in {}, returning 0 - {'gantry': {'complete': True, 'job_time': 4116.064682483673}, 'succ_jobs': {'count': 11, 'complete': True}, 'airfilter': {60745: {'prefilter': {'pressure': 582, 'job_time': 455.8900738954544}, 'carbon_filter': {'fan_test_rpm': 10243.2, 'pressure': 509, 'job_time': 587.999161362648}}, 16807: {'prefilter': {'job_time': 78.47987282276154}, 'carbon_filter': {'job_time': 31.386178970336914}}}, 'first_write': 1681805878.307062, 'ts': 1696601781.320388, 'prefilter': {'complete': True, 'job_time': 82345.12}, 'compressor': {'complete': True, 'job_time': 4116.064682483673}, 'version': '0+unknown', 'laser_head': {'LHS0300821004': {'complete': True, 'job_time': 0}, 'LHS0030322910': {'complete': True, 'job_time': 0}, '5078e646-0768-4ea2-9f54-61706de1df2c': {'complete': True, 'job_time': 713.5697939395905}, 'no_serial': {'complete': True, 'job_time': 0.0}}, 'serial': '00000000FBC2BE1C-2Q', 'total': {'complete': True, 'job_time': 4116.064682483673}, 'carbon_filter': {'complete': True, 'job_time': 12423.0}, 'restored': 0}
/home/pi/.octoprint/logs/octoprint.log.2023-10-06:2023-10-06 15:16:24,538 - octoprint.plugins.mrbeam.analytics.usage - ERROR - No job time found in {}, returning 0 - {'gantry': {'complete': True, 'job_time': 4116.064682483673}, 'succ_jobs': {'count': 11, 'complete': True}, 'airfilter': {60745: {'prefilter': {'pressure': 582, 'job_time': 455.8900738954544}, 'carbon_filter': {'fan_test_rpm': 10243.2, 'pressure': 509, 'job_time': 587.999161362648}}, 16807: {'prefilter': {'job_time': 78.47987282276154}, 'carbon_filter': {'job_time': 31.386178970336914}}}, 'first_write': 1681805878.307062, 'ts': 1696601781.320388, 'prefilter': {'complete': True, 'job_time': 82345.12}, 'compressor': {'complete': True, 'job_time': 4116.064682483673}, 'version': '0+unknown', 'laser_head': {'LHS0300821004': {'complete': True, 'job_time': 0}, 'LHS0030322910': {'complete': True, 'job_time': 0}, '5078e646-0768-4ea2-9f54-61706de1df2c': {'complete': True, 'job_time': 713.5697939395905}, 'no_serial': {'complete': True, 'job_time': 0.0}}, 'serial': '00000000FBC2BE1C-2Q', 'total': {'complete': True, 'job_time': 4116.064682483673}, 'carbon_filter': {'complete': True, 'job_time': 12423.0}, 'restored': 0}
/home/pi/.octoprint/logs/octoprint.log.2023-10-06:2023-10-06 15:16:24,582 - octoprint.plugins.mrbeam.analytics.usage - ERROR - No job time found in {}, returning 0 - {'gantry': {'complete': True, 'job_time': 4116.064682483673}, 'succ_jobs': {'count': 11, 'complete': True}, 'airfilter': {60745: {'prefilter': {'pressure': 582, 'job_time': 455.8900738954544}, 'carbon_filter': {'fan_test_rpm': 10243.2, 'pressure': 509, 'job_time'
: 587.999161362648}}, 16807: {'prefilter': {'job_time': 78.47987282276154}, 'carbon_filter': {'job_time': 31.386178970336914}}}, 'first_write': 1681805878.307062, 'ts': 1696601781.320388, 'prefilter': {'complete': True, 'job_time': 82345.12}, 'compressor': {'complete': True, 'job_time': 4116.064682483673}, 'version': '0+unknown', 'laser_head': {'LHS0300821004': {'complete': True, 'job_time': 0}, 'LHS0030322910': {'complete': True, 'job_time': 0}, '5078e646-0768-4ea2-9f54-61706de1df2c': {'complete': True, 'job_time': 713.5697939395905}, 'no_serial': {'complete': True, 'job_time': 0.0}}, 'serial': '00000000FBC2BE1C-2Q', 'total': {'complete': True, 'job_time': 4116.064682483673}, 'carbon_filter': {'complete': True, 'job_time': 12423.0}, 'restored': 0}
/home/pi/.octoprint/logs/octoprint.log.2023-10-06:2023-10-06 15:16:25,212 - octoprint.plugins.mrbeam.analytics.usage - ERROR - No job time found in {}, returning 0 - {'gantry': {'complete': True, 'job_time': 4116.064682483673}, 'succ_jobs': {'count': 11, 'complete': True}, 'airfilter': {60745: {'prefilter': {'pressure': 582, 'job_time': 455.8900738954544}, 'carbon_filter': {'fan_test_rpm': 10243.2, 'pressure': 509, 'job_time': 587.999161362648}}, 16807: {'prefilter': {'job_time': 78.47987282276154}, 'carbon_filter': {'job_time': 31.386178970336914}}}, 'first_write': 1681805878.307062, 'ts': 1696601781.320388, 'prefilter': {'complete': True, 'job_time': 82345.12}, 'compressor': {'complete': True, 'job_time': 4116.064682483673}, 'version': '0+unknown', 'laser_head': {'LHS0300821004': {'complete': True, 'job_time': 0}, 'LHS0030322910': {'complete': True, 'job_time': 0}, '5078e646-0768-4ea2-9f54-61706de1df2c': {'complete': True, 'job_time': 713.5697939395905}, 'no_serial': {'complete': True, 'job_time': 0.0}}, 'serial': '00000000FBC2BE1C-2Q', 'total': {'complete': True, 'job_time': 4116.064682483673}, 'carbon_filter': {'complete': True, 'job_time': 12423.0}, 'restored': 0}
/home/pi/.octoprint/logs/octoprint.log.2023-10-06:2023-10-06 15:16:25,308 - octoprint.plugins.mrbeam.analytics.usage - ERROR - No job time found in {}, returning 0 - {'gantry': {'complete': True, 'job_time': 4116.064682483673}, 'succ_jobs': {'count': 11, 'complete': True}, 'airfilter': {60745: {'prefilter': {'pressure': 582, 'job_time': 455.8900738954544}, 'carbon_filter': {'fan_test_rpm': 10243.2, 'pressure': 509, 'job_time': 587.999161362648}}, 16807: {'prefilter': {'job_time': 78.47987282276154}, 'carbon_filter': {'job_time': 31.386178970336914}}}, 'first_write': 1681805878.307062, 'ts': 1696601781.320388, 'prefilter': {'complete': True, 'job_time': 82345.12}, 'compressor': {'complete': True, 'job_time': 4116.064682483673}, 'version': '0+unknown', 'laser_head': {'LHS0300821004': {'complete': True, 'job_time': 0}, 'LHS0030322910': {'complete': True, 'job_time': 0}, '5078e646-0768-4ea2-9f54-61706de1df2c': {'complete': True, 'job_time': 713.5697939395905}, 'no_serial': {'complete': True, 'job_time': 0.0}}, 'serial': '00000000FBC2BE1C-2Q', 'total': {'complete': True, 'job_time': 4116.064682483673}, 'carbon_filter': {'complete': True, 'job_time': 12423.0}, 'restored': 0}
/home/pi/.octoprint/logs/octoprint.log.2023-10-06:2023-10-06 15:16:25,553 - octoprint.plugins.mrbeam.analytics.usage - ERROR - No job time found in {}, returning 0 - {'gantry': {'complete': True, 'job_time': 4116.064682483673}, 'succ_jobs': {'count': 11, 'complete': True}, 'airfilter': {60745: {'prefilter': {'pressure': 582, 'job_time': 455.8900738954544}, 'carbon_filter': {'fan_test_rpm': 10243.2, 'pressure': 509, 'job_time': 587.999161362648}}, 16807: {'prefilter': {'job_time': 78.47987282276154}, 'carbon_filter': {'job_time': 31.386178970336914}}}, 'first_write': 1681805878.307062, 'ts': 1696601781.320388, 'prefilter': {'complete': True, 'job_time': 82345.12}, 'compressor': {'complete': True, 'job_time': 4116.064682483673}, 'version': '0+unknown', 'laser_head': {'LHS0300821004': {'complete': True, 'job_time': 0}, 'LHS0030322910': {'complete': True, 'job_time': 0}, '5078e646-0768-4ea2-9f54-61706de1df2c': {'complete': True, 'job_time': 713.5697939395905}, 'no_serial': {'complete': True, 'job_time': 0.0}}, 'serial': '00000000FBC2BE1C-2Q', 'total': {'complete': True, 'job_time': 4116.064682483673}, 'carbon_filter': {'complete': True, 'job_time': 12423.0}, 'restored': 0}
/home/pi/.octoprint/logs/octoprint.log.2023-10-06:2023-10-06 15:16:25,625 - octoprint.plugins.mrbeam.analytics.usage - ERROR - No job time found in {}, returning 0 - {'gantry': {'complete': True, 'job_time': 4116.064682483673}, 'succ_jobs': {'count': 11, 'complete': True}, 'airfilter': {60745: {'prefilter': {'pressure': 582, 'job_time': 455.8900738954544}, 'carbon_filter': {'fan_test_rpm': 10243.2, 'pressure': 509, 'job_time': 587.999161362648}}, 16807: {'prefilter': {'job_time': 78.47987282276154}, 'carbon_filter': {'job_time': 31.386178970336914}}}, 'first_write': 1681805878.307062, 'ts': 1696601781.320388, 'prefilter': {'complete': True, 'job_time': 82345.12}, 'compressor': {'complete': True, 'job_time': 4116.064682483673}, 'version': '0+unknown', 'laser_head': {'LHS0300821004': {'complete': Tru"""

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
def migration0065():
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
def test_migration_should_run(command_output, return_code, should_run, migration0065):
    with patch(
        "octoprint_mrbeam.migration.Mig006.exec_cmd_output",
        return_value=(command_output, return_code),
    ):
        assert migration0065.shouldrun(Mig006FixUsageData, "0.14.0") == should_run


def test_migration_id(migration0065):
    assert migration0065.id == "006"
