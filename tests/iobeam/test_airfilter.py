import pytest
from mock.mock import MagicMock

from octoprint_mrbeam.iobeam.airfilter import AirFilter, airfilter

DEFAULT_PROFILE = {
    "carbonfilter": [
        {
            "lifespan": 280,
            "shopify_link": "products/aktivkohlefilter-inklusive-zehn-vorfilter?utm_source=beamos&utm_medium=beamos&utm_campaign=maintenance_page",
        }
    ],
    "carbonfilter_stages": 1,
    "prefilter": [
        {
            "lifespan": 40,
            "shopify_link": "products/vorfilter-mrbeam?utm_source=beamos&utm_medium=beamos&utm_campaign=maintenance_page",
            "heavy_duty_lifespan": 40,
            "heavy_duty_shopify_link": "products/mr-beam-vorfilter-kartusche-5er-pack?utm_source=beamos&utm_medium=beamos&utm_campaign=maintenance_page",
        }
    ],
    "prefilter_stages": 1,
}


def test_singelton(mrbeam_plugin):
    # Arrange
    air_filter = airfilter(mrbeam_plugin)

    # Act
    air_filter2 = airfilter(mrbeam_plugin)

    # Assert
    assert air_filter == air_filter2


def test_set_airfilter(air_filter):
    # Arrange

    # Act
    air_filter.set_airfilter(8, "123456")
    # Assert
    assert air_filter.model_id == 8
    assert air_filter.serial == "123456"


def test_model_name_AF1_or_fan(air_filter):
    # Arrange
    air_filter.connected = True  # AF1 or fan need to be connected state to show name
    # Act
    model_name = air_filter.model
    # Assert
    assert model_name == "Air Filter System | Fan"


def test_model_name_AF2(air_filter):
    # Arrange
    for i in range(2, 8):
        air_filter.set_airfilter(i, "serial")
        # Act
        model_name = air_filter.model
        # Assert
        assert model_name == "Air Filter II System"


def test_model_name_AF3(air_filter):
    # Arrange
    air_filter.set_airfilter(8, "serial")
    # Act
    model_name = air_filter.model
    # Assert
    assert model_name == "Air Filter 3 System"


def test_model_name_invalid_model_id(air_filter):
    # Arrange
    air_filter._model_id = None
    # Act
    model_name = air_filter.model
    # Assert
    assert model_name == "Unknown"

    # Arrange
    air_filter.set_airfilter(100, "serial")
    # Act
    model_name = air_filter.model
    # Assert
    assert model_name == "Unknown"


@pytest.mark.parametrize(
    "model_id, serial",
    [
        (0, None),
        (None, "123456"),
        (None, None),
    ],
)
def test_set_airfilter_when_information_is_missing(model_id, serial, air_filter):
    # Arrange

    # Act
    air_filter.set_airfilter(model_id, serial)
    # Assert
    assert air_filter.model_id is None
    assert air_filter.serial is None


def test_pressure_set_only_one(air_filter):
    # Arrange
    air_filter.set_pressure(pressure=1)
    # Act
    pressure = air_filter.pressure
    # Assert
    assert pressure == 1


def test_pressure_set_multiple(air_filter):
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


def test_pressure_set_invalid_data(air_filter):
    # Arrange
    air_filter.set_pressure(pressure2=None)
    # Act
    pressure = air_filter.pressure
    # Assert
    assert pressure is None


def test_temperatures_only_first(air_filter):
    # Arrange
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


def test_temperatures_all_values_at_once(air_filter):
    # Arrange
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


def test_temperatures_with_none_value(air_filter):
    # Arrange
    air_filter.set_temperatures(temperature2=None)  # temperature2 is not set
    # Act
    temperatures = air_filter.temperatures
    # Assert
    assert temperatures is None


def test_temperatures_int_value(air_filter):
    # Arrange
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


def test_temperatures_string_value(air_filter):
    # Arrange
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


def test_profile_for_airfilter_1(air_filter):
    # Arrange
    air_filter.set_airfilter(1, "serial")

    # Act
    profile = air_filter.profile

    # Assert
    assert profile == {
        "carbonfilter": [
            {
                "lifespan": 280,
                "shopify_link": "products/aktivkohlefilter-inklusive-zehn-vorfilter?utm_source=beamos&utm_medium=beamos&utm_campaign=maintenance_page",
            }
        ],
        "carbonfilter_stages": 1,
        "prefilter": [
            {
                "lifespan": 40,
                "shopify_link": "products/vorfilter-mrbeam?utm_source=beamos&utm_medium=beamos&utm_campaign=maintenance_page",
                "heavy_duty_lifespan": 80,
                "heavy_duty_shopify_link": "products/mr-beam-vorfilter-kartusche-5er-pack?utm_source=beamos&utm_medium=beamos&utm_campaign=maintenance_page",
            }
        ],
        "prefilter_stages": 1,
    }


