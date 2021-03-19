#!/usr/bin/env python3
from os.path import dirname, basename, join, split, realpath
import random
import pytest

from octoprint.settings import settings

# ~ Test camera settings, i.e. pic_settings and lens calibrations

from octoprint_mrbeam.camera.config import (
    calibration_needed_from_file,
    is_corner_calibration,
)
from octoprint_mrbeam.camera.definitions import QD_KEYS

sett = settings()  # fix some init bug
path = dirname(realpath(__file__))
CAM_SETTINGS_DIR = join(path, "rsc", "camera_settings")

SETTINGS_ALL = "pic_settings_all.yaml"
SETTINGS_RAW = "pic_settings_raw.yaml"
SETTINGS_GARBLED = "pic_settings_garbled.yaml"
SETTINGS_FACTORY = "pic_settings_factory.yaml"

SETTINGS_HAS_RAW = (SETTINGS_ALL, SETTINGS_RAW)
# SETTINGS_FACTORY_


@pytest.mark.datafiles(
    join(CAM_SETTINGS_DIR, SETTINGS_ALL),
    join(CAM_SETTINGS_DIR, SETTINGS_RAW),
    join(CAM_SETTINGS_DIR, SETTINGS_GARBLED),
)
def test_corner_calibration_file(datafiles):
    # ~ Settings contain the calibration values from the raw pictures are fine.
    for f_name in SETTINGS_HAS_RAW:
        settings_path = str(datafiles / f_name)
        assert not calibration_needed_from_file(settings_path)
    for f_name in (SETTINGS_GARBLED, "not_a_file_name.yaml"):
        settings_path = str(datafiles / f_name)
        assert calibration_needed_from_file(settings_path)


def test_is_corner_calibration():
    def rand_coords():
        return {q: [random.randint(0, 2000), random.randint(0, 1500)] for q in QD_KEYS}

    conf_map = {
        "corners": {
            "factory": {"raw": rand_coords()},
            "user": {"undistorted": rand_coords()},
        },
        "markers": {
            "factory": {
                "raw": rand_coords(),
                "undistorted": rand_coords(),
            },
            "user": {"undistorted": rand_coords()},
        },
    }
    assert is_corner_calibration(conf_map, "factory", "raw")
    assert is_corner_calibration(conf_map, "user", "undistorted")
    assert not is_corner_calibration(conf_map, "factory", "undistorted")
    assert not is_corner_calibration(conf_map, "user", "raw")
