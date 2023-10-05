import time

import pytest
from _pytest.python_api import approx
from mock.mock import MagicMock, patch
from mock import mock_open

from octoprint_mrbeam import IoBeamEvents, AirFilter
from octoprint_mrbeam.analytics.usage_handler import (
    UsageHandler,
)
from tests.conftest import wait_till_event_received

LASERHEAD_SERIAL = "dummy_serial"
AIRFILTER_SERIAL = "dummy_serial"


@pytest.fixture
def usage_handler(mrbeam_plugin, air_filter):
    usage_file = """
    carbon_filter:
      complete: true
      job_time: 201600.0
    compressor:
      complete: true
      job_time: 40.0
    first_write: 1000.00
    gantry:
      complete: true
      job_time: 30.0
    laser_head:
      {laserhead_serial}:
        complete: true
        job_time: 20.0
    airfilter:
      {airfilter_serial}:
        carbon_filter:
          complete: true
          job_time: 100000.0
          pressure: 1200
          fan_test_rpm: 8800
        prefilter:
          complete: true
          job_time: 150000.0
          pressure: 2000
    prefilter:
      complete: true
      job_time: 14400.0
    restored: 0
    serial: 000000000694FD5D-2X
    succ_jobs:
      complete: true
      count: 0
    total:
      complete: true
      job_time: 0.0
    ts: 1000.00
    version: 0.14.1a2
    """.format(
        laserhead_serial=LASERHEAD_SERIAL, airfilter_serial=AIRFILTER_SERIAL
    )

    def settings_get(key, default=None, **kwargs):
        if key == ["analytics", "usage_filename"]:
            return "test.yaml"
        elif key == ["analytics", "folder"]:
            return "analytics"
        elif key == ["analytics", "usage_backup_filename"]:
            return "backup.yaml"

    with patch("__builtin__.open", mock_open(read_data=usage_file)), patch(
        "octoprint_mrbeam.analytics.usage_handler.UsageHandler._write_usage_data",
        return_value=True,
    ), patch("os.path.isfile", return_value=True):
        mrbeam_plugin.laserhead_handler.current_laserhead_max_dust_factor = 3.0
        mrbeam_plugin.laserhead_handler.get_current_used_lh_data = MagicMock(
            return_value={"serial": LASERHEAD_SERIAL}
        )
        air_filter.set_airfilter(4, "dummy_serial")
        mrbeam_plugin.airfilter = air_filter
        mrbeam_plugin._settings.get = MagicMock(
            side_effect=settings_get
        )  # return_value="test.yaml")
        usage_handler = UsageHandler(mrbeam_plugin)
        usage_handler._on_mrbeam_plugin_initialized(None, None)
        return usage_handler


def test_load_load_with_file(usage_handler):
    # Assert
    assert usage_handler.get_gantry_usage() == 30
    assert usage_handler.get_laser_head_usage() == 20
    assert usage_handler._get_prefilter_usage_time() == 150000
    assert usage_handler._get_carbon_filter_usage_time() == 100000
    assert usage_handler.get_total_usage() == 0
    assert usage_handler.get_total_jobs() == 0
    assert (
        usage_handler._usage_data["compressor"]["job_time"] == 40
    )  # there is curretnly no get_compressor_usage() method


def test_load_with_empty_file(mrbeam_plugin, air_filter):
    usage_file = """
        """

    def settings_get(key, default=None, **kwargs):
        if key == ["analytics", "usage_filename"]:
            return "test.yaml"
        elif key == ["analytics", "folder"]:
            return "analytics"
        elif key == ["analytics", "usage_backup_filename"]:
            return "backup.yaml"

    with patch("__builtin__.open", mock_open(read_data=usage_file)), patch(
        "octoprint_mrbeam.analytics.usage_handler.UsageHandler._write_usage_data",
        return_value=True,
    ), patch("os.path.isfile", lambda x: True):
        mrbeam_plugin.laserhead_handler.current_laserhead_max_dust_factor = 3.0
        mrbeam_plugin.laserhead_handler.get_current_used_lh_data = MagicMock(
            return_value={"serial": LASERHEAD_SERIAL}
        )
        mrbeam_plugin.airfilter = air_filter
        mrbeam_plugin._settings.get = MagicMock(
            side_effect=settings_get
        )  # return_value="test.yaml")
        usage_handler = UsageHandler(mrbeam_plugin)
        usage_handler._on_mrbeam_plugin_initialized(None, None)

    # Assert
    assert usage_handler.get_gantry_usage() == 0
    assert usage_handler.get_laser_head_usage() == 0
    assert usage_handler.get_prefilter_usage() == 0
    assert usage_handler.get_carbon_filter_usage() == 0
    assert usage_handler.get_total_usage() == 0
    assert usage_handler.get_total_jobs() == 0
    assert (
        usage_handler._usage_data["compressor"]["job_time"] == 0
    )  # there is curretnly no get_compressor_usage() method


