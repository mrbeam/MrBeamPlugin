import socket
import sys
import threading
import time
import datetime
import collections
from distutils.version import LooseVersion

from octoprint.events import Events as OctoPrintEvents
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.lib.rwlock import RWLock
from flask.ext.babel import gettext
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.iobeam.laserhead_handler import laserheadHandler

# singleton
_instance = None


def ioBeamHandler(plugin):
	global _instance
	if _instance is None:
		_instance = IoBeamHandler(plugin)
	return _instance


class IoBeamEvents(object):
	"""
	These events are meant to be handled by OctoPrints event system
	"""
	CONNECT =            "iobeam.connect"
	DISCONNECT =         "iobeam.disconnect"
	ONEBUTTON_PRESSED =  "iobeam.onebutton.pressed"
	ONEBUTTON_DOWN =     "iobeam.onebutton.down"
	ONEBUTTON_RELEASED = "iobeam.onebutton.released"
	INTERLOCK_OPEN =     "iobeam.interlock.open"
	INTERLOCK_CLOSED =   "iobeam.interlock.closed"
	LID_OPENED =         "iobeam.lid.opened"
	LID_CLOSED =         "iobeam.lid.closed"


class IoBeamValueEvents(object):
	"""
	These Values / events are not intended to be handled byt OctoPrints event system
	but by IoBeamHandler's own event system
	"""
	LASER_TEMP =          "iobeam.laser.temp"
	DUST_VALUE =          "iobeam.dust.value"
	RPM_VALUE =           "iobeam.rpm.value"
	RPM_VALUE =           "iobeam.rpm.value"
	STATE_VALUE =         "iobeam.state.value"
	DYNAMIC_VALUE =       "iobeam.dynamic.value"
	CONNECTED_VALUE =     "iobeam.connected.value"
	FAN_ON_RESPONSE =     "iobeam.fan.on.response"
	FAN_OFF_RESPONSE =    "iobeam.fan.off.response"
	FAN_AUTO_RESPONSE =   "iobeam.fan.auto.response"
	FAN_FACTOR_RESPONSE = "iobeam.fan.factor.response"


