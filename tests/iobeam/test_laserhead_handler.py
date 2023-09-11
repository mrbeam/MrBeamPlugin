import pytest
from mock.mock import patch, MagicMock

from octoprint_mrbeam.iobeam.laserhead_handler import (
    LaserheadHandler,
    LASERHEAD_S_ID,
    LASERHEAD_X_ID,
    LASERHEAD_STOCK_ID,
)
from octoprint_mrbeam.util.device_info import (
    MODEL_MRBEAM_2,
    MODEL_MRBEAM_2_DC,
    MODEL_MRBEAM_2_DC_S,
    MODEL_MRBEAM_2_DC_R1,
    MODEL_MRBEAM_2_DC_R2,
    MODEL_MRBEAM_2_DC_X,
)


@pytest.mark.parametrize(
    "model",
    [
        MODEL_MRBEAM_2_DC,
        MODEL_MRBEAM_2_DC_S,
        MODEL_MRBEAM_2_DC_X,
    ],
    ids=[
        "MODEL_MRBEAM_2_DC",
        "MODEL_MRBEAM_2_DC_S",
        "MODEL_MRBEAM_2_DC_X",
    ],
)
@patch(
    "octoprint_mrbeam.iobeam.laserhead_handler.LaserheadHandler.get_current_used_lh_model_id",
    return_value=LASERHEAD_X_ID,
)
def test_is_current_used_lh_model_supported_lh_x_supported(_, model, mrbeam_plugin):
    with patch(
        "octoprint_mrbeam.util.device_info.DeviceInfo.get_model",
        return_value=model,
    ):
        # Arrange
        laserhead_handler = LaserheadHandler(mrbeam_plugin)

        # Act
        result = laserhead_handler.is_current_used_lh_model_supported()
        # Assert
        assert result is True


@pytest.mark.parametrize(
    "model",
    [
        MODEL_MRBEAM_2,
        MODEL_MRBEAM_2_DC_R1,
        MODEL_MRBEAM_2_DC_R2,
    ],
    ids=[
        "MODEL_MRBEAM_2",
        "MODEL_MRBEAM_2_DC_R1",
        "MODEL_MRBEAM_2_DC_R2",
    ],
)
@patch(
    "octoprint_mrbeam.iobeam.laserhead_handler.LaserheadHandler.get_current_used_lh_model_id",
    return_value=LASERHEAD_X_ID,
)
def test_is_current_used_lh_model_supported_lh_x_not_supported(_, model, mrbeam_plugin):
    with patch(
        "octoprint_mrbeam.util.device_info.DeviceInfo.get_model",
        return_value=model,
    ):
        # Arrange
        laserhead_handler = LaserheadHandler(mrbeam_plugin)

        # Act
        result = laserhead_handler.is_current_used_lh_model_supported()
        # Assert
        assert result is False


@pytest.mark.parametrize(
    "model",
    [
        MODEL_MRBEAM_2_DC,
        MODEL_MRBEAM_2_DC_S,
        MODEL_MRBEAM_2_DC_X,
    ],
    ids=[
        "MODEL_MRBEAM_2_DC",
        "MODEL_MRBEAM_2_DC_S",
        "MODEL_MRBEAM_2_DC_X",
    ],
)
@patch(
    "octoprint_mrbeam.iobeam.laserhead_handler.LaserheadHandler.get_current_used_lh_model_id",
    return_value=LASERHEAD_S_ID,
)
def test_is_current_used_lh_model_supported_lh_s_supported(_, model, mrbeam_plugin):
    with patch(
        "octoprint_mrbeam.util.device_info.DeviceInfo.get_model",
        return_value=model,
    ):
        # Arrange
        laserhead_handler = LaserheadHandler(mrbeam_plugin)

        # Act
        result = laserhead_handler.is_current_used_lh_model_supported()
        # Assert
        assert result is True


@pytest.mark.parametrize(
    "model",
    [
        MODEL_MRBEAM_2,
    ],
    ids=[
        "MODEL_MRBEAM_2",
    ],
)
@patch(
    "octoprint_mrbeam.iobeam.laserhead_handler.LaserheadHandler.get_current_used_lh_model_id",
    return_value=LASERHEAD_S_ID,
)
def test_is_current_used_lh_model_supported_lh_s_not_supported(_, model, mrbeam_plugin):
    with patch(
        "octoprint_mrbeam.util.device_info.DeviceInfo.get_model",
        return_value=model,
    ):
        # Arrange
        laserhead_handler = LaserheadHandler(mrbeam_plugin)

        # Act
        result = laserhead_handler.is_current_used_lh_model_supported()
        # Assert
        assert result is False