def test_profile_for_airfilter_8(air_filter):
    # Arrange
    air_filter.set_airfilter(8, "serial")

    # Act
    profile = air_filter.profile

    # Assert
    assert profile == {
        "carbonfilter": [
            {
                "lifespan": 1120,
                "shopify_link": "maintenance/af3/mf",
            }
        ],
        "carbonfilter_stages": 1,
        "prefilter": [
            {
                "lifespan": 320,
                "shopify_link": "maintenance/af3/pf1",
            },
        ],
        "prefilter_stages": 1,
    }


def test_get_profile_invalid_id(air_filter):
    # Arrange
    air_filter._model_id = None

    # Act
    profile = air_filter.profile

    # Assert
    assert profile == DEFAULT_PROFILE


def test_get_profile_none_existing_id(air_filter):
    # Arrange
    air_filter.set_airfilter(100, "serial")

    # Act
    profile = air_filter.profile

    # Assert
    assert profile == DEFAULT_PROFILE


def test_get_profile_for_none_id(air_filter):
    # Arrange
    air_filter._model_id = None

    # Act
    profile = air_filter.profile

    # Assert
    assert profile == DEFAULT_PROFILE


def test_get_lifespan_for_airfilter_1_carbonfilter(air_filter):
    # Arrange
    air_filter.set_airfilter(1, "serial")

    # Act
    lifespan = air_filter.get_lifespan("carbonfilter")

    # Assert
    assert lifespan == 280


@pytest.mark.parametrize(
    "model_id, expected_lifespan",
    [
        (1, 40),
        (2, 40),
        (3, 40),
        (4, 40),
        (5, 40),
        (8, 320),
        (None, 40),
    ],
)
def test_get_lifespan_for_prefilter(model_id, expected_lifespan, air_filter):
    # Arrange
    air_filter.set_airfilter(model_id, "serial")

    # Act
    lifespan = air_filter.get_lifespan("prefilter")

    # Assert
    assert lifespan == expected_lifespan


@pytest.mark.parametrize(
    "model_id, expected_lifespan",
    [
        (1, [80]),
        (2, [80]),
        (3, [80]),
        (4, [80]),
        (5, [40]),
        (8, [320]),
        (None, [40]),
    ],
)
def test_get_lifespans_when_filterstage_is_prefilter_and_heavy_duty_prefilter_is_enabled(
    model_id, expected_lifespan, air_filter
):
    # Arrange
    air_filter.set_airfilter(model_id, "serial")
    air_filter.heavy_duty_prefilter_enabled = MagicMock(return_value=True)

    # Act
    lifespan = air_filter.get_lifespans(air_filter.PREFILTER)

    # Assert
    assert lifespan == expected_lifespan


def test_get_lifespan_for_invalid_filter(air_filter):
    # Arrange
    air_filter.set_airfilter(1, "serial")

    # Act
    lifespan = air_filter.get_lifespan("invalidfilter")

    # Assert
    assert lifespan is None


def test_get_lifespan_for_invalid_model(air_filter):
    # Arrange
    air_filter._model_id = None

    # Act
    lifespan = air_filter.get_lifespan("carbonfilter")

    # Assert
    assert lifespan == 280  # should be fallback value


def test_get_lifespan_for_invalid_filter_stage_id(air_filter):
    # Arrange
    air_filter.set_airfilter(1, "serial")

    # Act
    lifespan = air_filter.get_lifespan("prefilter", 20)

    # Assert
    assert lifespan == 40


def test_get_lifespan_for_invalid_filter_stage_id_input(air_filter):
    # Arrange
    air_filter.set_airfilter(1, "serial")

    # Act
    lifespan = air_filter.get_lifespan("prefilter", "invalid")

    # Assert
    assert lifespan == 40


def test_get_list_of_lifespans_for_prefilter(air_filter, mrbeam_plugin):
    # Arrange
    air_filter.set_airfilter(1, "serial")

    # Act
    lifespan = air_filter.get_lifespans("prefilter")

    # Assert
    assert lifespan == [40]

    # Arrange
    air_filter = AirFilter(mrbeam_plugin)
    air_filter.set_airfilter(8, "serial")

    # Act
    lifespan = air_filter.get_lifespans("prefilter")

    # Assert
    assert lifespan == [320]


def test_get_list_of_lifespans_for_carbonfilter(air_filter, mrbeam_plugin):
    # Arrange
    air_filter.set_airfilter(1, "serial")

    # Act
    lifespan = air_filter.get_lifespans("carbonfilter")

    # Assert
    assert lifespan == [280]

    # Arrange
    air_filter = AirFilter(mrbeam_plugin)
    air_filter.set_airfilter(8, "serial")

    # Act
    lifespan = air_filter.get_lifespans("carbonfilter")

    # Assert
    assert lifespan == [1120]


def test_get_list_of_lifespans_profile_none(air_filter):
    # Arrange
    air_filter._model_id = None

    # Act
    lifespan = air_filter.get_lifespans("prefilter")

    # Assert
    assert lifespan == [40]


def test_get_shopify_links_AF1_prefilter(air_filter):
    # Arrange
    air_filter.set_airfilter(1, "serial")

    # Act
    shopify_link = air_filter.get_shopify_links("prefilter")

    # Assert
    assert shopify_link == [
        "https://www.mr-beam.org/en/products/vorfilter-mrbeam?utm_source=beamos&utm_medium=beamos&utm_campaign=maintenance_page"
    ]