class IoBeamHandler(object):

	# How to test and debug:
	# in config.yaml set
	#      [plugins mrbeam dev debug] to true (suppresses reconnect on socket timeout) and
	#      [plugins mrbeam dev sockets iobeam] to '/tmp/mrbeam_iobeam.sock' to open the socket without sudo pw
	# and then use  "/usr/bin/nc -U -l /tmp/mrbeam_iobeam.sock"
	#
	# How to get debug info:
	#       echo "info" |  nc -U -w1 /var/run/mrbeam_iobeam.sock


	SOCKET_FILE = "/var/run/mrbeam_iobeam.sock"
	MAX_ERRORS = 50

	IOBEAM_MIN_REQUIRED_VERSION =  '0.4.0'
	IOBEAM_JSON_PROTOCOL_VERSION = '0.7.0'

	CLIENT_ID = "MrBeamPlugin.v{vers_mrb}"

	PROCESSING_TIMES_LOG_LENGTH = 100
	PROCESSING_TIME_WARNING_THRESHOLD = 0.7

	MESSAGE_LENGTH_MAX = 4096
	MESSAGE_NEWLINE = "\n"
	MESSAGE_SEPARATOR = ":"
	MESSAGE_OK = "ok"
	MESSAGE_ERROR = "error"

	MESSAGE_DEVICE_ONEBUTTON =          "onebtn"
	MESSAGE_DEVICE_LID =   		        "lid"
	MESSAGE_DEVICE_INTERLOCK =          "intlk"
	MESSAGE_DEVICE_STEPRUN =            "steprun"
	MESSAGE_DEVICE_FAN =	            "fan"
	MESSAGE_DEVICE_LASER =	            "laser"
	MESSAGE_DEVICE_UNUSED =	            "unused"
	MESSAGE_DEVICE_IOBEAM =	            "iobeam"

	MESSAGE_ACTION_ONEBUTTON_PRESSED =  "pr"
	MESSAGE_ACTION_ONEBUTTON_DOWN =     "dn"
	MESSAGE_ACTION_ONEBUTTON_RELEASED = "rl"
	MESSAGE_ACTION_ONEBUTTON_UP =		"up"

	MESSAGE_ACTION_INTERLOCK_OPEN =     "op"
	MESSAGE_ACTION_INTERLOCK_CLOSED =   "cl"

	MESSAGE_ACTION_LID_OPENED =         "op"
	MESSAGE_ACTION_LID_CLOSED =         "cl"

	MESSAGE_IOBEAM_VERSION_0_2_3 =		"0.2.3"
	MESSAGE_IOBEAM_VERSION_0_2_4 =		"0.2.4"

	MESSAGE_ACTION_LASER_TEMP =         "temp"
	MESSAGE_ACTION_DUST_VALUE =         "dust"
	MESSAGE_ACTION_FAN_ON =             "on"
	MESSAGE_ACTION_FAN_OFF =            "off"
	MESSAGE_ACTION_FAN_AUTO =           "auto"
	MESSAGE_ACTION_FAN_FACTOR =         "factor"
	MESSAGE_ACTION_FAN_VERSION =        "version"
	MESSAGE_ACTION_FAN_RPM =            "rpm"
	MESSAGE_ACTION_FAN_PWM_MIN =        "pwm_min"
	MESSAGE_ACTION_FAN_TPR =            "tpr"
	MESSAGE_ACTION_FAN_STATE =          "state"
	MESSAGE_ACTION_FAN_DYNAMIC =        "dynamic"
	MESSAGE_ACTION_FAN_CONNECTED =      "connected"
	MESSAGE_ACTION_FAN_SERIAL =         "serial"
	MESSAGE_ACTION_FAN_EXHAUST =        "exhaust"
	MESSAGE_ACTION_FAN_LINK_QUALITY =   "link_quality"

	def __init__(self, plugin):
		self._plugin = plugin
		self._event_bus = plugin._event_bus
		self._socket_file = plugin._settings.get(["dev", "sockets", "iobeam"])
		self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam")

		self._shutdown_signaled = False
		self._isConnected = False
		self._my_socket = None
		self._errors = 0
		self._callbacks = dict()
		self._callbacks_lock = RWLock()

		self.dev_mode = plugin._settings.get_boolean(['dev', 'iobeam_disable_warnings'])

		self.iobeam_version = None

		self._connectionException = None
		self._interlocks = dict()

		self._subscribe()
		self._initWorker(self._socket_file)

		self.processing_times_log = collections.deque([], self.PROCESSING_TIMES_LOG_LENGTH)

		self._settings = plugin._settings
		self.reported_hardware_malfunctions = []

		self._laserheadHandler = laserheadHandler(plugin)

	def isRunning(self):
		return self._worker.is_alive()

	def isConnected(self):
		return self._isConnected

	def shutdown(self, *args):
		self._logger.debug("shutdown() args: %s", args)
		global _instance
		_instance = None
		self._shutdown_signaled = True

	def shutdown_fan(self):
		self.send_fan_command(self.MESSAGE_ACTION_FAN_OFF)

	def is_interlock_closed(self):
		return len(self._interlocks.keys()) == 0

	def open_interlocks(self):
		return self._interlocks.keys()

	def send_temperature_request(self):
		'''
		Request a single temperature value from iobeam.
		:return: True if the command was sent sucessfully.
		'''
		return self._send_command("{}:{}".format(self.MESSAGE_DEVICE_LASER, self.MESSAGE_ACTION_LASER_TEMP))

	def send_fan_command(self, command):
		'''
		Send the specified command as fan:<command>
		:param command: One of the three values (ON:<0-100>/OFF/AUTO)
		:return: True if the command was sent sucessfull (does not mean it was sucessfully executed)
		'''
		ok = self._send_command("{}:{}".format(self.MESSAGE_DEVICE_FAN, command))
		# self._logger.info("send_fan_command(): ok: %s, command: %s", ok, command)
		return ok

	def _send_command(self, command):
		'''
		Sends a command to iobeam
		:param command: Must not be None. May or may not end with a new line.
		:return: Boolean success
		'''
		command = self._normalize_command(command)
		if command is None:
			raise ValueError("Command must not be None in send_command().")
		if self._shutdown_signaled:
			return False
		if not self._isConnected:
			if not self.dev_mode:
				self._logger.warn("send_command() Can't send command since socket is not connected (yet?). Command: %s", command)
			return False
		if self._my_socket is None:
			self._logger.error("send_command() Can't send command while there's no connection on socket but _isConnected()=True!  Command: %s", command)
			return False

		command_with_nl = "{}\n".format(command)
		try:
			self._my_socket.sendall(command_with_nl)
		except Exception as e:
			self._errors += 1
			self._logger.error("Exception while sending command '%s' to socket: %s", command, e)
			return False
		return True

	def is_iobeam_version_ok(self):
		if self.iobeam_version is None:
			return False, 0
		vers_obj = None
		try:
			vers_obj = LooseVersion(self.iobeam_version)
		except ValueError as e:
			self._logger.error("iobeam version invalid: '{}'. ValueError from LooseVersion: {}".format(self.iobeam_version, e))
			return False, 0
		if vers_obj < LooseVersion(self.IOBEAM_MIN_REQUIRED_VERSION):
			return False, -1
		elif vers_obj >= LooseVersion(self.IOBEAM_JSON_PROTOCOL_VERSION):
			return False, 1
		else:
			return True, 0


	# return LooseVersion(self.iobeam_version) >= LooseVersion(self.IOBEAM_MIN_REQUIRED_VERSION) and LooseVersion(self.iobeam_version) < LooseVersion(self.IOBEAM_JSON_PROTOCOL_VERSION)

	def subscribe(self, event, callback):
		'''
		Subscibe to an event
		:param event:
		:param callback:
		'''
		try:
			self._callbacks_lock.writer_acquire()
			if event in self._callbacks:
				self._callbacks[event].append(callback)
			else:
				self._callbacks[event] = [callback]
		except:
			self._logger.exception("Exception while subscribing to event '{}': ".format(event))
		finally:
			self._callbacks_lock.writer_release()

	def _call_callback(self, _trigger_event, message, kwargs):
		try:
			self._callbacks_lock.reader_acquire()
			if _trigger_event in self._callbacks:
				_callback_array = self._callbacks[_trigger_event]
				kwargs['event'] = _trigger_event
				kwargs['message'] = message

				# If handling of these messages blockes iobeam_handling, we might need a threadpool or so.
				# One thread for handling this is almost the same bottleneck as current solution,
				# so I think we would need a thread pool here... But maybe this would be just over engineering.
				self.__execute_callback_called_by_new_thread(_trigger_event, False, _callback_array, kwargs)

				# thread_params = dict(target = self.__execute_callback_called_by_new_thread,
				#                      name = "iobeamCB_{}".format(_trigger_event),
				#                      args = (_trigger_event, _callback_array),
				#                      kwargs = kwargs)
				# my_thread = threading.Thread(**thread_params)
				# my_thread.daemon = True
				# my_thread.start()
		except:
			self._logger.exception("Exception in _call_callback() _trigger_event: %s, message: %s, kwargs: %s", _trigger_event, message, kwargs)
		finally:
			self._callbacks_lock.reader_release()

	def __execute_callback_called_by_new_thread(self, _trigger_event, acquire_lock, _callback_array, kwargs):
		try:
			if acquire_lock:
				# It's a trrible idea to acquire this lock two times in a row on the same thread.
				# It happened that there was a write request in between -> dead lock like in a text book ;-)
				self._callbacks_lock.reader_acquire()
			for my_cb in _callback_array:
				try:
					my_cb(kwargs)
				except Exception as e:
					self._logger.exception("Exception in a callback for event: %s : ", _trigger_event)
		except:
			self._logger.exception("Exception in __execute_callback_called_by_new_thread() for event: %s : ", _trigger_event)
		finally:
			if acquire_lock:
				self._callbacks_lock.reader_release()

	def _subscribe(self):
		self._event_bus.subscribe(OctoPrintEvents.SHUTDOWN, self.shutdown)

	def _initWorker(self, socket_file=None):
		self._logger.debug("initializing worker thread")

		# this is needed for unit tests
		if socket_file is not None:
			self.SOCKET_FILE = socket_file

		self._worker = threading.Thread(target=self._work, name="iobeamHandler")
		self._worker.daemon = True
		self._worker.start()

	def _work(self):
		threading.current_thread().name = self.__class__.__name__
		self._logger.debug("Worker thread starting, connecting to socket: %s %s", self.SOCKET_FILE, (" !!! iobeam_disable_warnings: True !!!" if self.dev_mode else ""))
		if self.dev_mode:
			self._logger.warn("iobeam handler: !!! iobeam_disable_warnings: True !!!")

		while not self._shutdown_signaled:
			self._my_socket = None
			self._isConnected = False
			try:
				temp_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
				temp_socket.settimeout(3)
				# self._logger.debug("Connecting to socket...")
				temp_socket.connect(self.SOCKET_FILE)
				self._my_socket = temp_socket
			except socket.error as e:
				self._isConnected = False
				if self.dev_mode:
					if not self._connectionException == str(e):
						self._logger.error("IoBeamHandler not able to connect to socket %s, reason: %s. I'll keept trying but I won't log further failures.", self.SOCKET_FILE, e)
						self._connectionException = str(e)
				else:
					self._logger.error("IoBeamHandler not able to connect to socket %s, reason: %s. ", self.SOCKET_FILE, e)

				time.sleep(1)
				continue

			self._isConnected = True
			self._errors = 0
			self._connectionException = None

			id =self._send_identification()
			self._logger.info("iobeam connection established. Identified ourselves as '%s'", id)
			self._fireEvent(IoBeamEvents.CONNECT)

			while not self._shutdown_signaled:
				try:

					try:
						data = self._my_socket.recv(self.MESSAGE_LENGTH_MAX)
					except Exception as e:
						if self.dev_mode and e.message == "timed out":
							# self._logger.warn("Connection stale but MRBEAM_DEBUG enabled. Continuing....")
							continue
						else:
							self._logger.warn("Exception while sockect.recv(): %s - Resetting connection...", e)
							break

					if not data:
						self._logger.warn("Connection ended from other side. Closing connection...")
						break

					# here we see what's in the data...
					my_errors, _ = self._handleMessages(data)
					if my_errors > 0:
						self._errors += my_errors
						if self._errors >= self.MAX_ERRORS:
							self._logger.warn("Resetting connection... error_count=%s, Resetting connection...", self._errors)
							break
						else:
							self._logger.warn("Received invalid message, error_count=%s", self._errors)

				except:
					self._logger.exception("Exception in socket loop. Not sure what to do, resetting connection...")

			if self._my_socket is not None:
				self._logger.debug("Closing socket...")
				self._my_socket.close()
				self._my_socket = None

			self._isConnected = False
			self._fireEvent(IoBeamEvents.DISCONNECT) # on shutdown this won't be broadcasted

			if not self._shutdown_signaled:
				self._logger.debug("Sleeping for a sec before reconnecting...")
				time.sleep(1)

		self._logger.debug("Worker thread stopped.")

	def _handleMessages(self, data):
		"""
		handles incoming data from the socket.
		:param data:
		:return: int: number of invalid messages 0 means all messages were handled correctly
		"""
		if not data: return 1

		error_count = 0
		message_count = 0
		message_list = data.split(self.MESSAGE_NEWLINE)
		for message in message_list:
			processing_start = time.time()
			# remove pings
			while message.startswith('.'):
				message = message[1:]
			if not message: continue

			err = -1
			message_count =+ 1
			# self._logger.debug("_handleMessages() handling message: %s", message)

			tokens = message.split(self.MESSAGE_SEPARATOR)
			# would allow to escape MESSAGE_SEPARATOR in case we want to use JSON some day
			# tokens = list(map(lambda x: x.replace('\\{}'.format(self.MESSAGE_SEPARATOR), self.MESSAGE_SEPARATOR),
			#                   re.split(r'(?<!\\){}'.format(self.MESSAGE_SEPARATOR), message)))
			if len(tokens) <=1:
				err = self._handle_invalid_message(message)
			else:
				device = tokens.pop(0)
				if device == self.MESSAGE_DEVICE_ONEBUTTON:
					err = self._handle_onebutton_message(message, tokens)
				elif device == self.MESSAGE_DEVICE_LID:
					err = self._handle_lid_message(message, tokens)
				elif device == self.MESSAGE_DEVICE_INTERLOCK:
					err = self._handle_interlock_message(message, tokens)
				elif device == self.MESSAGE_DEVICE_STEPRUN:
					err = self._handle_steprun_message(message, tokens)
				elif device == self.MESSAGE_DEVICE_FAN:
					err = self._handle_fan_message(message, tokens)
				elif device == self.MESSAGE_DEVICE_LASER:
					err = self._handle_laser_message(message, tokens)
				elif device == self.MESSAGE_DEVICE_IOBEAM:
					err = self._handle_iobeam_message(message, tokens)
				elif device == self.MESSAGE_DEVICE_UNUSED:
					pass
				elif device == self.MESSAGE_ERROR:
					err = self._handle_error_message(message, tokens)
				else:
					err = self._handle_unknown_device_message(message, tokens)

			if err >= 0:
				error_count += err

			processing_time = time.time() - processing_start
			self._handle_precessing_time(processing_time, message, err)

		return error_count, message_count

	def _handle_invalid_message(self, message):
		self._logger.warn("Received invalid message: '%s'", message)
		return 1

	def _handle_onebutton_message(self, message, token):
		action = token[0] if len(token)>0 else None
		payload = self._as_number(token[1]) if len(token)>1 else None
		self._logger.debug("_handle_onebutton_message() message: %s, action: %s, payload: %s", message, action, payload)

		if action == self.MESSAGE_ACTION_ONEBUTTON_PRESSED:
			self._fireEvent(IoBeamEvents.ONEBUTTON_PRESSED)
		elif action == self.MESSAGE_ACTION_ONEBUTTON_DOWN and payload is not None:
			self._fireEvent(IoBeamEvents.ONEBUTTON_DOWN, payload)
		elif action == self.MESSAGE_ACTION_ONEBUTTON_RELEASED and payload is not None:
			self._fireEvent(IoBeamEvents.ONEBUTTON_RELEASED, payload)
		elif action == self.MESSAGE_ACTION_ONEBUTTON_UP:
			return 0
		elif action == self.MESSAGE_ERROR:
			self._logger.warn("Received onebtn error: '%s'", message)
			return 1
		else:
			return self._handle_invalid_message(message)
		return 0

	def _handle_interlock_message(self, message, tokens):
		lock_id = tokens[0] if len(tokens) > 0 else None
		lock_state = tokens[1] if len(tokens) > 1 else None
		before_state = self.open_interlocks()
		self._logger.debug("_handle_interlock_message() message: %s, lock_id: %s, lock_state: %s, before_state: %s", message, lock_id, lock_state, before_state)

		if lock_id is not None and lock_state == self.MESSAGE_ACTION_INTERLOCK_OPEN:
			self._interlocks[lock_id] = True
		elif lock_id is not None and lock_state == self.MESSAGE_ACTION_INTERLOCK_CLOSED:
			self._interlocks.pop(lock_id, None)
		elif self.MESSAGE_ERROR in message:
			self._logger.error("iobeam received InterLock error: {}".format(message))
			return 1
		else:
			return self._handle_invalid_message(message)

		now_state = self.open_interlocks()
		if now_state != before_state:
			if self.is_interlock_closed():
				self._fireEvent(IoBeamEvents.INTERLOCK_CLOSED)
			else:
				self._fireEvent(IoBeamEvents.INTERLOCK_OPEN, now_state)

		return 0

	def _handle_lid_message(self, message, token):
		action = token[0] if len(token) > 0 else None
		payload = self._as_number(token[1]) if len(token) > 1 else None
		self._logger.debug("_handle_lid_message() message: %s, action: %s, payload: %s", message, action, payload)

		if action == self.MESSAGE_ACTION_LID_OPENED:
			self._fireEvent(IoBeamEvents.LID_OPENED)
		elif action == self.MESSAGE_ACTION_LID_CLOSED:
			self._fireEvent(IoBeamEvents.LID_CLOSED)
		else:
			return self._handle_invalid_message(message)

		return 0

	def _handle_steprun_message(self, message, tokens):
		return 0

	def _handle_fan_message(self, message, token):
		action = token[0] if len(token) > 0 else None
		value = token[1] if len(token) > 1 else None

		if action == self.MESSAGE_ACTION_FAN_DYNAMIC:
			if action.startswith(self.MESSAGE_ERROR):
				return 1
			elif len(token) >= 5:
				vals = dict(
					state =     self._as_number(token[1]),
					rpm =       self._as_number(token[2]),
					dust =      self._as_number(token[3]),
					connected = self._get_connected_val(token[4]))
				# if token[4] == 'error':
				# 	self._logger.warn("Received fan connection error: %s", message)
				self._call_callback(IoBeamValueEvents.DYNAMIC_VALUE, message, vals)
				self._call_callback(IoBeamValueEvents.STATE_VALUE, message, dict(val=vals['state']))
				self._call_callback(IoBeamValueEvents.RPM_VALUE, message, dict(val=vals['rpm']))
				self._call_callback(IoBeamValueEvents.DUST_VALUE, message, dict(val=vals['dust']))
				self._call_callback(IoBeamValueEvents.CONNECTED_VALUE, message, dict(val=vals['connected']))
				return 0
		elif action == self.MESSAGE_ACTION_DUST_VALUE:
			dust_val = self._as_number(value)
			if dust_val is not None:
				self._call_callback(IoBeamValueEvents.DUST_VALUE, message, dict(val=dust_val))
			return 0
		elif action == self.MESSAGE_ACTION_FAN_RPM:
			rpm_val = self._as_number(value)
			if rpm_val is not None:
				self._call_callback(IoBeamValueEvents.RPM_VALUE, message, dict(val=rpm_val))
			return 0
		elif action == self.MESSAGE_ACTION_FAN_STATE:
			state = self._as_number(value)
			if state is not None:
				self._call_callback(IoBeamValueEvents.STATE_VALUE, message, dict(val=state))
			return 0
		elif action == self.MESSAGE_ACTION_FAN_CONNECTED:
			self._call_callback(IoBeamValueEvents.CONNECTED_VALUE, message, dict(val=self._get_connected_val(value)))
			if value == 'error':
				self._logger.warn("Received fan connection error: %s", message)
			return 0
		elif action == self.MESSAGE_ACTION_FAN_VERSION:
			self._logger.info("Received fan version %s: '%s'", value, message)
			return 0
		elif action == self.MESSAGE_ACTION_FAN_PWM_MIN:
			return 0
		elif action == self.MESSAGE_ACTION_FAN_TPR:
			return 0
		elif action == self.MESSAGE_ACTION_FAN_SERIAL:
			self._logger.info("Received fan serial %s: '%s'", value, message)
			return 0
		elif action == self.MESSAGE_ACTION_FAN_EXHAUST and len(token) > 2:
			self._logger.info("Received exhaust %s %s: '%s'", value, token[2], message)
			return 0
		elif action == self.MESSAGE_ACTION_FAN_LINK_QUALITY and len(token) > 2:
			self._logger.info("Received link quality %s %s: '%s'", value, token[2], message)
			return 0

		# check if OK otherwise it's an error
		success = value == self.MESSAGE_OK
		payload = dict(success=success)
		if not success:
			payload['error'] = token[2] if len(token) > 2 else None

		if action == self.MESSAGE_ACTION_FAN_ON:
			self._call_callback(IoBeamValueEvents.FAN_ON_RESPONSE, message, payload)
		elif action == self.MESSAGE_ACTION_FAN_OFF:
			self._call_callback(IoBeamValueEvents.FAN_OFF_RESPONSE, message, payload)
		elif action == self.MESSAGE_ACTION_FAN_AUTO:
			self._call_callback(IoBeamValueEvents.FAN_AUTO_RESPONSE, message, payload)
		elif action == self.MESSAGE_ACTION_FAN_FACTOR:
			self._call_callback(IoBeamValueEvents.FAN_FACTOR_RESPONSE, message, payload)
		else:
			self._logger.info("Received fan data: '%s'", message)

		return 0

	def _handle_laser_message(self, message, token):
		action = token[0] if len(token) > 0 else None
		if action == self.MESSAGE_ACTION_LASER_TEMP:
			temp = self._as_number(token[1]) if len(token) > 1 else None
			if temp is not None:
				self._call_callback(IoBeamValueEvents.LASER_TEMP, message, dict(temp=temp))
		elif action == "head" and token[1] == 'data':
			# iobeam sends the whole laserhead data print
			try:
				data = ":".join(token[2:]).replace("|||", "\n| ")
				if data.startswith('Laserhead'):
					data = 'ok\n| {}'.format(data)
				self._logger.info("laserhead data: %s", data)
			except:
				self._logger.exception("laserhead: exception while handling head:data: ")
		elif action == "serial":
			sn = token[1]
			if sn not in ('error'):
				self._laserheadHandler.set_current_used_lh_serial(sn)
				self._logger.info("laserhead serial: %s", sn)
			else:
				self._logger.info("laserhead: '%s'", message)
		elif action == "power" and token[1] == '65':
			p65 = None
			try:
				p65 = int(token[2])
			except:
				self._logger.info("laserhead: '%s'", message)
				self._logger.warn("Can't read power 65 value as int: '%s'", token[2])

			if p65 is not None:
				self._laserheadHandler.set_power_measurement_value('p_65', p65)
				self._logger.info("laserhead p_65: %s", p65)
		elif action == "power" and token[1] == '75':
			p75 = None
			try:
				p75 = int(token[2])
			except:
				self._logger.info("laserhead: '%s'", message)
				self._logger.warn("Can't read power 75 value as int: '%s'", token[2])

			if p75 is not None:
				self._laserheadHandler.set_power_measurement_value('p_75', p75)
				self._logger.info("laserhead p_75: %s", p75)
		elif action == "power" and token[1] == '85':
			p85 = None
			try:
				p85 = int(token[2])
			except:
				self._logger.info("laserhead: '%s'", message)
				self._logger.warn("Can't read power 85 value as int: '%s'", token[2])

			if p85 is not None:
				self._laserheadHandler.set_power_measurement_value('p_85', p85)
				self._logger.info("laserhead p_85: %s", p85)
		else:
			self._logger.info("laserhead: '%s'", message)

		return 0

	def _handle_iobeam_message(self, message, token):
		action = token[0] if len(token) > 0 else None
		if action == 'version':
			version = token[1] if len(token) > 1 else None
			if version:
				self.iobeam_version = version
				ok, state = self.is_iobeam_version_ok()
				if ok:
					self._logger.info("Received iobeam version: %s - version OK", self.iobeam_version)
				else:
					if state <= 0:
						self._logger.error("Received iobeam version: %s - version OUTDATED. IOBEAM_MIN_REQUIRED_VERSION: %s", self.iobeam_version, self.IOBEAM_MIN_REQUIRED_VERSION)
						self._plugin.notify_frontend(title=gettext("Software Update required"),
													 text=gettext("Module 'iobeam' is outdated. Please run software "
																  "update from 'Settings' > 'Software Update' before "
																  "you start a laser job."),
													 type="error", sticky=True,
													 replay_when_new_client_connects=True)
					else:
						self._logger.error("Received iobeam version: %s - version INCOMPATIBLE. iobeam is already using new JSON protocol!", self.iobeam_version)
						self._plugin.notify_frontend(title=gettext("Software Update required"),
													 text=gettext("Module 'MrBeam Plugin' is outdated; iobeam version "
																  "is newer than expected. Please run software update "
																  "from 'Settings' > 'Software Update' before you start "
																  "a laser job."),
													 type="error", sticky=True,
													 replay_when_new_client_connects=True)
				return 0
			else:
				self._logger.warn("_handle_iobeam_message(): Received iobeam:version message without version number. Counting as error. Message: %s", message)
				return 1
		elif action == 'init':
			# introduced with iobeam 0.4.2
			# in future versions we could make this requried and only unlock laser functionality once this was ok
			init = token[1] if len(token) > 1 else None
			malfunction = token[2] if len(token) > 2 else None
			if init and init.startswith('ok'):
				self._logger.info("iobeam init ok: '%s'", message)
			else:
				self._logger.info("iobeam init error: '%s' - requesting iobeam_debug...", message)
				self._send_command('debug')
				self._fireEvent(MrBeamEvents.HARDWARE_MALFUNCTION, dict(iobeam_messsage=message))
				if malfunction == 'bottom_open':
					self.send_bottom_open_frontend_notification(malfunction)
				else:
					self.send_hardware_malfunction_frontend_notification(malfunction, message)
			self._plugin._analytics_handler.add_iobeam_message_log(self.iobeam_version, message)
		elif action == 'runtime': # introduced in iobeam 0.6.2
			init = token[1] if len(token) > 1 else None
			malfunction = token[2] if len(token) > 2 else None
			if init and init.startswith('ok'):
				self._logger.info("iobeam runtime ok: '%s'", message)
			else:
				self._logger.info("iobeam runtime error: '%s'", message)
				self._fireEvent(MrBeamEvents.HARDWARE_MALFUNCTION, dict(iobeam_messsage=message))
				if malfunction == 'bottom_open':
					self.send_bottom_open_frontend_notification(malfunction)
				else:
					self.send_hardware_malfunction_frontend_notification(malfunction, message)
			self._plugin._analytics_handler.add_iobeam_message_log(self.iobeam_version, message)
		elif action == 'i2c':
			self._logger.info("iobeam i2c devices: '%s'", message)
			self._plugin._analytics_handler.add_iobeam_message_log(self.iobeam_version, message)
		elif action == 'debug':
			self._logger.info("iobeam debug message: '%s'", message)
		else:
			self._logger.info("iobeam message: '%s'", message)
		return 0

	def _handle_error_message(self, message, token):
		action = token[0] if len(token) > 0 else None
		if action == "reconnect":
			raise Exception("ioBeam requested to reconnect. Now doing so...")
		return 1

	def _handle_unknown_device_message(self, message, token):
		self._logger.warn("Received message about unknown device: %s", message)
		return 0

	def _handle_precessing_time(self, processing_time, message, err, log_stats=False):
		self.processing_times_log.append(dict(ts=time.time(),
		                                      processing_time = processing_time,
		                                      message = message,
		                                      error_count = err))

		if processing_time > self.PROCESSING_TIME_WARNING_THRESHOLD:
			self._logger.warn("Message handling time took %ss. (Errors: %s, message: '%s')", processing_time, err, message)
		if log_stats or processing_time > self.PROCESSING_TIME_WARNING_THRESHOLD:
			self.log_debug_processing_stats()

	def send_hardware_malfunction_frontend_notification(self, malfunction, message):
		if malfunction not in self.reported_hardware_malfunctions:
			self.reported_hardware_malfunctions.append(malfunction)
			text = '<br/>' + \
			       gettext(
				       "A possible hardware malfunction has been detected on this device. Please contact our support team immediately at:") + \
			       '<br/><a href="https://mr-beam.org/ticket" target="_blank">mr-beam.org/ticket</a><br/><br/>' \
			       '<strong>' + gettext("Error:") + '</strong><br/>{}'.format(message.replace(':', ': ')) # add whitespaces so that longer messages break in frontend
			self._plugin.notify_frontend(title=gettext("Hardware malfunction"),
			                             text=text,
			                             type="error", sticky=True,
			                             replay_when_new_client_connects=True)

	def send_bottom_open_frontend_notification(self, malfunction):
		if malfunction not in self.reported_hardware_malfunctions:
			self.reported_hardware_malfunctions.append(malfunction)
			text = '<br/>' + \
			       gettext("The bottom plate is not closed correctly. "
			               "Please make sure that the bottom is correctly mounted as described in the Mr Beam II user manual.")
			self._plugin.notify_frontend(title=gettext("Bottom Plate Error"),
			                             text=text,
			                             type="error", sticky=True,
			                             replay_when_new_client_connects=True)

	def log_debug_processing_stats(self):
		"""
		Not exactly sure what my idea was with this...
		# TODO: find a way to trigger this manually for debugging and general curiosity.
		:return:
		"""
		min = sys.maxint
		max = 0
		sum = 0
		count = 0
		earliest = time.time()
		for entry in self.processing_times_log:
			if entry['processing_time'] < min:
				min = entry['processing_time']
			if entry['processing_time'] > max:
				max = entry['processing_time']
			if entry['ts'] < earliest: earliest = entry['ts']
			sum += entry['processing_time']
			count += 1
		if count <= 0:
			self._logger.error("_handle_precessing_time() stats: message count is <= 0, something seems be wrong.")
		else:
			avg = sum/count
			time_formatted = datetime.datetime.fromtimestamp(earliest).strftime('%Y-%m-%d %H:%M:%S')
			self._logger.info("Message handling stats: %s message since %s; max: %ss, avg: %ss, min: %ss", count, time_formatted, max, avg, min)

	def _send_identification(self):
		client_name = self.CLIENT_ID.format(vers_mrb=self._plugin._plugin_version)
		cmd = "{}:client:{}".format(self.MESSAGE_DEVICE_IOBEAM, client_name)
		sent = self._send_command(cmd)
		return client_name if sent else False

	def _fireEvent(self, event, payload=None):
		self._event_bus.fire(event, payload)

	def _normalize_command(self, cmd):
		if cmd is None:
			return None
		return cmd.replace("\n", '')

	def _as_number(self, str):
		if str is None:
			return None
		if str.lower() == "nan":
			return None
		try:
			return float(str)
		except:
			return None

	def _get_connected_val(self, value):
		connected = None
		if value is None:
			return None

		value = value.lower()
		if value in ('none', 'unknown'):
			connected = None
		elif value == 'false' or value == 'error':
			connected = False
		elif value == 'true':
			connected = True
		return connected