@pytest.mark.parametrize(
    "model",
    [
        MODEL_MRBEAM_2,
        MODEL_MRBEAM_2_DC_R1,
        MODEL_MRBEAM_2_DC_R2,
        MODEL_MRBEAM_2_DC,
        MODEL_MRBEAM_2_DC_S,
        MODEL_MRBEAM_2_DC_X,
    ],
    ids=[
        "MODEL_MRBEAM_2",
        "MODEL_MRBEAM_2_DC_R1",
        "MODEL_MRBEAM_2_DC_R2",
        "MODEL_MRBEAM_2_DC",
        "MODEL_MRBEAM_2_DC_S",
        "MODEL_MRBEAM_2_DC_X",
    ],
)
@patch(
    "octoprint_mrbeam.iobeam.laserhead_handler.LaserheadHandler.get_current_used_lh_model_id",
    return_value=LASERHEAD_STOCK_ID,
)
def test_is_current_used_lh_model_supported_lh_stock_dc_mrbeam2_supported(
    _, model, mrbeam_plugin
):
    with patch(
        "octoprint_mrbeam.util.device_info.DeviceInfo.get_model",
        return_value=model,
    ):
        # Arrange
        laserhead_handler = LaserheadHandler(mrbeam_plugin)

        # Act
        result = laserhead_handler.is_current_used_lh_model_supported()
        # Assert
        assert result is True


@pytest.mark.parametrize(
    "model",
    [
        "unknown",
        None,
    ],
    ids=[
        "unknown",
        "None",
    ],
)
@patch(
    "octoprint_mrbeam.iobeam.laserhead_handler.LaserheadHandler.get_current_used_lh_model_id",
    return_value=LASERHEAD_STOCK_ID,
)
def test_is_current_used_lh_model_supported_invalid_model(_, model, mrbeam_plugin):
    with patch(
        "octoprint_mrbeam.util.device_info.DeviceInfo.get_model",
        return_value=model,
    ):
        # Arrange
        laserhead_handler = LaserheadHandler(mrbeam_plugin)

        # Act
        result = laserhead_handler.is_current_used_lh_model_supported()
        # Assert
        assert result is False


@pytest.mark.parametrize(
    "lh_model",
    [
        "unknown",
        None,
    ],
    ids=[
        "unknown",
        "None",
    ],
)
@patch(
    "octoprint_mrbeam.util.device_info.DeviceInfo.get_model",
    return_value=MODEL_MRBEAM_2_DC,
)
def test_is_current_used_lh_model_supported_invalid_laserhead_model(
    _, lh_model, mrbeam_plugin
):
    with patch(
        "octoprint_mrbeam.iobeam.laserhead_handler.LaserheadHandler.get_current_used_lh_model_id",
        return_value=lh_model,
    ):
        # Arrange
        laserhead_handler = LaserheadHandler(mrbeam_plugin)

        # Act
        result = laserhead_handler.is_current_used_lh_model_supported()
        # Assert
        assert result is False


@pytest.mark.parametrize(
    "laserhead,expected_value",
    [
        (LASERHEAD_STOCK_ID, 1.15),
        (LASERHEAD_S_ID, 1.15),
        (LASERHEAD_X_ID, 1.23),
        (None, 1),
        (1000, 1),
    ],
    ids=[
        "Laserhead Stock",
        "Laserhead S",
        "Laserhead X",
        "None Laserhead",
        "unknown Laserhead",
    ],
)
def test_current_laserhead_max_correction_factor(
    laserhead, expected_value, mrbeam_plugin
):
    # Arrange
    with patch(
        "octoprint_mrbeam.iobeam.laserhead_handler.LaserheadHandler.get_current_used_lh_model_id",
        return_value=laserhead,
    ):
        laserhead_handler = LaserheadHandler(mrbeam_plugin)

        # Act
        max_correction_factor = (
            laserhead_handler.current_laserhead_max_correction_factor
        )

        # Assert
        assert max_correction_factor == expected_value


def test_default_laserhead_max_correction_factor(mrbeam_plugin):
    # Arrange
    laserhead_handler = LaserheadHandler(mrbeam_plugin)

    # Act
    max_correction_factor = laserhead_handler.default_laserhead_max_correction_factor

    # Assert
    assert max_correction_factor == 1


