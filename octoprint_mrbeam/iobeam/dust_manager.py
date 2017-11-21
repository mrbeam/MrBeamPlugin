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

	DEFAULT_TIMER_INTERVAL = 3.0
	BOOST_TIMER_INTERVAL = 0.2
	MAX_TIMER_BOOST_DURATION = 3.0

	DEFAUL_DUST_MAX_AGE = 10  # seconds
	FAN_MAX_INTENSITY = 100

	INITIAL_WARNINGS_GRACE_PERIOD = 15
	FINAL_DUSTING_DURATION = 30

	FAN_COMMAND_RETRIES = 2
	FAN_COMMAND_WAITTIME = 1.0

	FAN_COMMAND_ON =      "on:{}"
	FAN_COMMAND_OFF =     "off"
	FAN_COMMAND_AUTO =    "auto"

	DATA_TYPE_DYNAMIC  =  "dynamic"
	DATA_TYPE_CONENCTED = "connected"


	def __init__(self):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.dustmanager")
		self.dev_mode = _mrbeam_plugin_implementation._settings.get_boolean(['dev', 'iobeam_disable_warnings'])

		self._state = None
		self._dust = None
		self._rpm = None
		self._connected = None
		self._data_ts = 0

		self._init_ts = time.time()
		self._last_event = None
		self._shutting_down = False
		self._trail_extraction = None
		self._timer = None
		self._timer_interval = self.DEFAULT_TIMER_INTERVAL
		self._timer_boost_ts = 0
		self._auto_timer = None
		# self._command_response = None
		self._last_command = ''
		# self._command_event = threading.Event()


		self._subscribe()
		self._start_timer()
		self._stop_dust_extraction()

		self.extraction_limit = _mrbeam_plugin_implementation.laserCutterProfileManager.get_current_or_default()['dust']['extraction_limit']
		self.auto_mode_time = _mrbeam_plugin_implementation.laserCutterProfileManager.get_current_or_default()['dust']['auto_mode_time']


		self._logger.debug("initialized!")

	def is_fan_connected(self):
		return self._connected

	def shutdown(self):
		self._shutting_down = True

	def _subscribe(self):
		_mrbeam_plugin_implementation._ioBeam.subscribe(IoBeamValueEvents.DYNAMIC_VALUE, self._handle_fan_data)
		# _mrbeam_plugin_implementation._ioBeam.subscribe(IoBeamValueEvents.DUST_VALUE, self._handle_dust)
		# _mrbeam_plugin_implementation._ioBeam.subscribe(IoBeamValueEvents.RPM_VALUE, self._handle_rpm)
		_mrbeam_plugin_implementation._ioBeam.subscribe(IoBeamValueEvents.FAN_ON_RESPONSE, self._on_command_response)
		_mrbeam_plugin_implementation._ioBeam.subscribe(IoBeamValueEvents.FAN_OFF_RESPONSE, self._on_command_response)
		_mrbeam_plugin_implementation._ioBeam.subscribe(IoBeamValueEvents.FAN_AUTO_RESPONSE, self._on_command_response)

		_mrbeam_plugin_implementation._event_bus.subscribe(MrBeamEvents.READY_TO_LASER_START, self._onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(MrBeamEvents.READY_TO_LASER_START, self._onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(MrBeamEvents.READY_TO_LASER_CANCELED, self._onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.SLICING_DONE, self._onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.PRINT_STARTED, self._onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.PRINT_DONE, self._onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.PRINT_FAILED, self._onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.PRINT_CANCELLED, self._onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.SHUTDOWN, self._onEvent)

	def _handle_fan_data(self, args):
		#ANDYTEST remove this
		self.do_debug_stuff()

		self._logger.info("ANDYTEST _handle_fan_data() args: %s", args)

		err = False
		if args['state'] is not None:
			self._state = args['state']
		else:
			err = True
		if args['dust'] is not None:
			self._dust = args['dust']
		else:
			err = True
		if args['rpm'] is not None:
			self._rpm = args['rpm']
		else:
			err = True

		self._connected = args['connected']
		if self._connected is not None:
			self._unboost_timer_interval()

		if not err:
			self._data_ts = time.time()

		self._validate_values()
		self._send_dust_to_analytics(self._dust)
		self._send_status_to_frontend()


	def _on_command_response(self, args):
		self._logger.info("ANDYTEST _on_command_response() args: %s", args)
		if args['success']:
			if args['message'].split(':')[1] != self._last_command.split(':')[0]:
				# I'm not sure if we need to check or what to do if the command doesn't match.
				self._logger.warn("Fan command response doesn't match expected command: expected: {} received: fan:{} args: {}".format(self._last_command, args['message'], args))
		else:
			# TODO ANDY stop laser
			self._logger.error("Fan command responded error: received: fan:{} args: {}".format(args['message'], args))


	def _onEvent(self, event, payload):
		if event in (OctoPrintEvents.SLICING_DONE, MrBeamEvents.READY_TO_LASER_START, OctoPrintEvents.PRINT_STARTED):
			self._start_dust_extraction()
			self._boost_timer_interval()
		elif event == MrBeamEvents.READY_TO_LASER_CANCELED:
			self._stop_dust_extraction()
			self._unboost_timer_interval()
		elif event in (OctoPrintEvents.PRINT_DONE, OctoPrintEvents.PRINT_FAILED, OctoPrintEvents.PRINT_CANCELLED):
			self._last_event = event
			self._do_end_dusting()
		elif event == OctoPrintEvents.SHUTDOWN:
			self.shutdown()

	def _start_dust_extraction(self, value=None):
		"""
		Turn on fan on auto mode or set to constant value.
		:param value: Default: auto. 0-100 if constant value required.
		:return:
		"""
		if self._auto_timer is not None:
			self._auto_timer.cancel()
			self._auto_timer = None
		if value is None or value == self.FAN_COMMAND_AUTO:
			self._send_fan_command(self.FAN_COMMAND_AUTO)
		else:
			if value > 100:
				value = 100
			elif value < 0:
				value = 0
			self._send_fan_command(self.FAN_COMMAND_ON.format(int(value)))

	def _stop_dust_extraction(self):
		self._send_fan_command(self.FAN_COMMAND_OFF)

	def _do_end_dusting(self):
		if self._trail_extraction is None:
			self._trail_extraction = threading.Thread(target=self.__do_end_dusting_thread)
			self._trail_extraction.daemon = True
			self._trail_extraction.start()

	def __do_end_dusting_thread(self):
		try:
			if self._dust is not None:
				self._logger.debug("starting trial dust extraction (value={}).".format(self.extraction_limit))
				dust_start = self._dust
				dust_start_ts = self._data_ts
				self._start_dust_extraction(self.FAN_MAX_INTENSITY)
				while self.__continue_dust_extraction(self.extraction_limit, dust_start_ts):
					time.sleep(1)
				self._logger.debug("finished end dusting.")
				dust_end = self._dust
				dust_end_ts = self._data_ts
				if dust_start_ts != dust_end_ts:
					_mrbeam_plugin_implementation._analytics_handler.write_final_dust(dust_start, dust_start_ts, dust_end, dust_end_ts)
				else:
					self._logger.warning("No dust value received during extraction time. Skipping writing analytics!")
				self._activate_timed_auto_mode(self.auto_mode_time)
				self._trail_extraction = None
			else:
				self._logger.warning("No dust value received so far. Skipping trial dust extraction!")
		except:
			self._logger.exception("Exception in __do_end_dusting_thread(): ")
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
			self._logger.exception("Exception send_laser_done_event send_laser_job_event(): ")


	def __continue_dust_extraction(self, value, started):
		if time.time() - started > self.FINAL_DUSTING_DURATION:  # TODO: get this value from laser profile
			return False
		if self._dust is not None and self._dust < value:
			return False
		return True

	def _activate_timed_auto_mode(self, value):
		self._logger.debug("starting timed auto mode (value={}).".format(value))
		self._start_dust_extraction()
		self._auto_timer = threading.Timer(value, self._auto_timer_callback)
		self._auto_timer.daemon = True
		self._auto_timer.start()

	def _auto_timer_callback(self):
		self._logger.debug("auto mode stopped!")
		self._stop_dust_extraction()
		self._auto_timer = None

	def _send_fan_command(self, command):
		self._logger.debug("ANDYTEST _send_fan_command() command: {}".format(command))
		self._last_command = command
		ok = _mrbeam_plugin_implementation._ioBeam.send_fan_command(command)
		if not ok:
			self._logger.error("Failed to send fan command to iobeam: %s", command)
		return ok

	def _send_dust_to_analytics(self, val):
		"""
		Sends dust value periodically to analytics_handler to get overall stats and dust profile.
		:param val: measured dust value
		:return:
		"""
		_mrbeam_plugin_implementation._analytics_handler.add_dust_value(val)

	def _validate_values(self):
		result = True
		if time.time() - self._data_ts > self.DEFAUL_DUST_MAX_AGE:
			result = False
		if self._state is None or self._rpm is None or self._dust is None:
			result = False

		if not result and not self.dev_mode and time.time() - self._init_ts > self.INITIAL_WARNINGS_GRACE_PERIOD:
			self._logger.error("Invalid fan data from iobeam: state:{state}, rpm:{rpm}, dust:{dust}, age:{age}s".format(
				state=self._state, rpm=self._rpm, dust=self._dust, age=(time.time() - self._data_ts)
			))

		return result

	def _request_value(self, value):
		return _mrbeam_plugin_implementation._ioBeam.send_fan_command(value)

	def _timer_callback(self):
		self._logger.info("ANDYTEST _timer_callback()")
		try:
			self._request_value(self.DATA_TYPE_DYNAMIC)
			self._validate_values()
			self._start_timer(delay=self._timer_interval)
		except:
			self._logger.exception("Exception in _timer_callback(): ")
			self._start_timer(delay=self._timer_interval)

	def _start_timer(self, delay=0):
		self._logger.info("ANDYTEST _start_timer() delay:%s, self._timer_boost_ts:%s", delay, self._timer_boost_ts)
		if self._timer:
			self._timer.cancel()
		if self._timer_boost_ts > 0 and time.time() - self._timer_boost_ts > self.MAX_TIMER_BOOST_DURATION:
			self._unboost_timer_interval()
		if not self._shutting_down:
			if delay <=0:
				self._timer_callback()
			else:
				self._timer = threading.Timer(delay, self._timer_callback)
				self._timer.daemon = True
				self._timer.start()
		else:
			self._logger.debug("Shutting down.")

	def _boost_timer_interval(self):
		self._logger.info("ANDYTEST _boost_timer_interval()")
		self._timer_boost_ts = time.time()
		self._timer_interval = self.BOOST_TIMER_INTERVAL
		# want the boost immediately, se reset current timer
		self._start_timer()

	def _unboost_timer_interval(self):
		self._logger.info("ANDYTEST _unboost_timer_interval()")
		self._timer_boost_ts = 0
		self._timer_interval = self.DEFAULT_TIMER_INTERVAL
		# must not call _start_timer()!!

	def _send_status_to_frontend(self):
		payload = dict(status=dict(
			fan_state=self._state,
			fan_rpm = self._rpm,
			fan_dust = self._dust,
			fan_connected = self._connected
		))
		_mrbeam_plugin_implementation._plugin_manager.send_plugin_message("mrbeam", payload)


	def do_debug_stuff(self):
		from random import randint
		val =randint(0, 255)
		# self._send_fan_command(self.FAN_COMMAND_ON.format(int(val)))
