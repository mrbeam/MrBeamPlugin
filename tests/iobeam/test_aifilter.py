from mock.mock import MagicMock

from octoprint_mrbeam.iobeam.airfilter import AirFilter


def test_model_name_AF1_or_fan():
    # Arrange
    air_filter = AirFilter(MagicMock())
    air_filter.model_id = 0
    # Act
    model_name = air_filter.model
    # Assert
    assert model_name == "Air Filter System | Fan"


def test_model_name_AF2():
    # Arrange
    air_filter = AirFilter(MagicMock())
    for i in range(1, 8):
        air_filter.model_id = i
        # Act
        model_name = air_filter.model
        # Assert
        assert model_name == "Air Filter II System"


def test_model_name_AF3():
    # Arrange
    air_filter = AirFilter(MagicMock())
    air_filter.model_id = 8
    # Act
    model_name = air_filter.model
    # Assert
    assert model_name == "Air Filter 3 System"


def test_model_name_invalid_model_id():
    # Arrange
    air_filter = AirFilter(MagicMock())
    air_filter.model_id = None
    # Act
    model_name = air_filter.model
    # Assert
    assert model_name == "Unknown"

    # Arrange
    air_filter.model_id = 100
    # Act
    model_name = air_filter.model
    # Assert
    assert model_name == "Unknown"


def test_model_id():
    # Arrange
    air_filter = AirFilter(MagicMock())
    air_filter.model_id = 0
    # Act
    model_id = air_filter.model_id
    # Assert
    assert model_id == 0


def test_serial():
    # Arrange
    air_filter = AirFilter(MagicMock())
    air_filter.serial = "123456"
    # Act
    serial = air_filter.serial
    # Assert
    assert serial == "123456"


def test_pressure_set_only_one():
    # Arrange
    air_filter = AirFilter(MagicMock())
    air_filter.set_pressure(pressure=1)
    # Act
    pressure = air_filter.pressure
    # Assert
    assert pressure == 1


def test_pressure_set_multiple():
    # Arrange
    air_filter = AirFilter(MagicMock())
    air_filter.set_pressure(pressure1=1, pressure2=2, pressure3=3, pressure4=4)
    # Act
    pressure = air_filter.pressure
    # Assert
    assert pressure == {
        "pressure1": 1,
        "pressure2": 2,
        "pressure3": 3,
        "pressure4": 4,
    }


def test_pressure_set_invalid_data():
    # Arrange
    air_filter = AirFilter(MagicMock())
    air_filter.set_pressure(pressure2=None)
    # Act
    pressure = air_filter.pressure
    # Assert
    assert pressure is None


def test_temperatures_only_first():
    # Arrange
    air_filter = AirFilter(MagicMock())
    air_filter.set_temperatures(temperature1=1.0)
    # Act
    temperatures = air_filter.temperatures
    # Assert
    assert temperatures == {
        "temperature1": 1.0,
        "temperature2": None,
        "temperature3": None,
        "temperature4": None,
    }


def test_temperatures_all_values_at_once():
    # Arrange
    air_filter = AirFilter(MagicMock())
    air_filter.set_temperatures(
        temperature1=1.0, temperature2=2.0, temperature3=3.0, temperature4=4.0
    )
    # Act
    temperatures = air_filter.temperatures
    # Assert
    assert temperatures == {
        "temperature1": 1.0,
        "temperature2": 2.0,
        "temperature3": 3.0,
        "temperature4": 4.0,
    }


def test_temperatures_with_none_value():
    # Arrange
    air_filter = AirFilter(MagicMock())
    air_filter.set_temperatures(temperature2=None)  # temperature2 is not set
    # Act
    temperatures = air_filter.temperatures
    # Assert
    assert temperatures is None


def test_temperatures_int_value():
    # Arrange
    air_filter = AirFilter(MagicMock())
    air_filter.set_temperatures(temperature2=2)  # temperature2 is set
    # Act
    temperatures = air_filter.temperatures
    # Assert
    assert temperatures == {
        "temperature1": None,
        "temperature2": 2,
        "temperature3": None,
        "temperature4": None,
    }


def test_temperatures_string_value():
    # Arrange
    air_filter = AirFilter(MagicMock())
    air_filter.set_temperatures(temperature2="error")
    # Act
    temperatures = air_filter.temperatures
    # Assert
    assert temperatures == {
        "temperature1": None,
        "temperature2": "error",
        "temperature3": None,
        "temperature4": None,
    }
