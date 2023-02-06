import pytest
from mock.mock import patch

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
