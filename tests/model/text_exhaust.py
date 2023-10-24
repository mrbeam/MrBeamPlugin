import pytest

from octoprint_mrbeam.model.iobeam.exhaust import (
    ExhaustModelInitializationError,
    Device,
)


def test_exhaust_device__when__wrong_input__then__exception():
    with pytest.raises(ExhaustModelInitializationError):
        Device.from_dict({})
