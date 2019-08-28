
import threading
import time
from octoprint.events import Events as OctoPrintEvents
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.iobeam.iobeam_handler import IoBeamEvents, IoBeamValueEvents
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.analytics.analytics_handler import analyticsHandler


# singleton
_instance = None

def temperatureManager():
	global _instance
	if _instance is None:
		_instance = TemperatureManager()
	return _instance

# This guy manages the temperature of the laser head
class TemperatureManager(object):

	TEMP_TIMER_INTERVAL = 3
	TEMP_MAX_AGE = 10 # seconds

	def __init__(self):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.temperaturemanager")

		self.temperature = None
		self.temperature_ts = 0
		self.temperature_max = _mrbeam_plugin_implementation.laserCutterProfileManager.get_current_or_default()['laser']['max_temperature']
		self.hysteresis_temperature = _mrbeam_plugin_implementation.laserCutterProfileManager.get_current_or_default()['laser']['hysteresis_temperature']
		self.cooling_duration = _mrbeam_plugin_implementation.laserCutterProfileManager.get_current_or_default()['laser']['cooling_duration']
		self.mode_time_based = self.cooling_duration > 0
		self.temp_timer = None
		self.is_cooling_since = 0

		self.dev_mode = _mrbeam_plugin_implementation._settings.get_boolean(['dev', 'iobeam_disable_warnings'])

		self._shutting_down = False

		self._subscribe()
		self._start_temp_timer()

		msg = "TemperatureManager initialized. temperature_max: {max}, {key}: {value}".format(
			max = self.temperature_max,
			key = "cooling_duration" if self.mode_time_based else "hysteresis_temperature",
			value = self.cooling_duration if self.mode_time_based else self.hysteresis_temperature)
		self._logger.info(msg)

	def _subscribe(self):
		_mrbeam_plugin_implementation._ioBeam.subscribe(IoBeamValueEvents.LASER_TEMP, self.handle_temp)

		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.PRINT_DONE, self.onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.PRINT_FAILED, self.onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.PRINT_CANCELLED, self.onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.SHUTDOWN, self.onEvent)

	def shutdown(self):
		self._shutting_down = True

	def reset(self):
		self.temperature_max = _mrbeam_plugin_implementation.laserCutterProfileManager.get_current_or_default()['laser']['max_temperature']
		self.hysteresis_temperature = _mrbeam_plugin_implementation.laserCutterProfileManager.get_current_or_default()['laser']['hysteresis_temperature']
		self.cooling_duration = _mrbeam_plugin_implementation.laserCutterProfileManager.get_current_or_default()['laser']['cooling_duration']
		self.mode_time_based = self.cooling_duration > 0
		self.is_cooling_since = 0

	def onEvent(self, event, payload):
		if event == IoBeamValueEvents.LASER_TEMP:
			self.handle_temp(payload)
		elif event in (OctoPrintEvents.PRINT_DONE, OctoPrintEvents.PRINT_FAILED, OctoPrintEvents.PRINT_CANCELLED):
			self.reset()
		elif event == OctoPrintEvents.SHUTDOWN:
			self.shutdown()

	def handle_temp(self, kwargs):
		self.temperature = kwargs['temp']
		if self.temperature_ts <= 0:
			self._logger.info("laser_temp - first temperature from laserhead: %s", self.temperature)
		self.temperature_ts = time.time()
		self._check_temp_val()
		analyticsHandler(_mrbeam_plugin_implementation).add_laser_temp_value(self.temperature)

	def request_temp(self):
		"""
		Send a temperature request to iobeam
		:return: True if sent successfully, False otherwise.
		"""
		return _mrbeam_plugin_implementation._ioBeam.send_temperature_request()

	def cooling_stop(self):
		"""
		Stop the laser for cooling purpose
		"""
		if _mrbeam_plugin_implementation._oneButtonHandler.is_printing():
			self._logger.info("cooling_stop()")
			self.is_cooling_since = time.time()
			_mrbeam_plugin_implementation._oneButtonHandler.cooling_down_pause()
			_mrbeam_plugin_implementation.fire_event(MrBeamEvents.LASER_COOLING_PAUSE, dict(temp=self.temperature))

	def cooling_resume(self):
		"""
		Resume laser once the laser has cooled down enough.
		"""
		self._logger.debug("cooling_resume()")
		_mrbeam_plugin_implementation.fire_event(MrBeamEvents.LASER_COOLING_RESUME, dict(temp=self.temperature))
		_mrbeam_plugin_implementation._oneButtonHandler.cooling_down_end(only_if_behavior_is_cooling=True)
		self.is_cooling_since = 0

	def get_temperature(self):
		return self.temperature

	def is_cooling(self):
		return (self.is_cooling_since is not None and self.is_cooling_since > 0)

	def is_temperature_recent(self):
		if self.temperature is None:
			if not self.dev_mode:
				self._logger.error("is_temperature_recent(): Laser temperature is None. never received a temperature value.")
			return False
		age = time.time() - self.temperature_ts
		if age > self.TEMP_MAX_AGE:
			self._logger.error("is_temperature_recent(): Laser temperature too old: must be more recent than %s s but actual age is %s s",
			                   self.TEMP_MAX_AGE, age)
			return False
		return True

	def _temp_timer_callback(self):
		try:
			if not self._shutting_down:
				self.request_temp()
				self._stop_if_temp_is_not_current()
				self._start_temp_timer()
		except:
			self._logger.exception("Exception in _temp_timer_callback(): ")
			# this might have been the reason for the exception. Let's try to stay alive anyway...
			self._start_temp_timer()

	def _start_temp_timer(self):
		if not self._shutting_down:
			self.temp_timer = threading.Timer(self.TEMP_TIMER_INTERVAL, self._temp_timer_callback)
			self.temp_timer.daemon = True
			self.temp_timer.name = "TemperatureTimer"
			self.temp_timer.start()
		else:
			self._logger.debug("Shutting down.")

	def _stop_if_temp_is_not_current(self):
		if not self.is_temperature_recent():
			if not _mrbeam_plugin_implementation.is_boot_grace_period():
				self._logger.error("_stop_if_temp_is_not_current() Laser temperature is not recent. Stopping laser.")
			self.cooling_stop()

	def _check_temp_val(self):
		# cooling break
		if not self.is_cooling() and (self.temperature is None or self.temperature > self.temperature_max):
			self._logger.info("Laser temperature exceeded limit. Current temp: %s, max: %s", self.temperature, self.temperature_max)
			self.cooling_stop()
		# resume hysteresis temp based
		elif self.is_cooling() and \
			not self.mode_time_based and \
			self.temperature is not None and \
			self.temperature <= self.hysteresis_temperature:
			self._logger.info("Laser temperature passed hysteresis limit. Current temp: %s, hysteresis: %s", self.temperature, self.hysteresis_temperature)
			self.cooling_resume()
		# resume time based
		elif self.is_cooling() and \
			 self.mode_time_based and \
			 time.time() - self.is_cooling_since > self.cooling_duration and\
			 self.temperature is not None and \
			 self.temperature < self.temperature_max:
			self._logger.warn("Cooling break duration passed: %ss - Current temp: %s", self.cooling_duration, self.temperature)
			self.cooling_resume()
		else:
			# self._logger.debug("Laser temperature nothing. Current temp: %s, self.is_cooling(): %s", self.temperatur, self.is_cooling())
			pass

