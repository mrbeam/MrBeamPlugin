from datetime import date

import pytest
from mock.mock import patch, mock_open

from octoprint_mrbeam.migration.Mig006 import Mig006FixUsageData

YAML_FILE = """airfilter:
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

YAML_FILE_SHOULD_NOT_RUN = """airfilter:
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
  job_time: 1831.3413743973
ts: 1698678400.341805
version: 0.15.0.post0
"""


@pytest.fixture
def migration006():
    return Mig006FixUsageData(None)


@pytest.mark.parametrize(
    "yaml_file,should_run",
    [
        (YAML_FILE, True),
        (YAML_FILE_SHOULD_NOT_RUN, False),
    ],
    ids=["should_run", "should_not_run"],
)
def test_migration_should_run(yaml_file, should_run, migration006):
    with patch("__builtin__.open", mock_open(read_data=yaml_file)) as mock_open_func:
        assert migration006.shouldrun(Mig006FixUsageData, "0.14.0") == should_run


def test_migration_id(migration006):
    assert migration006.id == "006"


@pytest.fixture
def mock_yaml_safe_dump():
    with patch("octoprint_mrbeam.migration.Mig006.yaml.safe_dump") as mock_dump:
        yield mock_dump


def test_migration_did_run(migration006, mock_yaml_safe_dump, mocker):
    mocker.patch.object(migration006, "exec_cmd", autospec=True)

    # Act
    migration006.run()

    # Assert
    migration006.exec_cmd.assert_any_call(
        "sudo cp /home/pi/.octoprint/analytics/usage.yaml /home/pi/.octoprint/analytics/usage.yaml_{}".format(
            date.today().strftime("%Y_%m_%d_%H_%M_%S")
        )
    )
