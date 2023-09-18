import __builtin__
import logging

import pytest
from mock.mock import MagicMock, call

from octoprint_mrbeam.mrb_logger import MrbLogger


@pytest.fixture
def mrb_logger():
    logger = MrbLogger("mock_logger")
    logger._get_analytics_handler = MagicMock()
    __builtin__._mrbeam_plugin_implementation = MagicMock()
    logger._terminal = MagicMock()
    return logger


def test_error_log(mrb_logger):
    # Arrange
    mrb_logger.log = MagicMock()

    # Act
    mrb_logger.error("test")

    # Assert
    mrb_logger.log.assert_called_once_with(logging.ERROR, "test", analytics=True)


def test_recursive_log(mrb_logger):
    # Arrange
    mrb_logger.logger.log = MagicMock()

    def analytics_log_event_side_effect(*args, **kwargs):
        print("log - {} - {}".format(args[0], args[1]))
        # trigger a log during the log
        mrb_logger.error("recursive log")

    mrb_logger._analytics_log_event = MagicMock(
        side_effect=analytics_log_event_side_effect
    )

    # Act
    # log an error
    mrb_logger.error("test")

    # Assert
    mrb_logger.logger.log.assert_has_calls(
        [
            call(logging.ERROR, "Recursive call for log: recursive log"),
            call(logging.ERROR, "recursive log"),
            call(logging.ERROR, "test"),
        ]
    )