@pytest.mark.parametrize(
    "serial",
    [
        "dummy_serial",
        None,
    ],
)
def test_reset_carbon_filter_usage(serial, usage_handler):
    # Arrange

    # Act
    with patch.object(
        usage_handler, "_write_usage_data", return_value=True
    ) as patched_write_usage_data:
        usage_handler.reset_carbon_filter_usage(serial)

    # Assert
    if serial is None:
        serial = "no_serial"
    assert (
        usage_handler._usage_data["airfilter"][serial]["carbon_filter"]["job_time"] == 0
    )
    patched_write_usage_data.assert_called_once()  # make sure usage file was written after reset


@pytest.mark.parametrize(
    "serial",
    [
        "dummy_serial",
        None,
    ],
)
def test_reset_prefilter_usage(serial, usage_handler):
    # Arrange

    # Act
    with patch.object(
        usage_handler, "_write_usage_data", return_value=True
    ) as patched_write_usage_data:
        usage_handler.reset_prefilter_usage(serial)

    # Assert
    if serial is None:
        serial = "no_serial"
    assert usage_handler._usage_data["airfilter"][serial]["prefilter"]["job_time"] == 0
    patched_write_usage_data.assert_called_once()  # make sure usage file was written after reset


@pytest.mark.parametrize(
    "airfilter_serial",
    [
        "no_serial",
        "dummyserial",
        "None",
    ],
)
def test_event_write(airfilter_serial, usage_handler):
    # Arrange
    payload = {"time": 10}
    usage_handler._dust_manager.get_mean_job_dust = MagicMock(return_value=3)
    usage_handler.start_time_total = 1
    usage_handler._airfilter.set_airfilter(1, airfilter_serial)

    # Act
    with patch.object(
        usage_handler, "_write_usage_data", return_value=True
    ) as patched_write_usage_data:
        usage_handler._event_write("event", payload)

    # Assert
    assert usage_handler._usage_data["airfilter"][airfilter_serial]["prefilter"][
        "job_time"
    ] == approx(237.2, abs=0.1)
    assert usage_handler._usage_data["airfilter"][airfilter_serial]["carbon_filter"][
        "job_time"
    ] == approx(237.2, abs=0.1)
    assert usage_handler._usage_data["laser_head"][LASERHEAD_SERIAL][
        "job_time"
    ] == approx(237.2, abs=0.1)
    assert usage_handler._usage_data["compressor"]["job_time"] == approx(9, abs=0.1)
    assert usage_handler._usage_data["gantry"]["job_time"] == approx(9, abs=0.1)
    assert usage_handler._usage_data["total"]["job_time"] == approx(11, abs=0.1)
    patched_write_usage_data.assert_called_once()  # make sure usage file was written after reset


@pytest.mark.parametrize(
    "airfilter_serial",
    [
        "no_serial",
        "serial",
    ],
)
def test_migrate_af2_jobtime(airfilter_serial, usage_handler):

    # Arrange
    usage_handler._airfilter.set_airfilter(1, airfilter_serial)

    # Act
    # usage_handler._migrate_af2_job_time()

    # with patch("builtins.open", mock_open()):
    with patch.object(usage_handler, "MIGRATION_WAIT", 0):
        usage_handler._event_bus.fire(IoBeamEvents.FAN_CONNECTED)
        wait_till_event_received(usage_handler._event_bus, IoBeamEvents.FAN_CONNECTED)
        time.sleep(0.1)  # wait for thread to be finished

    assert usage_handler.get_prefilter_usage() == 10
    assert usage_handler.get_carbon_filter_usage() == 20

    assert "prefilter" not in usage_handler._usage_data
    assert "carbon_filter" not in usage_handler._usage_data


@pytest.mark.parametrize(
    "airfilter_serial",
    [
        None,
    ],
)
def test_migrate_af2_jobtime_if_single_or_af1(
    airfilter_serial, usage_handler, mrbeam_plugin
):

    # Arrange
    usage_handler._airfilter = AirFilter(mrbeam_plugin)  # set airfilter to None

    # Act
    # usage_handler._migrate_af2_job_time()
    with patch.object(usage_handler, "MIGRATION_WAIT", 0):
        usage_handler._event_bus.fire(IoBeamEvents.FAN_CONNECTED)
        wait_till_event_received(usage_handler._event_bus, IoBeamEvents.FAN_CONNECTED)
        time.sleep(0.1)  # wait for thread to be finished

    assert (
        usage_handler._usage_data["airfilter"][usage_handler.UNKNOWN_SERIAL_KEY][
            "prefilter"
        ]["job_time"]
        == 14400
    )
    assert (
        usage_handler._usage_data["airfilter"][usage_handler.UNKNOWN_SERIAL_KEY][
            "carbon_filter"
        ]["job_time"]
        == 201600
    )

    assert "prefilter" not in usage_handler._usage_data
    assert "carbon_filter" not in usage_handler._usage_data


