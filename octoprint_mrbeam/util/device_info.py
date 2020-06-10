#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from octoprint_mrbeam.mrb_logger import mrb_logger



DEVICE_INFO_FILE = '/etc/mrbeam'

_device_info = dict()
_logger = mrb_logger("octoprint.plugins.mrbeam.util.device_info")


def get_val_from_device_info(key, default=None, is_x86=False):
	global _device_info, _logger
	if not _device_info:
		try:
			with open(DEVICE_INFO_FILE, 'r') as f:
				for line in f:
					line = line.strip()
					token = line.split('=')
					if len(token) >= 2:
						_device_info[token[0]] = token[1]
		except Exception as e:
			_logger.error("Can't read device_info_file '%s' due to exception: %s", DEVICE_INFO_FILE, e)
			if is_x86:
				_device_info = dict(
					octopi="PROD 2019-12-12 13:05 1576155948",
					hostname="MrBeam-DEV",
					device_series="2X",
					device_type="MrBeam2X",
					serial="000000000694FD5D-2X",
					image_correction_markers="MrBeam2C-pink" ,)
	return _device_info.get(key, default)