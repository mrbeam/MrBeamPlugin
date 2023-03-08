#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import datetime
import os
import re
from octoprint_mrbeam.mrb_logger import mrb_logger


BEAMOS_DATE_PATTERN = re.compile(r"([A-Z]+)-([0-9]+-[0-9]+-[0-9]+)")
BEAMOS_VERSION_PATTERN = re.compile(r"([0-9]+.[0-9]+.[0-9]+\S*)")

_instance = None


def deviceInfo(use_dummy_values=False):
    global _instance
    if _instance is None:
        _instance = DeviceInfo(use_dummy_values=use_dummy_values)
    return _instance


MODEL_MRBEAM_2 = "MRBEAM2"
MODEL_MRBEAM_2_DC_R1 = "MRBEAM2_DC_R1"
MODEL_MRBEAM_2_DC_R2 = "MRBEAM2_DC_R2"
MODEL_MRBEAM_2_DC = "MRBEAM2_DC"
MODEL_MRBEAM_2_DC_S = "MRBEAM2_DC_S"
MODEL_MRBEAM_2_DC_X = "MRBEAM2_DC_X"
MODELS = {
    MODEL_MRBEAM_2: "Mr Beam II",
    MODEL_MRBEAM_2_DC_R1: "Mr Beam II dreamcut ready",
    MODEL_MRBEAM_2_DC_R2: "Mr Beam II dreamcut ready",
    MODEL_MRBEAM_2_DC: "Mr Beam II dreamcut",
    MODEL_MRBEAM_2_DC_S: "Mr Beam II dreamcut [S]",
    MODEL_MRBEAM_2_DC_X: "Mr Beam II dreamcut [x]",
}
MODEL_DEFAULT = MODEL_MRBEAM_2
DC_SERIES = [MODEL_MRBEAM_2_DC, MODEL_MRBEAM_2_DC_S, MODEL_MRBEAM_2_DC_X]


class DeviceInfo(object):

    DEVICE_INFO_FILE = "/etc/mrbeam"

    KEY_DEVICE_TYPE = "device_type"
    KEY_DEVICE_SERIES = "device_series"
    KEY_HOSTNAME = "hostname"
    KEY_SERIAL = "serial"
    KEY_OCTOPI = "octopi"
    KEY_IMAGE_CORRECTION_MARKERS = "image_correction_markers"
    KEY_PRODUCTION_DATE = "production_date"
    KEY_MODEL = "model"

    def __init__(self, use_dummy_values=False):
        self._logger = mrb_logger("octoprint.plugins.mrbeam.util.device_info")
        self._device_data = (
            self._read_file() if not use_dummy_values else self._get_dummy_values()
        )
        self._model = None

    def get(self, key, default=None):
        return self._device_data.get(key, default)

    def get_series(self):
        return self._device_data.get(self.KEY_DEVICE_SERIES)

    def get_type(self):
        return self._device_data.get(self.KEY_DEVICE_TYPE)

    def get_serial(self):
        return self._device_data.get(self.KEY_SERIAL)

    def get_hostname(self):
        return self._device_data.get(self.KEY_HOSTNAME)

    def get_model(self, refresh=False):
        """Gives you the device's model id like MRBEAM2 or MRBEAM2_DC The value
        is solely read from device_info file (/etc/mrbeam) and it's cached once
        read.

        :return: model
        :rtype: String
        """
        if refresh or self._model is None:
            self._model = self._device_data.get(self.KEY_MODEL, MODEL_DEFAULT)
        return self._model

    def is_mrbeam2_dc_series(self):
        return self.get_model() in DC_SERIES

    def get_production_date(self):
        return self._device_data.get(self.KEY_PRODUCTION_DATE, None)

    def get_beamos_version(self):
        """Expect the beamos date to be formatted as TIER-YYYY-MM-DD.

        returns the tier of the beamos and the date of the image creation

        the name of the method was kept for backward compatibility

        Returns:
            tier of beamos, beamos date
        """
        from octoprint_mrbeam.software_update_information import BEAMOS_LEGACY_DATE

        beamos_date = self._device_data.get(self.KEY_OCTOPI, None)
        if not beamos_date:
            return None, BEAMOS_LEGACY_DATE
        match = BEAMOS_DATE_PATTERN.match(beamos_date)
        if match:
            # date = datetime.date.fromisoformat(match.group(2)) # available in python3
            date = datetime.datetime.strptime(match.group(2), "%Y-%m-%d").date()
            return match.group(1), date
        else:
            return None, BEAMOS_LEGACY_DATE

    def get_beamos_version_number(self):
        """returns the beamos version.

        Returns:
            version of beamos
        """
        path_to_beamos_version_buster = os.path.join("/etc/beamos_version")
        path_to_beamos_version_legacy = os.path.join("/etc/octopi_version")
        if os.path.exists(path_to_beamos_version_buster):
            path_to_beamos_version = path_to_beamos_version_buster
        elif os.path.exists(path_to_beamos_version_legacy):
            path_to_beamos_version = path_to_beamos_version_legacy
        else:
            self._logger.error("can't find beamos version file")
            return None
        with open(path_to_beamos_version) as f:
            beamos_version = f.read()
        match = BEAMOS_VERSION_PATTERN.match(beamos_version)
        if match:
            return match.group(1)
        else:
            self._logger.debug("beamos_version invalid: " + beamos_version)
            return None

    def _read_file(self):
        try:
            # See configparser for a better solution
            res = dict()
            with open(self.DEVICE_INFO_FILE, "r") as f:
                for line in f:
                    token = list(map(str.strip, line.split("=")))
                    if len(token) >= 2:
                        res[token[0]] = token[1]
            return res
        except Exception as e:
            self._logger.error(
                "Can't read device_info_file '%s' due to exception: %s",
                self.DEVICE_INFO_FILE,
                e,
            )

    def _get_dummy_values(self):
        return dict(
            octopi="PROD 2019-12-12 13:05 1576155948",
            hostname="MrBeam-DEV",
            device_series="2X",
            device_type="MrBeam2X",
            serial="000000000694FD5D-2X",
            model="MRBEAM2_DC",
            production_date="2014-06-11",
        )

    def get_product_name(self):
        return MODELS.get(self._model, MODELS[MODEL_DEFAULT])