def test_carbon_filter_usage_af3(usage_handler, mrbeam_plugin):
    # Arrange
    mrbeam_plugin.airfilter.set_airfilter(8, AIRFILTER_SERIAL)

    # Act
    usage = usage_handler.get_carbon_filter_usage()

    # Assert
    assert usage == 40


def test_prefilter_usage_af3(usage_handler, mrbeam_plugin):
    # Arrange
    mrbeam_plugin.airfilter.set_airfilter(8, AIRFILTER_SERIAL)

    # Act
    usage = usage_handler.get_prefilter_usage()

    # Assert
    assert usage == 66


# TODO TEST time higher as pressure
# TODO TEST pressure higher as time

# test set pressure
@pytest.mark.parametrize(
    "pressure, expected",
    [
        (1000, 1200),  # lower values will not be set
        (2000, 2000),  # higher values will be set
        (0, 0),  # 20% lower will be set
    ],
)
def test_set_pressure_when_filter_stage_is_carbonfilter(
    pressure, expected, usage_handler, mrbeam_plugin
):
    # Arrange
    mrbeam_plugin.airfilter.set_airfilter(8, AIRFILTER_SERIAL)

    # Act
    with patch(
        "octoprint_mrbeam.analytics.usage_handler.UsageHandler._write_usage_data",
        return_value=True,
    ):
        usage_handler.set_pressure(pressure, AirFilter.CARBONFILTER)

    # Assert
    print(usage_handler._usage_data)
    assert (
        usage_handler._usage_data[UsageHandler.AIRFILTER_KEY][AIRFILTER_SERIAL][
            UsageHandler.CARBON_FILTER_KEY
        ][UsageHandler.PRESSURE_KEY]
        == expected
    )


@pytest.mark.parametrize(
    "pressure, expected",
    [
        (2000, 2000),  # lower values will not be set
        (3000, 3000),  # higher values will be set
        (0, 0),  # 20% lower will be set
    ],
)
def test_set_pressure_when_filter_stage_is_prefilter(
    pressure, expected, usage_handler, mrbeam_plugin
):
    # Arrange
    mrbeam_plugin.airfilter.set_airfilter(8, AIRFILTER_SERIAL)

    # Act
    with patch(
        "octoprint_mrbeam.analytics.usage_handler.UsageHandler._write_usage_data",
        return_value=True,
    ):
        usage_handler.set_pressure(pressure, AirFilter.PREFILTER)

    # Assert
    assert (
        usage_handler._usage_data[UsageHandler.AIRFILTER_KEY][AIRFILTER_SERIAL][
            UsageHandler.PREFILTER_KEY
        ][UsageHandler.PRESSURE_KEY]
        == expected
    )


@pytest.mark.parametrize(
    "filter_stage",
    [
        None,
        "invalid",
    ],
)
def test_set_pressure_when_filter_stage_is_not_valid(
    filter_stage, usage_handler, mrbeam_plugin
):
    # Arrange
    mrbeam_plugin.airfilter.set_airfilter(8, AIRFILTER_SERIAL)

    # Act
    with patch(
        "octoprint_mrbeam.analytics.usage_handler.UsageHandler._write_usage_data",
        return_value=True,
    ), pytest.raises(ValueError) as exc_info:
        usage_handler.set_pressure(200, filter_stage)

    assert "Unknown filter stage:" in str(exc_info.value)


def test_set_fan_test_rpm(usage_handler, mrbeam_plugin):
    # Arrange
    mrbeam_plugin.airfilter.set_airfilter(8, AIRFILTER_SERIAL)

    # Act
    with patch(
        "octoprint_mrbeam.analytics.usage_handler.UsageHandler._write_usage_data",
        return_value=True,
    ):
        usage_handler.set_fan_test_rpm(1000)

    # Assert
    assert (
        usage_handler._usage_data[UsageHandler.AIRFILTER_KEY][AIRFILTER_SERIAL][
            UsageHandler.CARBON_FILTER_KEY
        ][UsageHandler.FAN_TEST_RPM_KEY]
        == 1000
    )


# TODO test reset if 20% lower