@pytest.mark.parametrize(
    "laserhead,expected_value",
    [
        (LASERHEAD_STOCK_ID, 1500),
        (LASERHEAD_S_ID, 1500),
        (LASERHEAD_X_ID, 1600),
        (None, 1500),
        (1000, 1500),
    ],
    ids=[
        "Laserhead Stock",
        "Laserhead S",
        "Laserhead X",
        "None Laserhead",
        "unknown Laserhead",
    ],
)
def test_current_laserhead_max_intensity_including_correction(
    laserhead, expected_value, mrbeam_plugin
):
    # Arrange
    with patch(
        "octoprint_mrbeam.iobeam.laserhead_handler.LaserheadHandler.get_current_used_lh_model_id",
        return_value=laserhead,
    ):
        laserhead_handler = LaserheadHandler(mrbeam_plugin)

        # Act
        max_intensity = (
            laserhead_handler.current_laserhead_max_intensity_including_correction
        )

        # Assert
        assert max_intensity == expected_value


def test_default_laserhead_max_intensity_including_correction(mrbeam_plugin):
    # Arrange
    laserhead_handler = LaserheadHandler(mrbeam_plugin)

    # Act
    max_intensity = (
        laserhead_handler.default_laserhead_max_intensity_including_correction
    )

    # Assert
    assert max_intensity == 1500


@pytest.mark.parametrize(
    "laserhead,expected_value",
    [
        (LASERHEAD_STOCK_ID, 2),
        (LASERHEAD_S_ID, 3),
        (LASERHEAD_X_ID, 3),
        (None, 3),
        (1000, 3),
    ],
    ids=[
        "Laserhead Stock",
        "Laserhead S",
        "Laserhead X",
        "None Laserhead",
        "unknown Laserhead",
    ],
)
def test_current_laserhead_max_dust_factor(mrbeam_plugin, laserhead, expected_value):
    # Arrange
    with patch(
        "octoprint_mrbeam.iobeam.laserhead_handler.LaserheadHandler.get_current_used_lh_model_id",
        return_value=laserhead,
    ):
        laserhead_handler = LaserheadHandler(mrbeam_plugin)

        # Act
        max_dust_factor = laserhead_handler.current_laserhead_max_dust_factor

        # Assert
        assert max_dust_factor == expected_value


@pytest.mark.parametrize(
    "laserhead,expected_value",
    [
        (LASERHEAD_STOCK_ID, 40),
        (LASERHEAD_S_ID, 40),
        (LASERHEAD_X_ID, 80),
        (None, 40),
        (1000, 40),
    ],
    ids=[
        "Laserhead Stock",
        "Laserhead S",
        "Laserhead X",
        "None Laserhead",
        "unknown Laserhead",
    ],
)
def test_current_laserhead_lifespan(laserhead, expected_value, mrbeam_plugin):
    # Arrange
    with patch(
        "octoprint_mrbeam.iobeam.laserhead_handler.LaserheadHandler.get_current_used_lh_model_id",
        return_value=laserhead,
    ):
        laserhead_handler = LaserheadHandler(mrbeam_plugin)

        # Act
        lifespan = laserhead_handler.current_laserhead_lifespan

        # Assert
        assert lifespan == expected_value


@pytest.mark.parametrize(
    "laserhead,expected_value",
    [
        (LASERHEAD_STOCK_ID, 3.0),
        (LASERHEAD_S_ID, 3.0),
        (LASERHEAD_X_ID, 3.0),
        (None, 3.0),
        (1000, 3.0),
    ],
    ids=[
        "Laserhead Stock",
        "Laserhead S",
        "Laserhead X",
        "None Laserhead",
        "unknown Laserhead",
    ],
)
def test_current_laserhead_high_temperature_warn_offset(
    laserhead, expected_value, mrbeam_plugin
):
    # Arrange
    with patch(
        "octoprint_mrbeam.iobeam.laserhead_handler.LaserheadHandler.get_current_used_lh_model_id",
        return_value=laserhead,
    ):
        laserhead_handler = LaserheadHandler(mrbeam_plugin)

        # Act
        lifespan = laserhead_handler.current_laserhead_high_temperature_warn_offset

        # Assert
        assert lifespan == expected_value


