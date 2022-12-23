from octoprint_mrbeam.iobeam.airfilter import AirFilter


def test_model_name():
    # Arrange
    air_filter = AirFilter(None)
    air_filter.set_model_id(0)
    # Act
    model_name = air_filter.model
    # Assert
    assert model_name == "Air Filter System | Fan"

    # Arrange
    for i in range(1, 8):
        air_filter.set_model_id(i)
        # Act
        model_name = air_filter.model
        # Assert
        assert model_name == "Air Filter II System"

    # Arrange
    air_filter.set_model_id(8)
    # Act
    model_name = air_filter.model
    # Assert
    assert model_name == "Air Filter 3 System"

    # Arrange
    air_filter.set_model_id(None)
    # Act
    model_name = air_filter.model
    # Assert
    assert model_name == "Unknown"

    # Arrange
    air_filter.set_model_id(100)
    # Act
    model_name = air_filter.model
    # Assert
    assert model_name == "Unknown"


def test_model_id():
    # Arrange
    air_filter = AirFilter(None)
    air_filter.set_model_id(0)
    # Act
    model_id = air_filter.model_id
    # Assert
    assert model_id == 0


def test_serial():
    # Arrange
    air_filter = AirFilter(None)
    air_filter.set_serial("123456")
    # Act
    serial = air_filter.serial
    # Assert
    assert serial == "123456"


def test_pressure():
    # Arrange
    air_filter = AirFilter(None)
    air_filter.set_pressure(pressure=1)
    # Act
    pressure = air_filter.pressure
    # Assert
    assert pressure == 1

    # Arrange
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

    # Arrange
    air_filter.set_pressure(pressure2=None)
    # Act
    pressure = air_filter.pressure
    # Assert
    assert pressure == {
        "pressure1": 1,
        "pressure2": 2,
        "pressure3": 3,
        "pressure4": 4,
    }
