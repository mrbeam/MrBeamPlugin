import socket
import sys
import threading
import time
import datetime
import collections
import json
from distutils.version import StrictVersion

from octoprint.events import Events as OctoPrintEvents
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.lib.rwlock import RWLock
from flask.ext.babel import gettext

# singleton
_instance = None


def ioBeamHandler(eventBusOct, socket_file=None):
	global _instance
	if _instance is None:
		_instance = IoBeamHandler(eventBusOct, socket_file)
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

	IOBEAM_MIN_REQUIRED_VERSION = '0.7.0'
	CLIENT_NAME = "MrBeamPlugin"
	CLIENT_ID = CLIENT_NAME + ".v{vers_mrb}"

	PROCESSING_TIMES_LOG_LENGTH = 100
	PROCESSING_TIME_WARNING_THRESHOLD = 0.1

	MESSAGE_LENGTH_MAX = 4096
	MESSAGE_NEWLINE = "\n"
	MESSAGE_SEPARATOR = ":"
	MESSAGE_OK = "ok"
	MESSAGE_ERROR = "err"
	MESSAGE_COMMAND = 'command'

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
	MESSAGE_ACTION_FAN_TYPE = 			"type"
	MESSAGE_ACTION_FAN_EXHAUST =        "exhaust"
	MESSAGE_ACTION_FAN_LINK_QUALITY =   "link_quality"

	# Possible datasets
	DATASET_FAN_DYNAMIC =	            "fan_dynamic"
	DATASET_FAN_STATIC = 				"fan_static"
	DATASET_FAN_EXHAUST = 				"fan_exhaust"
	DATASET_FAN_LINK_QUALITY= 			"fan_link_quality"
	DATASET_PCF =          				"pcf"
	DATASET_LID =   		        	"lid"
	DATASET_INTERLOCK =          		"intlk"
	DATASET_STEPRUN =            		"steprun"
	DATASET_LASER =	            		"laser"
	DATASET_LASERHEAD =					"laserhead"
	DATASET_IOBEAM =	           	 	"iobeam"

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

		self.command_request_id = 1

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
		"""
		Request a single temperature value from iobeam.
		:return: True if the command was sent sucessfully.
		"""
		return self._send_command({'request': [self.MESSAGE_DEVICE_LASER + "_temp"]})

	def send_fan_command(self, action, value=None):
		"""
		Send the specified command as fan:<command>
		:param command: One of the three values (ON:<0-100>/OFF/AUTO)
		:return: True if the command was sent sucessfull (does not mean it was sucessfully executed)
		"""
		command = {self.MESSAGE_COMMAND: {'device': self.MESSAGE_DEVICE_FAN, 'action': action}}
		if value:
			command[self.MESSAGE_COMMAND]['value'] = value

		# Add request id to the command
		command['request_id'] = self.command_request_id
		self.command_request_id += 1

		ok = self._send_command(command)
		# self._logger.info("send_fan_command(): ok: %s, command: %s", ok, command)
		return ok, command['request_id']

	def _send_command(self, command):
		"""
		Sends a command to iobeam
		:param command: Must not be None. May or may not end with a new line.
		:return: Boolean success
		"""
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

		try:
			self._my_socket.sendall("{}\n".format(json.dumps(command)))
		except Exception as e:
			self._errors += 1
			self._logger.error("Exception while sending command '%s' to socket: %s", command, e)
			return False
		return True

	def is_iobeam_version_ok(self):
		if self.iobeam_version is None:
			return False
		try:
			StrictVersion(self.iobeam_version)
		except ValueError as e:
			self._logger.error("iobeam version invalid: '{}'. ValueError from StrictVersion: {}".format(self.iobeam_version, e))
			return False

		return StrictVersion(self.iobeam_version) >= StrictVersion(self.IOBEAM_MIN_REQUIRED_VERSION)

	def subscribe(self, event, callback):
		"""
		Subscibe to an event
		:param event:
		:param callback:
		"""
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
				temp_socket.settimeout(10)
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

			id = self._send_identification()
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
							self._logger.warn("Warning continuation %s ", e.message)
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
			self._fireEvent(IoBeamEvents.DISCONNECT)  # on shutdown this won't be broadcasted

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
		if not data:
			return 1

		error_count = 0
		message_count = 0
		try:
			# Split all JSON messages by "\n"
			json_list = data.split(self.MESSAGE_NEWLINE)
			for json_data in json_list:
				if len(json_data) > 0:
					try:
						json_dict = json.loads(json_data)

						# Now there could be "data" and "response"
						if 'data' in json_dict:
							if not self.MESSAGE_ERROR in json_dict['data']:
								# Process all data sets
								if isinstance(json_dict['data'], dict):
									for dataset in json_dict['data']:
										if 'all' in dataset or 'info' in dataset:
											for dataset2 in dataset:
												error_count += self._handleDataset(dataset2, json_dict['data'][dataset][dataset2])
										error_count += self._handleDataset(dataset, json_dict['data'][dataset])
							else:
								self._logger.debug("Received error in data '%s'", json_dict['data'][self.MESSAGE_ERROR])
						elif 'response' in json_dict:
							error_count += self._handleResponse(json_dict)

						message_count += 1
					except ValueError, ve:
						self._logger.debug("Could not parse data '%s' as JSON", json_data)
						# TODO: hanle line: iobeam:version:0.6.0
					except Exception as e2:
						self._logger.debug("Some error with data '%s'", json_data)
						self._logger.debug(e2)
				# else:
					# self._logger.debug("Received empty message")

		except Exception as e:
			self._logger.debug("Error handling error")
			self._logger.debug(e)

		return error_count, message_count

	def _handleDataset(self, name, dataset):
		error_count = 0
		processing_start = time.time()

		err = -1
		try:
			if len(name) <= 0:
				err = self._handle_invalid_dataset(name, dataset)
			elif self.MESSAGE_ERROR in dataset:
				self._logger.debug("Received %s dataset error: %s", dataset, dataset[self.MESSAGE_ERROR])
			else:

				if name == self.DATASET_FAN_DYNAMIC:
					err = self._handle_fan_dynamic(dataset)
				elif name == self.DATASET_FAN_STATIC:
					err = self._handle_fan_static(dataset)
				elif name == self.DATASET_LASER:
					err = self._handle_laser(dataset)
				elif name == self.DATASET_LASERHEAD:
					err = self._handle_laserhead(dataset)
				elif name == self.DATASET_IOBEAM:
					err = self._handle_iobeam(dataset)
				elif name == self.DATASET_PCF:
					err = self._handle_pcf(dataset)
				elif name == self.DATASET_FAN_LINK_QUALITY:
					err = self._handle_link_quality(dataset)
				elif name == self.DATASET_FAN_EXHAUST:
					err = self._handle_exhaust(dataset)
				elif name == self.MESSAGE_DEVICE_UNUSED:
					pass
				elif name == self.MESSAGE_ERROR:
					err = self._handle_error_message(dataset)
				else:
					err = self._handle_unknown_device_message(dataset)
		except:
			self._logger.debug("Error handling message")
			self._logger.debug(dataset)

		if err >= 0:
			error_count += err

		processing_time = time.time() - processing_start
		self._handle_precessing_time(processing_time, dataset, err)

		return error_count

	def _handle_fan_dynamic(self, dataset):
		if isinstance(dataset, dict) and len(dataset) > 3:
			vals = dict(
				state=self._as_number(dataset[self.MESSAGE_ACTION_FAN_STATE]),
				rpm=self._as_number(dataset[self.MESSAGE_ACTION_FAN_RPM]),
				dust=self._as_number(dataset[self.MESSAGE_ACTION_DUST_VALUE]),
				connected=self._get_connected_val(dataset[self.MESSAGE_ACTION_FAN_CONNECTED]))
			# if token[4] == 'error':
			# 	self._logger.warn("Received fan connection error: %s", message)
			self._call_callback(IoBeamValueEvents.DYNAMIC_VALUE, dataset, vals)
			self._call_callback(IoBeamValueEvents.STATE_VALUE, dataset, dict(val=vals[self.MESSAGE_ACTION_FAN_STATE]))
			self._call_callback(IoBeamValueEvents.RPM_VALUE, dataset, dict(val=vals[self.MESSAGE_ACTION_FAN_RPM]))
			self._call_callback(IoBeamValueEvents.DUST_VALUE, dataset, dict(val=vals[self.MESSAGE_ACTION_DUST_VALUE]))
			self._call_callback(IoBeamValueEvents.CONNECTED_VALUE, dataset, dict(val=vals[self.MESSAGE_ACTION_FAN_CONNECTED]))
		else:
			# Handle values one by one
			if self.MESSAGE_ACTION_DUST_VALUE in dataset:
				dust_val = self._as_number(dataset[self.MESSAGE_ACTION_DUST_VALUE])
				if dust_val is not None:
					self._call_callback(IoBeamValueEvents.DUST_VALUE, dataset, dict(val=dust_val))

			if self.MESSAGE_ACTION_FAN_RPM in dataset:
				rpm_val = self._as_number(dataset[self.MESSAGE_ACTION_FAN_RPM])
				if rpm_val is not None:
					self._call_callback(IoBeamValueEvents.RPM_VALUE, dataset, dict(val=rpm_val))

			if self.MESSAGE_ACTION_FAN_STATE in dataset:
				state = self._as_number(dataset[self.MESSAGE_ACTION_FAN_STATE])
				if state is not None:
					self._call_callback(IoBeamValueEvents.STATE_VALUE, dataset, dict(val=state))

			if self.MESSAGE_ACTION_FAN_CONNECTED in dataset:
				self._call_callback(IoBeamValueEvents.CONNECTED_VALUE, dataset, dict(val=self._get_connected_val(dataset[self.MESSAGE_ACTION_FAN_CONNECTED])))
				if self.MESSAGE_ERROR in dataset[self.MESSAGE_ACTION_FAN_CONNECTED]:
					self._logger.warn("Received fan connection error: %s", dataset[self.MESSAGE_ACTION_FAN_CONNECTED][self.MESSAGE_ERROR])
		return 0

	def _handle_fan_static(self, dataset):
		if self.MESSAGE_ACTION_FAN_VERSION in dataset:
			self._logger.info("Received fan version %s: '%s'", dataset[self.MESSAGE_ACTION_FAN_VERSION], dataset)

		if self.MESSAGE_ACTION_FAN_FACTOR in dataset:
			self._logger.info("Received fan factor %s: '%s'", dataset[self.MESSAGE_ACTION_FAN_FACTOR], dataset)
		'''
		if self.MESSAGE_ACTION_FAN_PWM_MIN not in dataset:
			err += 1

		if self.MESSAGE_ACTION_FAN_TPR not in dataset:
			err += 1
		'''
		return 0

	def _handle_laser(self, dataset):
		if self.MESSAGE_ACTION_LASER_TEMP in dataset:
			if dataset[self.MESSAGE_ACTION_LASER_TEMP]:
				self._call_callback(IoBeamValueEvents.LASER_TEMP, dataset, dict(temp=self._as_number(dataset[self.MESSAGE_ACTION_LASER_TEMP])))

		if "serial" in dataset:
			if self.MESSAGE_ERROR not in dataset['serial']:
				_mrbeam_plugin_implementation.lh['serial'] = dataset['serial']
				self._logger.info("laserhead serial: %s", dataset['serial'])
			else:
				self._logger.info("laserhead: '%s'", dataset)

		if "power" in dataset and isinstance(dataset, dict):
			if self.MESSAGE_ERROR not in dataset['power']:
				for pV in dataset['power']:
					if self.MESSAGE_ERROR not in pV:
						pwr = None
						try:
							pwr = int(dataset['power'][pV])
						except:
							self._logger.info("laserhead: '%s'", dataset)
							self._logger.warn("Can't read power %s value as int: '%s'", pV, dataset['power'][pV])
						if pwr is not None:
							_mrbeam_plugin_implementation.lh['p_'+pV] = pwr
							self._logger.info("laserhead p_%s: %s", pV, pwr)
		return 0

	def _handle_laserhead(self, dataset):
		# iobeam sends the whole laserhead data
		try:
			data = 'ok\n| {}'.format(dataset)
			self._logger.info("laserhead data: %s", data)
		except:
			self._logger.exception("laserhead: exception while handling head:data: ")
		return 0

	def _handle_pcf(self, dataset):
		if self.MESSAGE_DEVICE_ONEBUTTON in dataset:
			self._handle_onebutton(dataset[self.MESSAGE_DEVICE_ONEBUTTON])

		if self.MESSAGE_DEVICE_INTERLOCK in dataset:
			self._handle_interlock(dataset[self.MESSAGE_DEVICE_INTERLOCK])

		if self.MESSAGE_DEVICE_LID in dataset:
			self._handle_lid(dataset[self.MESSAGE_DEVICE_LID])

		if self.MESSAGE_DEVICE_STEPRUN in dataset:
			self._handle_steprun(dataset[self.MESSAGE_DEVICE_STEPRUN])

		return 0

	def _handle_onebutton(self, dataset):
		duration = None
		if 'state' in dataset and dataset['state']:
			state = dataset['state']
			if 'duration' in dataset and dataset['duration']:
					try:
						duration = self._as_number(dataset['duration'])
					except:
						self._logger.debug("Received invalid onebtn duration: %s", dataset['duration'])
						return 1
		else:
			return self._handle_invalid_dataset(self.MESSAGE_DEVICE_ONEBUTTON, dataset)

		self._logger.debug("_handle_onebutton() message: %s, state: %s, duration: %s", dataset, state, duration)

		if state == self.MESSAGE_ACTION_ONEBUTTON_PRESSED:
			self._fireEvent(IoBeamEvents.ONEBUTTON_PRESSED)
		elif state == self.MESSAGE_ACTION_ONEBUTTON_DOWN and duration is not None:
			self._fireEvent(IoBeamEvents.ONEBUTTON_DOWN, duration)
		elif state == self.MESSAGE_ACTION_ONEBUTTON_RELEASED and duration is not None:
			self._fireEvent(IoBeamEvents.ONEBUTTON_RELEASED, duration)
		elif state == self.MESSAGE_ACTION_ONEBUTTON_UP:
			return 0
		else:
			return self._handle_invalid_dataset(self.MESSAGE_DEVICE_ONEBUTTON, dataset)
		return 0

	def _handle_interlock(self, dataset):
		if isinstance(dataset, dict):
			before_state = self.open_interlocks()
			for lock_id, lock_state in dataset.iteritems():
				self._logger.debug("_handle_interlock() dataset: %s, lock_id: %s, lock_state: %s, before_state: %s", dataset, lock_id, lock_state, before_state)

				if lock_id is not None and lock_state == self.MESSAGE_ACTION_INTERLOCK_OPEN:
					self._interlocks[lock_id] = True
				elif lock_id is not None and lock_state == self.MESSAGE_ACTION_INTERLOCK_CLOSED:
					self._interlocks.pop(lock_id, None)
				elif self.MESSAGE_ERROR in dataset:
					self._logger.error("Received interLock error: {}".format(dataset[self.MESSAGE_ERROR]))
					return 1
				else:
					return self._handle_invalid_message(dataset)

				now_state = self.open_interlocks()
				if now_state != before_state:
					if self.is_interlock_closed():
						# self._logger.debug("Interlock CLOSED")
						self._fireEvent(IoBeamEvents.INTERLOCK_CLOSED)
					else:
						# self._logger.debug("Interlock OPEN")
						self._fireEvent(IoBeamEvents.INTERLOCK_OPEN, now_state)
		return 0

	def _handle_lid(self, dataset):
		'''
		payload = None
		if isinstance(dataset, dict):
			action = dataset.keys()[0]
			payload = self._as_number(dataset[action])
		else:
		'''
		action = dataset

		self._logger.debug("_handle_lid() message: %s, action: %s", dataset, action)

		if action == self.MESSAGE_ACTION_LID_OPENED:
			self._fireEvent(IoBeamEvents.LID_OPENED)
		elif action == self.MESSAGE_ACTION_LID_CLOSED:
			self._fireEvent(IoBeamEvents.LID_CLOSED)
		else:
			return self._handle_invalid_message(dataset)
		return 0

	def _handle_steprun(self, dataset):
		return 0

	def _handle_iobeam(self, dataset):
		if 'version' in dataset:
			if dataset['version']:
				self.iobeam_version = dataset['version']
				ok = self.is_iobeam_version_ok()
				if ok:
					self._logger.info("Received iobeam version: %s - version OK", self.iobeam_version)
				else:
					self._logger.error("Received iobeam version: %s - version OUTDATED. IOBEAM_MIN_REQUIRED_VERSION: %s", self.iobeam_version, self.IOBEAM_MIN_REQUIRED_VERSION)
					_mrbeam_plugin_implementation.notify_frontend(title=gettext("Software Update required"),
					                                              text=gettext("Module 'iobeam' is outdated. Please run Software Update from 'Settings' > 'Software Update' before you start a laser job."),
																  type="error", sticky=True, replay_when_new_client_connects=True)
				return 0
			else:
				self._logger.warn("_handle_iobeam(): Received iobeam:version message without version number. Counting as error. Message: %s", dataset)
				return 1

		if 'init' in dataset:
			# introduced with iobeam 0.4.2
			# in future versions we could make this requried and only unlock laser functionality once this was ok
			if dataset['init'] and dataset['init'].startswith('ok'):
				self._logger.info("iobeam init ok: '%s'", dataset)
			else:
				# ANDYTEST add analytics=True to next log line
				self._logger.info("iobeam init error: '%s' - requesting iobeam_debug...", dataset)
				self._send_command('debug')
				text = '<br/>' + \
					   gettext("A possible hardware malfunction has been detected on this device. Please contact our support team immediately at:") + \
					   '<br/><a href="https://mr-beam.org/support" target="_blank">mr-beam.org/support</a><br/><br/>' \
				       '<strong>' + gettext("Error:") + '</strong><br/>{}'.format(dataset)
				_mrbeam_plugin_implementation.notify_frontend(title=gettext("Hardware malfunction"),
															  text=text,
															  type="error", sticky=True,
															  replay_when_new_client_connects=True)
		return 0

	def _handle_debug(self, dataset):
		self._logger.info("iobeam debug dataset: '%s'", dataset)
		return 0

	def _handle_exhaust(self, dataset):
		self._logger.info("exhaust dataset: '%s'", dataset)
		return 0

	def _handle_link_quality(self, dataset):
		self._logger.info("link quality dataset: '%s'", dataset)
		return 0

	def _handle_invalid_dataset(self, name, dataset):
		self._logger.debug("Received invalid dataset %s: '%s'", name, dataset)
		return 0

	def _handleResponse(self, message):
		response = message['response']
		if 'request_id' in message:
			message['response']['request_id'] = message['request_id']
		if 'state' in response:
			value = response['state']
			# check if OK otherwise it's an error
			success = value == self.MESSAGE_OK
			payload = dict(success=success)
			if not success and self.MESSAGE_ERROR in response:
				payload['error'] = response[self.MESSAGE_ERROR]

			if self.MESSAGE_COMMAND in response:
				if 'device' in response[self.MESSAGE_COMMAND] and 'action' in response[self.MESSAGE_COMMAND]:
					device = response[self.MESSAGE_COMMAND]['device']
					action = response[self.MESSAGE_COMMAND]['action']

					if device == self.MESSAGE_DEVICE_FAN:
						if action == self.MESSAGE_ACTION_FAN_ON:
							self._call_callback(IoBeamValueEvents.FAN_ON_RESPONSE, response, payload)
						elif action == self.MESSAGE_ACTION_FAN_OFF:
							self._call_callback(IoBeamValueEvents.FAN_OFF_RESPONSE, response, payload)
						elif action == self.MESSAGE_ACTION_FAN_AUTO:
							self._call_callback(IoBeamValueEvents.FAN_AUTO_RESPONSE, response, payload)
						elif action == self.MESSAGE_ACTION_FAN_FACTOR:
							self._call_callback(IoBeamValueEvents.FAN_FACTOR_RESPONSE, response, payload)
						else:
							self._logger.debug("Received response: %s", response)

					return 0
		return 1

	def _handle_invalid_message(self, message):
		self._logger.warn("Received invalid message: '%s'", message)
		return 1

	def _handle_error_message(self, message):
		# TODO: A better way to extract?
		action = message.values()[0]
		if action == "reconnect":
			raise Exception("ioBeam requested to reconnect. Now doing so...")
		return 1

	def _handle_unknown_device_message(self, message):
		self._logger.warn("Received message about unknown device: %s", message)
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
			if entry['ts'] < earliest:
				earliest = entry['ts']
			sum += entry['processing_time']
			count += 1
		if count <= 0:
			self._logger.error("_handle_precessing_time() stats: message count is <= 0, something seems be wrong.")
		else:
			avg = sum/count
			time_formatted = datetime.datetime.fromtimestamp(earliest).strftime('%Y-%m-%d %H:%M:%S')
			self._logger.info("Message handling stats: %s message since %s; max: %ss, avg: %ss, min: %ss", count, time_formatted, max, avg, min)

	def _send_identification(self):
		client_name = self.CLIENT_ID.format(vers_mrb=_mrbeam_plugin_implementation._plugin_version)
		cmd = {'client': {'name': self.CLIENT_NAME, 'version': _mrbeam_plugin_implementation._plugin_version}}
		sent = self._send_command(cmd)
		return client_name if sent else False

	def _fireEvent(self, event, payload=None):
		self._event_bus.fire(event, payload)

	def _as_number(self, str):
		if str is None:
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