@pytest.mark.parametrize(
    "laserhead,expected_value",
    [
        (LASERHEAD_STOCK_ID, 30),
        (LASERHEAD_S_ID, 50),
        (LASERHEAD_X_ID, 100),
        (None, 100),
        (1000, 100),
    ],
    ids=[
        "Laserhead Stock",
        "Laserhead S",
        "Laserhead X",
        "None Laserhead",
        "unknown Laserhead",
    ],
)
def test_current_laserhead_min_speed(laserhead, expected_value, mrbeam_plugin):
    # Arrange
    with patch(
        "octoprint_mrbeam.iobeam.laserhead_handler.LaserheadHandler.get_current_used_lh_model_id",
        return_value=laserhead,
    ):
        laserhead_handler = LaserheadHandler(mrbeam_plugin)

        # Act
        min_speed = laserhead_handler.current_laserhead_min_speed

        # Assert
        assert min_speed == expected_value


@pytest.mark.parametrize(
    "month,expected_offset",
    [
        (1, 0.0),
        (2, 0.0),
        (3, 0.0),
        (4, 0.0),
        (5, 0.0),
        (6, 1.0),
        (7, 2.0),
        (8, 2.0),
        (9, 1.0),
        (10, 0.0),
        (11, 0.0),
        (12, 0.0),
    ],
)
@patch("time.localtime")
def test_get_summermont_temperature_offset_ntp_synced(
    mock_localtime, month, expected_offset, mrbeam_plugin
):
    # Arrange
    laserhead_handler = LaserheadHandler(mrbeam_plugin)
    laserhead_handler._plugin.is_time_ntp_synced = MagicMock(return_value=True)

    mock_localtime.return_value.tm_mon = month
    offset = laserhead_handler.get_summermonth_temperature_offset()

    # Assert
    assert offset == expected_offset


@pytest.mark.parametrize(
    "month,expected_offset",
    [
        (1, 0.0),
        (2, 0.0),
        (3, 0.0),
        (4, 0.0),
        (5, 0.0),
        (6, 0.0),
        (7, 0.0),
        (8, 0.0),
        (9, 0.0),
        (10, 0.0),
        (11, 0.0),
        (12, 0.0),
    ],
)
@patch("time.localtime")
def test_get_summermont_temperature_offset_ntp_not_synced(
    mock_localtime, month, expected_offset, mrbeam_plugin
):
    # Arrange
    laserhead_handler = LaserheadHandler(mrbeam_plugin)
    laserhead_handler._plugin.is_time_ntp_synced = MagicMock(return_value=False)

    mock_localtime.return_value.tm_mon = month
    offset = laserhead_handler.get_summermonth_temperature_offset()

    # Assert
    assert offset == expected_offset


@pytest.mark.parametrize(
    "laserhead,expected_value",
    [
        (LASERHEAD_STOCK_ID, 55),
        (LASERHEAD_S_ID, 59),
        (LASERHEAD_X_ID, 60),
        (None, 55),
        (1000, 55),
    ],
    ids=[
        "Laserhead Stock",
        "Laserhead S",
        "Laserhead X",
        "None Laserhead",
        "unknown Laserhead",
    ],
)
def test_current_laserhead_max_temperature_without_summer_month_offset(
    laserhead, expected_value, mrbeam_plugin
):
    # Arrange
    with patch(
        "octoprint_mrbeam.iobeam.laserhead_handler.LaserheadHandler.get_current_used_lh_model_id",
        return_value=laserhead,
    ):
        laserhead_handler = LaserheadHandler(mrbeam_plugin)

        # Act
        current_laserhead_max_temperature = (
            laserhead_handler.current_laserhead_max_temperature
        )

        # Assert
        assert current_laserhead_max_temperature == expected_value


@pytest.mark.parametrize(
    "laserhead,expected_value",
    [
        (LASERHEAD_STOCK_ID, 55),
        (LASERHEAD_S_ID, 59),
        (LASERHEAD_X_ID, 60),
        (None, 55),
        (1000, 55),
    ],
    ids=[
        "Laserhead Stock",
        "Laserhead S",
        "Laserhead X",
        "None Laserhead",
        "unknown Laserhead",
    ],
)
def test_current_laserhead_max_temperature_with_summer_month_offset(
    laserhead, expected_value, mrbeam_plugin
):
    # Arrange
    with patch(
        "octoprint_mrbeam.iobeam.laserhead_handler.LaserheadHandler.get_current_used_lh_model_id",
        return_value=laserhead,
    ):
        laserhead_handler = LaserheadHandler(mrbeam_plugin)
        laserhead_handler.get_summermonth_temperature_offset = MagicMock(
            return_value=2.0
        )

        # Act
        max_temp = laserhead_handler.current_laserhead_max_temperature

        # Assert
        assert max_temp == expected_value + 2.0
