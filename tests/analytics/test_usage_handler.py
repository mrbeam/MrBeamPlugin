import pytest
from mock.mock import MagicMock

from octoprint_mrbeam.analytics.usage_handler import UsageHandler


@pytest.fixture
def usage_handler(mrbeam_plugin):
    usagehandler = UsageHandler(mrbeam_plugin)
    return usagehandler


@pytest.mark.parametrize(
    "heavy_duty_filter, expected_lifespan",
    [
        (True, UsageHandler.HEAVY_DUTY_PREFILTER_LIFESPAN),
        (False, UsageHandler.DEFAULT_PREFILTER_LIFESPAN),
    ],
)
def test_get_prefilter_lifespan_when_havy_duty_prefilter_then_80_hours(
    heavy_duty_filter, expected_lifespan, usage_handler
):
    # Arrange
    usage_handler._settings.get = MagicMock(return_value=heavy_duty_filter)

    # Act
    lifespan = usage_handler.get_prefilter_lifespan()

    # Assert
    assert lifespan == expected_lifespan
