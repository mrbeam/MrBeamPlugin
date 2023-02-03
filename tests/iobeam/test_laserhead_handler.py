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
    MODEL_MRBEAM_2_DC_x,
)


@pytest.mark.parametrize(
    "model",
    [
        MODEL_MRBEAM_2_DC,
        MODEL_MRBEAM_2_DC_S,
        MODEL_MRBEAM_2_DC_x,
    ],
    ids=[
        "MODEL_MRBEAM_2_DC",
        "MODEL_MRBEAM_2_DC_S",
        "MODEL_MRBEAM_2_DC_x",
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
        MODEL_MRBEAM_2_DC_x,
    ],
    ids=[
        "MODEL_MRBEAM_2_DC",
        "MODEL_MRBEAM_2_DC_S",
        "MODEL_MRBEAM_2_DC_x",
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
        MODEL_MRBEAM_2_DC_x,
    ],
    ids=[
        "MODEL_MRBEAM_2",
        "MODEL_MRBEAM_2_DC_R1",
        "MODEL_MRBEAM_2_DC_R2",
        "MODEL_MRBEAM_2_DC",
        "MODEL_MRBEAM_2_DC_S",
        "MODEL_MRBEAM_2_DC_x",
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
