
import os
import yaml
import re
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.mrbeam_events import MrBeamEvents

# singleton
_instance = None


def laserheadHandler(plugin):
	global _instance
	if _instance is None:
		_instance = LaserheadHandler(plugin)
	return _instance


class LaserheadHandler(object):
	LASER_POWER_GOAL = 950
	LASERHEAD_SERIAL_REGEXP = re.compile("^[0-9a-f-]{36}$")

	def __init__(self, plugin):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.laserhead")
		self._plugin = plugin
		self._settings = plugin._settings
		self._plugin_version = plugin._plugin_version

		self._lh_cache = {}
		self._last_used_lh_serial = None
		self._correction_settings = {}
		self._laser_heads_file = os.path.join(self._settings.getBaseFolder("base"), self._settings.get(['laser_heads', 'filename']))
		self._load_laser_heads_file()  # Loads correction_settings, last_used_lh_serial and lh_cache

		self._current_used_lh_serial = self._last_used_lh_serial

	def set_current_used_lh_data(self, lh_data):
		try:
			self._logger.info("Laserhead: %s", lh_data)
			self._current_used_lh_serial = lh_data['main']['serial']
			self._write_lh_data_to_cache(lh_data)

			self._calculate_and_write_correction_factor()

			self._plugin._analytics_handler.event_laserhead_info()
			self._write_laser_heads_file()
			self._plugin.fire_event(MrBeamEvents.LASER_HEAD_READ, dict(serial=lh_data['main']['serial']))

		except Exception as e:
			self._logger.exception('Exception during set_current_used_lh_data: {}'.format(e))

	def _write_lh_data_to_cache(self, lh_data):
		self._lh_cache[self._current_used_lh_serial] = lh_data

	def get_current_used_lh_data(self):
		if self._current_used_lh_serial:
			data = dict(
				serial=self._current_used_lh_serial,
				info=self._lh_cache[self._current_used_lh_serial]
			)
		else:
			data = dict(
				serial=None,
				info=dict(
					correction_factor=1,
				)
			)
		return data

	def get_correction_settings(self):
		settings = self._correction_settings
		if 'gcode_intensity_limit' not in settings:
			settings['gcode_intensity_limit'] = None
		if 'correction_factor_override' not in settings:
			settings['correction_factor_override'] = None
		if 'correction_enabled' not in settings:
			settings['correction_enabled'] = True

		return self._correction_settings

	def _validate_lh_serial(self, serial):
		try:
			return bool(self.LASERHEAD_SERIAL_REGEXP.match(serial))
		except:
			self.logger.exception("_validate_lh_serial() Failed to validate serial due to exception. Serial: %s ", serial)
			return False

	def _calculate_and_write_correction_factor(self):
		correction_factor = self._calculate_power_correction_factor()
		self._lh_cache[self._current_used_lh_serial]['correction_factor'] = correction_factor
		self._lh_cache[self._current_used_lh_serial]['mrbeam_plugin_version'] = self._plugin_version

	def _calculate_power_correction_factor(self):
		power_calibrations = self._lh_cache[self._current_used_lh_serial]['power_calibrations'][-1]
		p_65 = power_calibrations.get('power_65', None)
		p_75 = power_calibrations.get('power_75', None)
		p_85 = power_calibrations.get('power_85', None)

		correction_factor = 1

		if p_65 and p_75 and p_85:
			if p_65 < self.LASER_POWER_GOAL < p_75:
				step_difference = float(p_75-p_65)
				goal_difference = self.LASER_POWER_GOAL - p_65
				new_intensity = goal_difference * (75-65) / step_difference + 65
				correction_factor = new_intensity / 65.0

			elif p_75 < self.LASER_POWER_GOAL < p_85:
				step_difference = float(p_85 - p_75)
				goal_difference = self.LASER_POWER_GOAL - p_75
				new_intensity = goal_difference * (85-75) / step_difference + 75
				correction_factor = new_intensity / 65.0

		else:
			self._logger.info('Insufficient data for correction factor. Default factor: {cf}'.format(cf=correction_factor))

		self._logger.info('Laser head info - serial={serial}, p_65={p65}, p_75={p75}, p_85={p85}, correction_factor={cf}'
			.format(serial=self._current_used_lh_serial, p65=p_65, p75=p_75, p85=p_85, cf=correction_factor))

		return correction_factor

	def _load_laser_heads_file(self):
		if os.path.isfile(self._laser_heads_file):
			self._logger.info('Loading laser_heads.yaml...')
			try:
				with open(self._laser_heads_file, 'r') as stream:
					data = yaml.safe_load(stream)

				if data:
					if 'laser_heads' in data:
						self._lh_cache = data['laser_heads']

					if 'last_used_lh_serial' in data:
						self._last_used_lh_serial = data['last_used_lh_serial']

					if 'correction_settings' in data:
						self._correction_settings = data['correction_settings']
			except:
				self._logger.error("Can't read _laser_heads_file file: %s", self._laser_heads_file)

	def _write_laser_heads_file(self, file=None):
		self._logger.info('Writing to laser_heads.yaml...')

		data = dict(
			laser_heads=self._lh_cache,
			correction_settings=self._correction_settings,
			last_used_lh_serial=self._current_used_lh_serial
		)
		file = self._laser_heads_file if file is None else file
		try:
			with open(file, 'w') as outfile:
				yaml.safe_dump(data, outfile, default_flow_style=False)
		except:
			self._logger.exception("Can't write file %s due to an exception: ", file)

