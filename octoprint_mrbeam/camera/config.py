#!/usr/bin/env python3


from collections.abc import Mapping
import numpy as np
from octoprint_mrbeam.util import dict_map, dict_get
import yaml

from .definitions import (
    CALIB_REFS,
    QD_KEYS,
    FACT_UNDIST_CALIB_MARKERS_KEY,
    FACT_UNDIST_CORNERS_KEY,
    UNDIST_CALIB_MARKERS_KEY,
    UNDIST_CORNERS_KEY,
)

"""
Relates the config files in use for the camera.
pic_settings.yaml : stores information from the corner calibration
lens_calibration_xxxx_yyyy.npz : Stores the info for the lens calibration.
Can take different names for the different calibrations made (factory vs user calibration)
"""


def is_lens_calibration_file(path):
    try:
        _conf = np.load(path)
    except (IOError, ValueError):
        return False
    else:
        return all(k in list(_conf.keys()) for k in ("mtx", "dist"))


def is_corner_calibration_map(_map):
    assert isinstance(_map, Mapping)

    def is_qd_map(qdDict):
        return isinstance(qdDict, Mapping) and all(
            qd in qdDict
            and len(qdDict[qd]) == 2
            and all(not x is None for x in qdDict[qd])
            for qd in QD_KEYS
        )

    return is_qd_map(_map["corners"]) and is_qd_map(_map["markers"])


def get_corner_calibration(settings):
    # Values taken from the settings map. Used as a reference to warp the image correctly.
    # Legacy devices only have the values for the lensCorrected position.
    return dict_map(lambda key: settings.get(key, None), CALIB_REFS)


def is_corner_calibration(conf_map, config_type="factory", origin_picture="raw"):
    _conf = {
        edge_type: dict_get(conf_map, [edge_type, config_type, origin_picture], None)
        for edge_type in ("corners", "markers")
    }
    return is_corner_calibration_map(_conf)


def calibration_available(
    corner_config,
    lens_calibration_file_path=None,
    config_type="factory",
    origin_picture="raw",
):
    if origin_picture == "raw":
        # The lens calibration here is only optional.
        return is_corner_calibration(corner_config, config_type, origin_picture)
    else:
        return (
            is_corner_calibration(corner_config, config_type, origin_picture)
            and lens_calibration_file_path is not None
            and is_lens_calibration_file(lens_calibration_file_path)
        )


def calibration_needed(
    corner_conf, calibration_file_factory=None, calibration_file_user=None
):
    """Determine whether a corner calibration is required.

    Uses the config file (pic_settings.yaml) and optionnaly the lens
    calibration files
    """
    for config_type in ("user", "factory"):
        if is_corner_calibration(corner_conf, config_type, origin_picture="raw"):
            return False
    # now we need to know if both the lens undistorted corner calibration has been done,
    # and if the lens undistortion file is present. Both would be needed to correct the picture.
    origin_picture = "undistorted"
    if calibration_file_factory is not None and calibration_available(
        corner_conf, calibration_file_factory, "factory", origin_picture
    ):
        return False
    if calibration_file_user is not None and calibration_available(
        corner_conf, calibration_file_user, "user", origin_picture
    ):
        return False
    return True


def calibration_needed_from_file(
    config_path, calibration_file_factory=None, calibration_file_user=None
):
    try:
        with open(config_path) as f:
            corner_conf = get_corner_calibration(yaml.load(f))
    except IOError:
        return True
    else:
        return calibration_needed(
            corner_conf, calibration_file_factory, calibration_file_user
        )


def calibration_needed_from_flat(
    flat_corner_conf, calibration_file_factory=None, calibration_file_user=None
):
    """The pic_settings yaml file is written as mostly a shallow map."""
    corner_conf = get_corner_calibration(flat_corner_conf)
    return calibration_needed(
        corner_conf, calibration_file_factory, calibration_file_user
    )


def rm_undistorted_keys(flat_corner_conf, factory=False):
    """Remove the keys and values for the undistorted marker/arrow positions
    saved during the corner calibration."""
    flat_corner_conf = get_corner_calibration(flat_corner_conf)
    if factory:
        keys = [FACT_UNDIST_CALIB_MARKERS_KEY, FACT_UNDIST_CORNERS_KEY]
    else:
        keys = [UNDIST_CALIB_MARKERS_KEY, UNDIST_CORNERS_KEY]
    for k in keys:
        if k in flat_corner_conf.keys():
            flat_corner_conf.pop(k)
    return flat_corner_conf
