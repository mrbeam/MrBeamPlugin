import time
import threading
from octoprint.events import Events as OctoPrintEvents
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.iobeam.iobeam_handler import IoBeamValueEvents
from octoprint_mrbeam.mrb_logger import mrb_logger
# singleton
_instance = None

def dustManager():
	global _instance
	if _instance is None:
		_instance = DustManager()
	return _instance

class DustManager(object):

	DEFAULT_DUST_TIMER_INTERVAL = 3
	DEFAUL_DUST_MAX_AGE = 10  # seconds
	FAN_MAX_INTENSITY = 100

	FAN_COMMAND_RETRIES = 2
	FAN_COMMAND_WAITTIME = 1.0

	def __init__(self):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.dustmanager")

		self._dust = None
		self._dust_ts = time.time()

		self._last_event = None
		self._shutting_down = False
		self._trail_extraction = None
		self._dust_timer = None
		self._dust_timer_interval = self.DEFAULT_DUST_TIMER_INTERVAL
		self._auto_timer = None
		self._command_response = None
		self._last_command = None
		self._command_event = threading.Event()

		self.dev_mode = _mrbeam_plugin_implementation._settings.get_boolean(['dev', 'iobeam_disable_warnings'])

		self._subscribe()
		self._start_dust_timer()
		self._stop_dust_extraction_thread()

		self.extraction_limit = _mrbeam_plugin_implementation.laserCutterProfileManager.get_current_or_default()['dust']['extraction_limit']
		self.auto_mode_time = _mrbeam_plugin_implementation.laserCutterProfileManager.get_current_or_default()['dust']['auto_mode_time']


		self._logger.debug("initialized!")

	def _subscribe(self):
		_mrbeam_plugin_implementation._ioBeam.subscribe(IoBeamValueEvents.DUST_VALUE, self._handle_dust)
		_mrbeam_plugin_implementation._ioBeam.subscribe(IoBeamValueEvents.FAN_ON_RESPONSE, self._on_command_response)
		_mrbeam_plugin_implementation._ioBeam.subscribe(IoBeamValueEvents.FAN_OFF_RESPONSE, self._on_command_response)
		_mrbeam_plugin_implementation._ioBeam.subscribe(IoBeamValueEvents.FAN_AUTO_RESPONSE, self._on_command_response)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.PRINT_STARTED, self._onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.PRINT_DONE, self._onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.PRINT_FAILED, self._onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.PRINT_CANCELLED, self._onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.SHUTDOWN, self._onEvent)

	def _handle_dust(self, args):
		self._dust = args['val']
		self._dust_ts = time.time()
		self.check_dust_value()
		self._send_dust_to_analytics(self._dust)
		self.send_status_to_frontend(self._dust)

	def _on_command_response(self, args):
		if args['message'].split(':')[1] == self._last_command.split(':')[0]:
			self._logger.debug("command response: {}".format(args))
			self._command_response = args['success']
			self._command_event.set()


	def _onEvent(self, event, payload):
		if event == OctoPrintEvents.PRINT_STARTED:
			self._start_dust_extraction_thread()
		elif event in (OctoPrintEvents.PRINT_DONE, OctoPrintEvents.PRINT_FAILED, OctoPrintEvents.PRINT_CANCELLED):
			self._last_event = event
			self._stop_dust_extraction_when_below(self.extraction_limit)
		elif event == OctoPrintEvents.SHUTDOWN:
			self.shutdown()

	def shutdown(self):
		self._shutting_down = True

	def _start_dust_extraction_thread(self, value=None):
		command_thread = threading.Thread(target=self._start_dust_extraction, args=(value,))
		command_thread.daemon = True
		command_thread.start()

	def _start_dust_extraction(self, value=None):
		if self._auto_timer is not None:
			self._auto_timer.cancel()
			self._auto_timer = None
		if value is None:
			if not self._send_fan_command('auto'):
				self._logger.warning("Could not start auto mode!")
		else:
			if value > 100:
				value = 100
			elif value < 0:
				value = 0
			if not self._send_fan_command('on:{}'.format(int(value))):
				self._logger.warning("Could not start fixed mode!")

	def _stop_dust_extraction_thread(self):
		command_thread = threading.Thread(target=self._stop_dust_extraction)
		command_thread.daemon = True
		command_thread.start()

	def _stop_dust_extraction(self):
		if not self._send_fan_command('off'):
			self._logger.warning("Could not turn off dust extraction!")

	def _stop_dust_extraction_when_below(self, value):
		if self._trail_extraction is None:
			self._trail_extraction = threading.Thread(target=self._wait_until, args=(value,))
			self._trail_extraction.daemon = True
			self._trail_extraction.start()

	def _wait_until(self, value):
		try:
			if self._dust is not None:
				self._logger.debug("starting trial dust extraction (value={}).".format(value))
				dust_start = self._dust
				dust_start_ts = self._dust_ts
				self._dust_timer_interval = 1
				self._start_dust_extraction_thread(self.FAN_MAX_INTENSITY)
				while self._continue_dust_extraction(value, dust_start_ts):
					time.sleep(self._dust_timer_interval)
				self._logger.debug("finished trial dust extraction.")
				dust_end = self._dust
				dust_end_ts = self._dust_ts
				self._dust_timer_interval = 3
				if dust_start_ts != dust_end_ts:
					_mrbeam_plugin_implementation._analytics_handler.write_final_dust(dust_start, dust_start_ts, dust_end, dust_end_ts)
				else:
					self._logger.warning("No dust value recieved during extraction time. Skipping writing analytics!")
				self._activate_timed_auto_mode(self.auto_mode_time)
				self._trail_extraction = None
			else:
				self._logger.warning("No dust value received so far. Skipping trial dust extraction!")
		except:
			self._logger.exception("Exception in _wait_until(): ")
		self.send_laser_job_event()

	def send_laser_job_event(self):
		try:
			self._logger.debug("Last event: {}".format(self._last_event))
			if self._last_event == OctoPrintEvents.PRINT_DONE:
				_mrbeam_plugin_implementation._event_bus.fire(MrBeamEvents.LASER_JOB_DONE)
				_mrbeam_plugin_implementation._plugin_manager.send_plugin_message("mrbeam", dict(event=MrBeamEvents.LASER_JOB_DONE))
				self._logger.debug("Fire event: {}".format(MrBeamEvents.LASER_JOB_DONE))
			elif self._last_event == OctoPrintEvents.PRINT_CANCELLED:
				_mrbeam_plugin_implementation._event_bus.fire(MrBeamEvents.LASER_JOB_CANCELLED)
				_mrbeam_plugin_implementation._plugin_manager.send_plugin_message("mrbeam", dict(event=MrBeamEvents.LASER_JOB_CANCELLED))
				self._logger.debug("Fire event: {}".format(MrBeamEvents.LASER_JOB_CANCELLED))
			elif self._last_event == OctoPrintEvents.PRINT_FAILED:
				_mrbeam_plugin_implementation._event_bus.fire(MrBeamEvents.LASER_JOB_FAILED)
				_mrbeam_plugin_implementation._plugin_manager.send_plugin_message("mrbeam", dict(event=MrBeamEvents.LASER_JOB_FAILED))
				self._logger.debug("Fire event: {}".format(MrBeamEvents.LASER_JOB_FAILED))
		except:
			self._logger.exception("Exception send_laser_done_event _wait_until(): ")


	def _continue_dust_extraction(self, value, started):
		if time.time() - started > 30:  # TODO: get this value from laser profile
			return False
		if self._dust is not None and self._dust < value:
			return False
		return True

	def _activate_timed_auto_mode(self, value):
		self._logger.debug("starting timed auto mode (value={}).".format(value))
		self._start_dust_extraction_thread()
		self._auto_timer = threading.Timer(value, self._auto_timer_callback)
		self._auto_timer.daemon = True
		self._auto_timer.start()

	def _auto_timer_callback(self):
		self._logger.debug("auto mode stopped!")
		self._stop_dust_extraction_thread()
		self._auto_timer = None

	def _send_fan_command(self, command, wait_time=-1.0, max_retries=-1):
		max_retries = self.FAN_COMMAND_RETRIES if max_retries < 0 else max_retries
		wait_time = self.FAN_COMMAND_WAITTIME if wait_time < 0 else wait_time
		retries = 0
		while retries <= max_retries:
			self._command_response = None
			self._last_command = command
			self._logger.debug("sending command: {}".format(command))
			_mrbeam_plugin_implementation._ioBeam.send_fan_command(command)
			retries += 1

			self._command_event.wait(timeout=wait_time)
			self._command_event.clear()

			if self._command_response:
				return True

		return False

	def _send_dust_to_analytics(self,val):
		"""
		Sends dust value periodically to analytics_handler to get overall stats and dust profile.
		:param val: measured dust value
		:return:
		"""
		_mrbeam_plugin_implementation._analytics_handler.add_dust_value(val)

	def check_dust_value(self):
		pass

	def _check_dust_is_current(self):
		if time.time() - self._dust_ts > self.DEFAUL_DUST_MAX_AGE:
			if not self.dev_mode:
				self._logger.error("Can't read dust value.")
			# TODO fire some Error pause (together with andy)

	def request_dust(self):
		return _mrbeam_plugin_implementation._ioBeam.send_fan_command("dust")

	def _dust_timer_callback(self):
		try:
			self.request_dust()
			self._check_dust_is_current()
			self._start_dust_timer()
		except:
			self._logger.exception("Exception in _dust_timer_callback(): ")
			self._start_dust_timer()

	def _start_dust_timer(self):
		if not self._shutting_down:
			self._dust_timer = threading.Timer(self._dust_timer_interval, self._dust_timer_callback)
			self._dust_timer.daemon = True
			self._dust_timer.start()
		else:
			self._logger.debug("Shutting down.")

	def send_status_to_frontend(self, dust):
		_mrbeam_plugin_implementation._plugin_manager.send_plugin_message("mrbeam", dict(status=dict(dust_value=dust)))
