import socket
import sys
import threading
import time
import datetime
import collections

from octoprint.events import Events as OctoPrintEvents
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.lib.rwlock import RWLock

# singleton
_instance = None

def ioBeamHandler(eventBusOct, socket_file=None):
	global _instance
	if _instance is None:
		_instance = IoBeamHandler(eventBusOct, socket_file)
	return _instance


class IoBeamEvents(object):
	'''
	These events are meant to be handled by OctoPrints event system
	'''
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
	'''
	These Values / events are not intended to be handled byt OctoPrints event system
	but by IoBeamHandler's own event system
	'''
	LASER_TEMP =          "iobeam.laser.temp"
	DUST_VALUE =          "iobeam.dust.value"
	FAN_ON_RESPONSE =     "iobeam.fan.on.response"
	FAN_OFF_RESPONSE =    "iobeam.fan.off.response"
	FAN_AUTO_RESPONSE =   "iobeam.fan.auto.response"
	FAN_FACTOR_RESPONSE = "iobeam.fan.factor.response"

class IoBeamHandler(object):

	# > iobeam:<data>
	# > iobeam:version:<version_string>
	# > iobeam:debug:<data>
	# < iobeam:<data>
	# < iobeam:client:<client_id_string>
	# < info
	# < debug

	# > onebtn:up
	# > onebtn:pr
	# > onebtn:dn:< time >
	# > onebtn:rl:< time >
	# > onebtn:error	?
	# > lid:op
	# > lid:cl
	# > intlk:0:op
	# > intlk:0:cl
	# > intlk:1:op
	# > intlk:1:cl
	# > intlk:2:op
	# > intlk:2:cl
	# > intlk:3:op
	# > intlk:3:cl
	# > steprun:on
	# > steprun:off
	# > steprun:error

	# < fan:on:< value 0-100 >
	# > fan:on:ok
	# > fan:on:error
	# < fan:off
	# > fan:off:ok
	# > fan:off:error
	# < fan:auto
	# > fan:auto:ok
	# > fan:auto:error
	# < fan:state
	# > fan:state:<value 0-100 | auto> #TODO refine value
	# < fan:rpm
	# > fan:rpm:<rpm value>
	# > fan:rpm:error
	# < fan:factor:<factor 0.00-2.55, default: 0.35>
	# > fan:factor:<factor 0.00-2.55>
	# > fan:factor:ok
	# > fan:factor:error
	# < fan:tpr:<tics per roto 0-255, default: 2>
	# > fan:tpr:<tics per roto 0-255>
	# > fan:tpr:ok
	# > fan:tpr:error
	# < fan:pwm_min:<pwm_min 0-255, default: 55>
	# > fan:pwm_min:<pwm_min 0-255>
	# > fan:pwm_min:ok
	# > fan:pwm_min:error
	# < fan:version
	# > fan:version:<version-string>
	# > fan:version:error
	# < fan:dust
	# > fan:dust:<dust value 0.3>
	# > fan:dust:error

	# < laser:temp
	# > laser:temp:< temperatur >
	# > laser:temp:error:<error type or message>

	# How to test and debug:
	# in config.yaml set
	#      [plugins mrbeam dev debug] to true (suppresses reconnect on socket timeout) and
	#      [plugins mrbeam dev sockets iobeam] to '/tmp/mrbeam_iobeam.sock' to open the socket without sudo pw
	# and then use  "/usr/bin/nc -U -l /tmp/mrbeam_iobeam.sock"
	#
	# How to get debug info:
	#       echo "info" |  nc -U -w1 /var/run/mrbeam_iobeam.sock


	SOCKET_FILE = "/var/run/mrbeam_iobeam.sock"
	MAX_ERRORS = 10

	CLIENT_ID = "MrBeamPlugin.v{vers_mrb}/OctoPrint.v{vers_op}"

	PROCESSING_TIMES_LOG_LENGTH = 100
	PROCESSING_TIME_WARNING_THRESHOLD = 0.1

	MESSAGE_LENGTH_MAX = 1024
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


	def __init__(self, event_bus, socket_file=None):
		self._event_bus = event_bus
		self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam")

		self._shutdown_signaled = False
		self._isConnected = False
		self._my_socket = None
		self._errors = 0
		self._callbacks = dict()
		self._callbacks_lock = RWLock()

		self.dev_mode = _mrbeam_plugin_implementation._settings.get_boolean(['dev', 'iobeam_disable_warnings'])

		self.iobeam_version = None

		self._connectionException = None
		self._interlocks = dict()

		self._subscribe()
		self._initWorker(socket_file)

		self.processing_times_log = collections.deque([], self.PROCESSING_TIMES_LOG_LENGTH)

	def isRunning(self):
		return self._worker.is_alive()

	def isConnected(self):
		return self._isConnected

	def shutdown(self, *args):
		self._logger.debug("shutdown() args: %s", args)
		global _instance
		_instance = None
		self._shutdown_signaled = True

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
		# self._logger.info("ANDYTEST send_fan_command(): ok: %s, command: %s", ok, command)
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
			self._logger.exception("Exception while subscribing to event '%s': ", event)
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


	# handles incoming data from the socket.
	# @return int: number of invalid messages 0 means all messages were handled correctly
	def _handleMessages(self, data):
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
			raise Exception("iobeam received OneButton error: %s", message)
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
			raise Exception("iobeam received InterLock error: %s", message)
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

		if action == self.MESSAGE_ACTION_DUST_VALUE:
			dust_val = self._as_number(value)
			if dust_val is not None:
				self._call_callback(IoBeamValueEvents.DUST_VALUE, message, dict(val=dust_val))
			return 0
		elif action == self.MESSAGE_ACTION_FAN_RPM:
			return 0
		elif action == self.MESSAGE_ACTION_FAN_VERSION:
			return 0
		elif action == self.MESSAGE_ACTION_FAN_PWM_MIN:
			return 0
		elif action == self.MESSAGE_ACTION_FAN_TPR:
			return 0
		elif action == self.MESSAGE_ACTION_FAN_STATE:
			return 0

		# check if OK otherwise it's an error
		success = value == self.MESSAGE_OK
		payload = dict(success=success)
		if not success: payload['error'] = token[2] if len(token) > 2 else None

		if action == self.MESSAGE_ACTION_FAN_ON:
			self._call_callback(IoBeamValueEvents.FAN_ON_RESPONSE, message, payload)
		elif action == self.MESSAGE_ACTION_FAN_OFF:
			self._call_callback(IoBeamValueEvents.FAN_OFF_RESPONSE, message, payload)
		elif action == self.MESSAGE_ACTION_FAN_AUTO:
			self._call_callback(IoBeamValueEvents.FAN_AUTO_RESPONSE, message, payload)
		elif action == self.MESSAGE_ACTION_FAN_FACTOR:
			self._call_callback(IoBeamValueEvents.FAN_FACTOR_RESPONSE, message, payload)
		else:
			return self._handle_invalid_message(message)

		return 0

	def _handle_laser_message(self, message, token):
		action = token[0] if len(token) > 0 else None
		temp = self._as_number(token[1]) if len(token) > 1 else None

		if action == self.MESSAGE_ACTION_LASER_TEMP and temp is not None:
			self._call_callback(IoBeamValueEvents.LASER_TEMP, message, dict(temp=temp))
		else:
			return self._handle_invalid_message(message)

		return 0

	def _handle_iobeam_message(self, message, token):
		action = token[0] if len(token) > 0 else None
		if action == 'version':
			version = token[1] if len(token) > 1 else None
			if version:
				self.iobeam_version = version
				self._logger.info("Received iobeam version: %s", self.iobeam_version)
				return 0
			else:
				self._logger.warn("_handle_iobeam_message(): Received iobeam:version message without version number. Counting as error. Message: %s", message)
				return 1
		elif action == 'debug':
			self.log_debug_processing_stats()
		else:
			self._logger.debug("_handle_iobeam_message(): Received unknown message for device 'iobeam'. NOT counting as error. Message: %s", message)
			return 0

	def _handle_error_message(self, message, token):
		action = token[0] if len(token) > 0 else None
		if action == "reconnect":
			raise Exception("ioBeam requested to reconnect. Now doing so...")
		return 1

	def _handle_unknown_device_message(self, message, token):
		self._logger.warn("Received mesage about unknown device: %s", message)
		return 0

	def _handle_precessing_time(self, processing_time, message, err, log_stats=False):
		self.processing_times_log.append(dict(ts=time.time(),
		                                      processing_time = processing_time,
		                                      message = message,
		                                      error_count = err))

		if processing_time > self.PROCESSING_TIME_WARNING_THRESHOLD:
			# TODO: write an error to our analytics module
			self._logger.warn("Message handling time took %ss. (Errors: %s, message: '%s')", processing_time, err, message)
		if log_stats or processing_time > self.PROCESSING_TIME_WARNING_THRESHOLD:
			self.log_debug_processing_stats()

	def log_debug_processing_stats(self):
		# TODO: find a way to trigger this manually for debugging and general curiosity.
			min = sys.maxint
			max = 0
			sum = 0
			count = 0
			earliest = time.time()
			for entry in self.processing_times_log:
				if entry['processing_time'] < min: min = entry['processing_time']
				if entry['processing_time'] > max: max = entry['processing_time']
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
		client_name = self.CLIENT_ID.format(vers_mrb=_mrbeam_plugin_implementation._plugin_version, vers_op="?")
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
		if str is None: return None
		if str.lower() == "nan": return None
		try:
			return float(str)
		except:
			return None