def test_get_shopify_links_profile_none(air_filter):
    # Arrange
    air_filter._model_id = None

    # Act
    shopify_link = air_filter.get_shopify_links("prefilter")

    # Assert
    assert shopify_link == [
        "https://www.mr-beam.org/en/products/vorfilter-mrbeam?utm_source=beamos&utm_medium=beamos&utm_campaign=maintenance_page"
    ]


def test_get_shopify_links_when_no_link_is_set_in_profile_then_return_empty_list(
    air_filter,
):
    # Arrange
    air_filter.set_airfilter(8, "serial")
    air_filter._profile = {"prefilter_stages": 1}

    # Act
    shopify_link = air_filter.get_shopify_links("prefilter")

    # Assert
    assert shopify_link == []


@pytest.mark.parametrize(
    "enabled",
    [
        (True),
        (False),
    ],
)
def test_heavy_duty_prefilter_enabled_when_enabled_then_true(enabled, air_filter):
    # Arrange
    air_filter._plugin.is_heavy_duty_prefilter_enabled = MagicMock(return_value=enabled)
    air_filter.set_airfilter(8, "serial")

    # Act
    heavy_duty_prefilter_enabled = air_filter.heavy_duty_prefilter_enabled()

    # Assert
    assert heavy_duty_prefilter_enabled is enabled


@pytest.mark.parametrize(
    "model_id, expected_pressure_drop",
    [
        (1, None),
        (8, 100),
    ],
)
def test_pressure_drop_prefilter(model_id, expected_pressure_drop, air_filter):
    # Arrange
    air_filter.set_airfilter(model_id, "serial")
    air_filter.set_pressure(pressure1=900, pressure2=800, pressure3=700, pressure4=600)

    # Act
    pressure_drop = air_filter.pressure_drop_prefilter

    # Assert
    assert pressure_drop == expected_pressure_drop


@pytest.mark.parametrize(
    "model_id, expected_pressure_drop",
    [
        (1, None),
        (8, 100),
    ],
)
def test_pressure_drop_main_filter(model_id, expected_pressure_drop, air_filter):
    # Arrange
    air_filter.set_airfilter(model_id, "serial")
    air_filter.set_pressure(pressure1=900, pressure2=800, pressure3=700, pressure4=600)

    # Act
    pressure_drop = air_filter.pressure_drop_mainfilter

    # Assert
    assert pressure_drop == expected_pressure_drop


def test_get_last_pressure_values(air_filter):
    # Arrange
    air_filter.set_pressure(pressure1=900, pressure2=800, pressure3=700, pressure4=600)
    air_filter.set_pressure(pressure1=950, pressure2=850, pressure3=750, pressure4=650)
    air_filter.set_pressure(pressure1=960, pressure2=860, pressure3=760, pressure4=660)
    air_filter.set_pressure(pressure1=970, pressure2=870, pressure3=770, pressure4=670)
    air_filter.set_pressure(pressure1=980, pressure2=880, pressure3=780, pressure4=680)
    air_filter.set_pressure(pressure1=990, pressure2=890, pressure3=790, pressure4=690)

    # Act
    pressure_values = air_filter.last_pressure_values

    # Assert
    assert pressure_values == [
        [950, 850, 750, 650],
        [960, 860, 760, 660],
        [970, 870, 770, 670],
        [980, 880, 780, 680],
        [990, 890, 790, 690],
    ]


def test_set_pressure_af2(air_filter):
    # Arrange
    air_filter.set_airfilter(2, "serial")

    # Act
    air_filter.set_pressure(pressure=900)
    air_filter.set_pressure(pressure=800)

    # Assert
    assert air_filter.last_pressure_values == [900, 800]


@pytest.mark.parametrize(
    "model_id, pressure, expected_blocked",
    [
        (1, 900, None),  # AF1 doesn't have this check
        (2, 900, None),  # AF2 doesn't have this check
        (8, 900, True),  # AF3 pressure below threshold
        (8, 9300, False),  # AF3 pressure above threshold
    ],
    ids=("AF1", "AF2", "AF3_below", "AF3_above"),
)
def test_exhaust_hose_is_blocked_if_af3(
    model_id, pressure, expected_blocked, air_filter
):
    # Arrange
    air_filter.set_airfilter(model_id, "serial")
    air_filter.set_pressure(pressure, pressure, pressure, pressure)

    # Act
    blocked = air_filter.exhaust_hose_is_blocked()

    # Assert
    assert blocked is expected_blocked


@pytest.mark.parametrize(
    "connected",
    [
        True,
        False,
    ],
)
def test_set_connected(connected, air_filter):
    # Arrange
    air_filter.set_airfilter(8, "serial")
    # Act
    air_filter.connected = connected

    # Assert
    assert air_filter.connected == connected


@pytest.mark.parametrize(
    "connected",
    [
        True,
        False,
    ],
)
def test_set_connected__when__non_smart_af(connected, air_filter):
    # Arrange
    air_filter.set_airfilter(None, None)
    # Act
    air_filter.connected = connected

    # Assert
    assert air_filter.connected == connected
