#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from octoprint_mrbeam.mrb_logger import mrb_logger


_instance = None


def deviceInfo(use_dummy_values=False):
    global _instance
    if _instance is None:
        _instance = DeviceInfo(use_dummy_values=use_dummy_values)
    return _instance


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

    MODEL_MRBEAM_2 = "MRBEAM2"
    MODEL_MRBEAM_2_DC_R1 = "MRBEAM2_DC_R1"
    MODEL_MRBEAM_2_DC_R2 = "MRBEAM2_DC_R2"
    MODEL_MRBEAM_2_DC = "MRBEAM2_DC"

    def __init__(self, use_dummy_values=False):
        self._logger = mrb_logger("octoprint.plugins.mrbeam.util.device_info")
        self._device_data = (
            self._read_file() if not use_dummy_values else self._get_dummy_values()
        )

    def get(self, key, default=None):
        return self._device_data.get(key, default)

    def get_series(self):
        return self._device_data.get(self.KEY_DEVICE_SERIES)

    def get_serial(self):
        return self._device_data.get(self.KEY_SERIAL)

    def get_hostname(self):
        return self._device_data.get(self.KEY_HOSTNAME)

    def get_model(self):
        return self._device_data.get(self.KEY_MODEL, self.MODEL_MRBEAM_2)

    def get_production_date(self):
        return self._device_data.get(self.KEY_PRODUCTION_DATE, None)

    def _read_file(self):
        try:
            res = dict()
            with open(self.DEVICE_INFO_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    token = line.split("=")
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
            image_correction_markers="MrBeam2C-pink",
            model="MRBEAM2_DC",
            production_date="2014-06-11",
        )
