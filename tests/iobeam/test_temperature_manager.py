import pytest as pytest
from mock.mock import MagicMock, patch
from octoprint_mrbeam.iobeam.temperature_manager import TemperatureManager


@pytest.fixture
def temperature_manager(mrbeam_plugin):
    mrbeam_plugin.laserhead_handler = MagicMock(current_laserhead_max_temperature=55)

    temperature_manager = TemperatureManager(mrbeam_plugin)
    temperature_manager._analytics_handler = MagicMock()

    return temperature_manager


@pytest.mark.parametrize("new_tmp", [90.0, -6, None, "abc", "123", "12.3", "12,3"])
def test_handle_temp_invalid_temperature(new_tmp, temperature_manager):
    # Arrange

    # Act
    temperature_manager.handle_temp({"temp": new_tmp})
    tmp = temperature_manager.get_temperature()
    # Assert
    assert tmp == 20.0


def test_handle_temp_fire_warning_tmp_to_high(mrbeam_plugin):
    # if the current_laserhead_max_temperature is higher as MAX_ALLOWED_TEMPERATURE
    # the current_laserhead_max_temperature will be set to MAX_ALLOWED_TEMPERATURE -5
    # Arrange
    mrbeam_plugin.laserhead_handler = MagicMock(current_laserhead_max_temperature=99)

    temperature_manager = TemperatureManager(mrbeam_plugin)
    temperature_manager._analytics_handler = MagicMock()
    temperature_manager.temperature = 70.0
    with patch.object(
        temperature_manager._analytics_handler, "add_fire_detected"
    ) as analytics:
        # Act
        temperature_manager.handle_temp({"temp": 71.0})
        tmp = temperature_manager.get_temperature()
        # Assert
        assert tmp == 71.0
        assert analytics.called


def test_handle_temp_fire_temperature(temperature_manager):
    # Arrange
    temperature_manager.temperature = 60.0
    with patch.object(
        temperature_manager._analytics_handler, "add_fire_detected"
    ) as analytics:
        # Act
        temperature_manager.handle_temp({"temp": 61.0})
        tmp = temperature_manager.get_temperature()
        # Assert
        assert tmp == 61.0
        assert analytics.called


def test_handle_temp_slow_increase(temperature_manager):
    # Arrange
    temperature_manager.temperature = 25.0  # start temperature
    new_temperature = 40.0  # new temperature
    # Act
    temperature_manager.handle_temp({"temp": new_temperature})
    tmp1 = temperature_manager.get_temperature()
    temperature_manager.handle_temp({"temp": new_temperature})
    tmp2 = temperature_manager.get_temperature()
    temperature_manager.handle_temp({"temp": new_temperature})
    tmp3 = temperature_manager.get_temperature()
    temperature_manager.handle_temp({"temp": new_temperature})
    tmp4 = temperature_manager.get_temperature()
    temperature_manager.handle_temp({"temp": new_temperature})
    tmp5 = temperature_manager.get_temperature()
    # Assert
    assert tmp1 == 26
    assert tmp2 == 27
    assert tmp3 == 28
    assert tmp4 == 29
    assert tmp5 == 30


def test_handle_temp_slow_decrease(temperature_manager):
    # Arrange
    temperature_manager.temperature = 40.0  # start temperature
    new_temperature = 25.0  # new temperature
    # Act
    temperature_manager.handle_temp({"temp": new_temperature})
    tmp1 = temperature_manager.get_temperature()
    temperature_manager.handle_temp({"temp": new_temperature})
    tmp2 = temperature_manager.get_temperature()
    temperature_manager.handle_temp({"temp": new_temperature})
    tmp3 = temperature_manager.get_temperature()
    temperature_manager.handle_temp({"temp": new_temperature})
    tmp4 = temperature_manager.get_temperature()
    temperature_manager.handle_temp({"temp": new_temperature})
    tmp5 = temperature_manager.get_temperature()
    # Assert
    assert tmp1 == 39
    assert tmp2 == 38
    assert tmp3 == 37
    assert tmp4 == 36
    assert tmp5 == 35


def test_handle_temp_fast_increase(temperature_manager):
    # Arrange
    temperature_manager.temperature = 25.0  # start temperature
    # Act
    temperature_manager.handle_temp({"temp": 27.0})
    tmp1 = temperature_manager.get_temperature()
    temperature_manager.handle_temp({"temp": 30})
    tmp2 = temperature_manager.get_temperature()
    temperature_manager.handle_temp({"temp": 31.5})
    tmp3 = temperature_manager.get_temperature()
    # Assert
    assert tmp1 == 27
    assert tmp2 == 30
    assert tmp3 == 31.5


def test_handle_temp_fast_decrease(temperature_manager):
    # Arrange
    temperature_manager.temperature = 40.0  # start temperature
    # Act
    temperature_manager.handle_temp({"temp": 38})
    tmp1 = temperature_manager.get_temperature()
    temperature_manager.handle_temp({"temp": 35})
    tmp2 = temperature_manager.get_temperature()
    temperature_manager.handle_temp({"temp": 32.5})
    tmp3 = temperature_manager.get_temperature()
    # Assert
    assert tmp1 == 38
    assert tmp2 == 35
    assert tmp3 == 32.5
