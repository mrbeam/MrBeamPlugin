import time
import json
import os.path
import logging
import netifaces
import sys
import fileinput
import re
import uuid
import requests

from datetime import datetime
from value_collector import ValueCollector
from cpu import Cpu
from threading import Timer

from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint.events import Events as OctoPrintEvents
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.iobeam.laserhead_handler import laserheadHandler
from analytics_keys import AnalyticsKeys as ak
from uploader import FileUploader

# singleton
_instance = None


def analyticsHandler(plugin):
	global _instance
	if _instance is None:
		_instance = AnalyticsHandler(plugin)
	return _instance


def existing_analyticsHandler():
	"""
	Returns AnalyticsHandler instance only if it's already initialized. None otherwise
	:return: None or AnalyticsHandler instance
	"""
	global _instance
	return _instance


class AnalyticsHandler(object):
	DISK_SPACE_TIMER = 3.0
	IP_ADDRESSES_TIMER = 15.0
	SELF_CHECK_TIMER = 20.0
	INTERNET_CONNECTION_TIMER = 25.0
	MAINTENANCE_TIMER = 5.0
	SELF_CHECK_USER_AGENT = 'MrBeamPlugin self check'

	def __init__(self, plugin):
		self._plugin = plugin
		self._event_bus = plugin._event_bus
		self._settings = plugin._settings
		self._laserheadHandler = laserheadHandler(plugin)

		self._logger = mrb_logger("octoprint.plugins.mrbeam.analytics.analyticshandler")

		self._analyticsOn = self._settings.get(['analyticsEnabled'])
		self._camAnalyticsOn = self._settings.get(['analytics', 'cam_analytics'])

		self._session_id = "{uuid}@{serial}".format(serial=self._plugin.getSerialNum(), uuid=uuid.uuid4().hex)

		self._current_job_id = None
		self._isJobPaused = False
		self._isCoolingPaused = False
		self._isJobDone = False

		self._current_dust_collector = None
		self._current_cam_session_id = None
		self._current_intensity_collector = None
		self._current_lasertemp_collector = None
		self._current_cpu_data = None
		self._current_job_time_estimation = None

		self._storedConversions = list()

		self._analytics_log_version = 7		# bumped in 0.3.1.1 for os_health

		self.event_waiting_for_terminal_dump = None

		self._logger.info("Analytics analyticsEnabled: %s, sid: %s", self._analyticsOn, self._session_id)

		self.analyticsfolder = os.path.join(self._settings.getBaseFolder("base"),
		                                    self._settings.get(['analytics', 'folder']))
		if not os.path.isdir(self.analyticsfolder):
			os.makedirs(self.analyticsfolder)

		if self._analyticsOn is not None:
			FileUploader.upload_now(self._plugin)

		self._jsonfile = os.path.join(self.analyticsfolder, self._settings.get(['analytics', 'filename']))

		if self._analyticsOn:
			self._activate_analytics()

	def _activate_analytics(self):
		if not os.path.isfile(self._jsonfile):
			self._init_jsonfile()

		if self._analyticsOn:
			# check if <two days> have passed and software should be written away
			TWO_DAYS = 2
			_days_passed_since_last_log = self._days_passed(self._jsonfile)
			self._logger.debug('Days since last edit: {}'.format(_days_passed_since_last_log))
			if _days_passed_since_last_log > TWO_DAYS:
				self._write_current_software_status()

			self._subscribe()

	def _subscribe(self):
		self._event_bus.subscribe(OctoPrintEvents.PRINT_STARTED, self._event_print_started)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_PAUSED, self._event_print_paused)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_RESUMED, self._event_print_resumed)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_DONE, self._event_print_done)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_FAILED, self._event_print_failed)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_CANCELLED, self._event_print_cancelled)
		self._event_bus.subscribe(OctoPrintEvents.SLICING_STARTED, self._event_slicing_started)
		self._event_bus.subscribe(OctoPrintEvents.SLICING_DONE, self._event_slicing_done)
		self._event_bus.subscribe(MrBeamEvents.PRINT_PROGRESS, self._event_print_progress)
		self._event_bus.subscribe(MrBeamEvents.LASER_COOLING_PAUSE, self._event_laser_cooling_pause)
		self._event_bus.subscribe(MrBeamEvents.LASER_COOLING_RESUME, self._event_laser_cooling_resume)
		self._event_bus.subscribe(MrBeamEvents.LASER_JOB_DONE, self._event_laser_job_done)
		self._event_bus.subscribe(OctoPrintEvents.STARTUP, self._event_startup)
		self._event_bus.subscribe(OctoPrintEvents.SHUTDOWN, self._event_shutdown)
		self._event_bus.subscribe(MrBeamEvents.ANALYTICS_DATA, self._other_plugin_data)
		self._event_bus.subscribe(MrBeamEvents.JOB_TIME_ESTIMATED, self._event_job_time_estimated)

	@staticmethod
	def _getLaserHeadVersion():
		# TODO get Real laser_head_id
		laser_head_version = None
		return laser_head_version

	@staticmethod
	def _getSerialNumber():
		return _mrbeam_plugin_implementation.getSerialNum()

	# def _getShortSerial(self):
	# 	serial_long = self._getSerialNumber()
	# 	return serial_long.split('-')[0][-8::]

	@staticmethod
	def _getHostName():
		return _mrbeam_plugin_implementation.getHostname()

	@staticmethod
	def _days_passed(path_to_file):
		"""
		Returns time that has passed since last log into analytics file in days
		:return: int: days since last log
		"""
		# check days since path_to_file has been changed the last time
		lm_ts = os.path.getmtime(path_to_file)
		lm_date = datetime.utcfromtimestamp(lm_ts)

		now_date = datetime.utcnow()
		days_passed = (now_date - lm_date).days

		return days_passed

	def analytics_user_permission_change(self, analytics_enabled):
		self._logger.info("analytics user permission change: analyticsEnabled=%s", analytics_enabled)

		if analytics_enabled:
			self._analyticsOn = True
			self._settings.set_boolean(["analyticsEnabled"], True)
			self._activate_analytics()
			self._write_deviceinfo(ak.ANALYTICS_ENABLED, payload=dict(enabled=True))
		else:
			# can not log this since the user just disagreed
			# self._write_deviceinfo(ak.ANALYTICS_ENABLED, payload=dict(enabled=False))
			self._analyticsOn = False
			self._settings.set_boolean(["analyticsEnabled"], False)

	def log_event(self, level, msg,
	              module=None,
	              component=None,
	              component_version=None,
	              caller=None,
	              exception_str=None,
	              stacktrace=None,
	              wait_for_terminal_dump=False):
		filename = caller.filename.replace(__package_path__ + '/', '')
		payload = dict(
			level=logging._levelNames[level] if level in logging._levelNames else level,
			msg=msg,
			module=module,
			component=component or _mrbeam_plugin_implementation._identifier,
			component_version=component_version or _mrbeam_plugin_implementation._plugin_version
		)
		if exception_str:
			payload['level'] = ak.EXCEPTION
		if caller is not None:
			payload.update({
				'hash': hash('{}{}{}'.format(filename, caller.lineno, _mrbeam_plugin_implementation._plugin_version)),
				'file': filename,
				'line': caller.lineno,
				'function': caller.function,
				# code_context: caller.code_context[0].strip()
			})
		if exception_str:
			payload['exception'] = exception_str
		if stacktrace:
			payload['stacktrace'] = stacktrace

		if wait_for_terminal_dump:
			self.event_waiting_for_terminal_dump = dict(
				payload=payload,
			)
		else:
			self._write_log_event(ak.EVENT_LOG, payload=payload, analytics=False)

	def log_terminal_dump(self, dump):
		if self.event_waiting_for_terminal_dump is not None:
			payload = self.event_waiting_for_terminal_dump['payload']
			payload['terminal_dump'] = dump
			self._write_log_event(ak.EVENT_LOG, payload=payload, analytics=False)
			self.event_waiting_for_terminal_dump = None
		else:
			self._logger.warn(
				"log_terminal_dump() called but no foregoing event tracked. self.event_waiting_for_terminal_dump is None. ignoring this dump.")

	def log_cpu_warning(self, temp, throttle_alerts):
		try:
			data = {'temp': temp,
					'throttle_alerts': throttle_alerts}
			self._write_log_event(ak.LOG_CPU, payload=data)
		except Exception as e:
			self._logger.exception('Error during log_cpu_warning: {}'.format(e.message), analytics=True)

	def log_camera_session(self, errors):
		try:
			self._logger.info(errors)
			success = True
			if errors:
				success = False
			data = {
				'success': success,
				'err': errors,
			}
			self._write_log_event(ak.CAMERA, payload=data)

		except Exception as e:
			self._logger.exception('Error during log_camera_error: {}'.format(e.message), analytics=True)

	def log_frontend_event(self, event, payload=dict()):
		try:
			self._write_frontend_event(event, payload=payload)
		except Exception as e:
			self._logger.exception('Error during log_frontend_event: {}'.format(e.message), analytics=True)

	def log_os_health_event(self, data):
		try:
			self._write_log_event(ak.OS_HEALTH, payload=data)
		except Exception as e:
			self._logger.exception('Error during log_frontend_event: {}'.format(e.message), analytics=True)

	def log_camera_session(self, errors):
		try:
			self._logger.info(errors)
			success = True
			if errors:
				success = False
			data = {
				'success': success,
				'err': errors,
			}
			self._write_log_event(ak.CAMERA, payload=data)

		except Exception as e:
			self._logger.exception('Error during log_camera_error: {}'.format(e.message), analytics=True)

	def _write_current_software_status(self):
		try:
			# TODO get all software statuses
			# get all sw_stati and then print out status for each
			# for each sw_status in sw_stati:
			# 	sw_status = dict(name='<name>',version='<x.x.x>')
			# 	self._write_deviceinfo('sw_status',payload=sw_status)
			pass
		except Exception as e:
			self._logger.error('Error during write_current_software_status: {}'.format(e.message))

	def _event_startup(self, event, payload):
		self._write_new_line()
		payload = {
			ak.LASERHEAD_SERIAL: self._laserheadHandler.get_current_used_lh_data()['serial'],
			ak.ENV: self._plugin.get_env(),
			ak.USERS: len(self._plugin._user_manager._users)  # users = self.plugin._user_manager._users
		}
		self._write_deviceinfo(ak.STARTUP, payload=payload)

		# Schedule event_disk_space task (to write that line 3 seconds after startup)
		t1 = Timer(self.DISK_SPACE_TIMER, self._event_disk_space)
		t1.start()

		# Schedule event_ip_addresses task (to write that line 15 seconds after startup)
		t2 = Timer(self.IP_ADDRESSES_TIMER, self._event_ip_addresses)
		t2.start()

		# Schedule event_http_self_check task (to write that line 20 seconds after startup)
		t3 = Timer(self.SELF_CHECK_TIMER, self._event_http_self_check)
		t3.start()

		# Schedule event_http_self_check task (to write that line 20 seconds after startup)
		t4 = Timer(self.INTERNET_CONNECTION_TIMER, self._event_internet_connection)
		t4.start()

	def _event_shutdown(self, event, payload):
		self._write_deviceinfo(ak.SHUTDOWN)

	def write_flash_grbl(self, from_version, to_version, succesful, err=None):
		payload = dict(
			from_version=from_version,
			to_version=to_version,
			succesful=succesful,
			err=err)
		self._write_deviceinfo(ak.FLASH_GRBL, payload=payload)

	def write_mrbeam_usage(self, usage_data):
		self._write_deviceinfo(ak.MRBEAM_USAGE, payload=usage_data)

	def _event_http_self_check(self):
		try:
			payload = dict()
			interfaces = netifaces.interfaces()
			err = None

			for interface in interfaces:
				if interface != 'lo':
					addresses = netifaces.ifaddresses(interface)
					if netifaces.AF_INET in addresses:
						ip = addresses[netifaces.AF_INET][0]['addr']

						try:
							url = "http://" + ip
							headers = {
								'User-Agent': self.SELF_CHECK_USER_AGENT
							}
							r = requests.get(url, headers=headers)
							response = r.status_code
							elapsed_seconds = r.elapsed.total_seconds()
						except requests.exceptions.RequestException as e:
							response = -1
							err = str(e)

						payload[interface] = {
							"ip": ip,
							"response": response,
							"elapsed_s": elapsed_seconds,
							"err": err,
						}

			self._write_deviceinfo(ak.HTTP_SELF_CHECK, payload=payload)

		except:
			self._logger.exception('Exception when performing the http self check')

	def _event_internet_connection(self):
		try:
			try:
				headers = {
					'User-Agent': self.SELF_CHECK_USER_AGENT
				}
				r = requests.head('http://find.mr-beam.org', headers=headers)
				response = r.status_code
				err = None
				connection = True
			except requests.exceptions.RequestException as e:
				response = -1
				err = str(e)
				connection = False

			payload = {
				"response": response,
				"err": err,
				"connection": connection,
			}
			self._write_deviceinfo(ak.INTERNET_CONNECTION, payload=payload)
		except:
			self._logger.exception('Exception while performing the internet check')

	def _event_ip_addresses(self):
		try:
			payload = dict()
			interfaces = netifaces.interfaces()

			for interface in interfaces:
				addresses = netifaces.ifaddresses(interface)
				payload[interface] = dict()
				if netifaces.AF_INET in addresses:
					payload[interface]['IPv4'] = addresses[netifaces.AF_INET][0]['addr']
				if netifaces.AF_INET6 in addresses:
					for idx, addr in enumerate(addresses[netifaces.AF_INET6]):
						payload[interface]['IPv6_{}'.format(idx)] = addr['addr']

			self._write_deviceinfo(ak.IPS, payload=payload)

		except:
			self._logger.exception('Exception when recording the IP addresses')

	def _event_disk_space(self):
		try:
			statvfs = os.statvfs('/')
			total_space = statvfs.f_frsize * statvfs.f_blocks
			available_space = statvfs.f_frsize * statvfs.f_bavail  # Available space for non-super users
			used_percent = round((total_space - available_space) * 100 / total_space)

			disk_space = {
				ak.TOTAL_SPACE: total_space,
				ak.AVAILABLE_SPACE: available_space,
				ak.USED_SPACE: used_percent,
			}
			self._write_deviceinfo(ak.DISK_SPACE, payload=disk_space)

		except:
			self._logger.exception('Exception when saving info about the disk space')

	def event_laserhead_info(self):
		try:
			lh = self._laserheadHandler.get_current_used_lh_data()
			settings = self._laserheadHandler.get_correction_settings()
			laserhead_info = {
				ak.LASERHEAD_SERIAL: lh['serial'],
				ak.POWER_65: lh['info']['p_65'],
				ak.POWER_75: lh['info']['p_75'],
				ak.POWER_85: lh['info']['p_85'],
				ak.CORRECTION_FACTOR: lh['info']['correction_factor'],
				ak.CORRECTION_ENABLED: settings['correction_enabled'],
				ak.CORRECTION_OVERRIDE: settings['correction_factor_override'],
			}
			self._write_deviceinfo(ak.LASERHEAD_INFO, payload=laserhead_info)

		except:
			self._logger.exception('Exception when saving info about the laserhead')

	def _event_print_started(self, event, payload):
		if not self._current_job_id:
			self._current_job_id = 'j_{}_{}'.format(self._getSerialNumber(), time.time())
		self._current_cpu_data = Cpu(state='laser', repeat=True)
		self._init_collectors()
		self._isJobPaused = False
		self._isCoolingPaused = False
		self._isJobDone = False
		self._write_conversion_details()
		self._write_jobevent(ak.PRINT_STARTED)

	def _init_collectors(self):
		self._current_dust_collector = ValueCollector('DustColl')
		self._current_intensity_collector = ValueCollector('IntensityColl')
		self._current_lasertemp_collector = ValueCollector('TempColl')

	def _event_print_paused(self, event, payload):
		# TODO add how it has been paused (lid_opened during job, frontend, onebutton)
		"""
		Cooling: payload holds some information if it was a cooling_pause or not.
		Lid/Button: Currently there is no way to know other than checking the current state: _mrbeam_plugin_implementation._ioBeam .is_interlock_closed()
		"""
		if not self._isJobPaused:  # prevent multiple printPaused events per Job
			self._write_jobevent(ak.PRINT_PAUSED, payload={ak.JOB_DURATION: int(round(payload['time']))})
			self._isJobPaused = True

	def _event_print_resumed(self, event, payload):
		if self._isJobPaused:  # prevent multiple printResume events per Job
			self._write_jobevent(ak.PRINT_RESUMED, payload={ak.JOB_DURATION: int(round(payload['time']))})
			self._isJobPaused = False

	def _event_print_done(self, event, payload):
		if not self._isJobDone:
			self._isJobDone = True  # prevent two jobDone events per Job
			self._write_jobevent(ak.PRINT_DONE, payload={ak.JOB_DURATION: int(round(payload['time'])),
														ak.JOB_TIME_ESTIMATION: int(round(self._current_job_time_estimation))})
			self._write_collectors()
			self._write_cpu_data(dur=payload['time'])

	def _write_collectors(self):
		self._write_jobevent(ak.DUST_SUM, payload=self._current_dust_collector.getSummary())
		self._write_jobevent(ak.INTENSITY_SUM, payload=self._current_intensity_collector.getSummary())
		self._write_jobevent(ak.LASERTEMP_SUM, payload=self._current_lasertemp_collector.getSummary())

	def _write_cpu_data(self, dur=None):
		payload = self._current_cpu_data.get_cpu_data()
		payload['dur'] = dur
		self._write_jobevent(ak.CPU_DATA, payload=payload)

	def _cleanup(self):
		self._current_job_id = None
		self._current_dust_collector = None
		self._current_intensity_collector = None
		self._current_lasertemp_collector = None
		self._current_cpu_data = None

	def _event_laser_job_done(self, event, payload):
		if self._current_job_id is not None:
			self._write_jobevent(ak.LASERJOB_DONE)
			self._cleanup()
		FileUploader.upload_now(self._plugin, delay=5.0)

	def _event_print_failed(self, event, payload):
		if self._current_job_id is not None:
			self._write_jobevent(ak.PRINT_FAILED, payload={ak.JOB_DURATION: int(round(payload['time']))})
			self._write_collectors()
			self._write_cpu_data(dur=payload['time'])
			self._cleanup()

	def _event_print_cancelled(self, event, payload):
		if self._current_job_id is not None:
			self._write_jobevent(ak.PRINT_CANCELLED, payload={ak.JOB_DURATION: int(round(payload['time']))})
			self._write_collectors()
			self._write_cpu_data(dur=payload['time'])
			self._cleanup()

	def _event_print_progress(self, event, payload):
		data = {
			ak.PROGRESS_PERCENT: payload['progress'],
			ak.PROGRESS_LASER_TEMPERATURE: self._current_lasertemp_collector.get_latest_value(),
			ak.PROGRESS_LASER_INTENSITY: self._current_intensity_collector.get_latest_value(),
			ak.PROGRESS_DUST_VALUE: self._current_dust_collector.get_latest_value(),
			ak.JOB_DURATION: round(payload['time'], 1),
			ak.FAN_RPM: self._plugin._dustManager.get_fan_rpm(),
			ak.FAN_STATE: self._plugin._dustManager.get_fan_state(),
		}
		self._write_jobevent(ak.PRINT_PROGRESS, data)

		if self._current_cpu_data:
			self._current_cpu_data.update_progress(payload['progress'])

	def _event_slicing_started(self, event, payload):
		self._current_job_id = 'j_{}_{}'.format(self._getSerialNumber(), time.time())
		self._current_cpu_data = Cpu(state='slicing', repeat=False)

	def _event_slicing_done(self, event, payload):
		if self._current_cpu_data:
			self._current_cpu_data.record_cpu_data()
			self._write_cpu_data(dur=payload['time'])

	def _event_laser_cooling_pause(self, event, payload):
		if not self._isCoolingPaused:
			data = {
				ak.LASERTEMP: None
			}
			if self._current_lasertemp_collector:
				data[ak.LASERTEMP] = self._current_lasertemp_collector.get_latest_value()
			self._write_jobevent(ak.COOLING_START, payload=data)
			self._isCoolingPaused = True

	def _event_laser_cooling_resume(self, event, payload):
		if self._isCoolingPaused:
			data = {
				ak.LASERTEMP: None
			}
			if self._current_lasertemp_collector:
				data[ak.LASERTEMP] = self._current_lasertemp_collector.get_latest_value()
			self._write_jobevent(ak.COOLING_DONE, payload=data)
			self._isCoolingPaused = False

	def _event_job_time_estimated(self, event, payload):
		self._current_job_time_estimation = payload['jobTimeEstimation']

	def _other_plugin_data(self, event, event_payload):
		try:
			if 'component' in event_payload and 'type' in event_payload and 'component_version' in event_payload:
				component = event_payload.get('component')
				type = event_payload.get('type')
				if type == ak.EVENT_LOG:
					data = event_payload.get('data', dict())
					data['component'] = component
					data['component_version'] = event_payload.get('component_version')
					self._write_log_event(ak.EVENT_LOG, payload=data)
				else:
					self._logger.warn("Unknown type: '%s' from component %s. payload: %s", type, component,
					                  event_payload)
			elif 'plugin' in event_payload and 'eventname' in event_payload:
				plugin = event_payload.get('plugin')
				if plugin:
					eventname = event_payload.get('eventname')
					data = event_payload.get('data', None)
					self._write_event(plugin, eventname, self._analytics_log_version, payload=dict(data=data))
				else:
					self._logger.warn("Invalid plugin: '%s'. payload: %s", plugin, event_payload)
			else:
				self._logger.warn("Invalid payload data in event %s", event)
		except Exception as e:
			self._logger.exception('Exception during _other_plugin_data: {}'.format(e.message))

	def log_iobeam_message(self, iobeam_version, message):
		data = dict(
			version=iobeam_version,
			message=message
		)
		self._write_log_event(ak.IOBEAM, payload=data)

	def log_ui_render_calls(self, host, remote_ip, referrer, language):
		try:
			data = dict(
				host=host,
				remote_ip=remote_ip,
				referrer=referrer,
				language=language
			)
			self._write_event(ak.TYPE_CONNECTIVITY_EVENT, ak.EVENT_UI_RENDER_CALL, self._analytics_log_version,
			                  payload=dict(data=data))
		except Exception as e:
			self._logger.exception('Exception during log_ui_render_calls: {}'.format(e.message))

	def log_client_opened(self, remote_ip):
		try:
			data = dict(
				remote_ip=remote_ip
			)
			self._write_event(ak.TYPE_CONNECTIVITY_EVENT, ak.EVENT_CLIENT_OPENED, self._analytics_log_version,
			                  payload=dict(data=data))
		except Exception as e:
			self._logger.exception('Exception during log_client_opened: {}'.format(e.message))

	def log_connections_state(self, connections):
		try:
			self._write_event(ak.TYPE_CONNECTIVITY_EVENT, ak.CONNECTIONS_STATE, self._analytics_log_version,
			                  payload=dict(data=connections))
		except Exception as e:
			self._logger.exception('Exception during log_connections_state: {}'.format(e.message))

	def write_cam_update(self, newMarkers, newCorners):
		try:
			if self._camAnalyticsOn:
				data = {
					ak.MARKERS: newMarkers,
					ak.CORNERS: newCorners
				}
				self.write_cam_event(ak.CAM_CALIBRATION, payload=data)
		except Exception as e:
			self._logger.exception('Error during write_cam_update: {}'.format(e.message))

	def software_channel_switch_event(self, old_channel, new_channel):
		try:
			data = {
				ak.OLD_CHANNEL: old_channel,
				ak.NEW_CHANNEL: new_channel,
			}

			self._write_event(ak.TYPE_DEVICE_EVENT, ak.SW_CHANNEL_SWITCH, self._analytics_log_version,
							  payload=dict(data=data))

		except Exception as e:
			self._logger.exception('Error when writing the software channel switch event: {}'.format(e.message))

	def store_conversion_details(self, details):
		try:
			self._storedConversions = list()

			if self._analyticsOn:
				# "laser_job" line as the beginning of a job
				eventname = ak.LASER_JOB
				data = {
					'advanced_settings': details['advanced_settings']
				}
				data.update(details['material'])
				self._store_conversion_details(eventname, payload=data)

				# "conv_eng" line with the engraving parameters
				if 'engrave' in details and details['engrave'] and 'raster' in details:
					eventname = ak.CONV_ENGRAVE
					eng_settings = details['raster']

					data = {
						'svgDPI': details['svgDPI'],
						'mpr_black': self._calculate_mpr_value(eng_settings.get('intensity_black'), eng_settings.get('speed_black')),
						'mpr_white': self._calculate_mpr_value(eng_settings.get('intensity_white'), eng_settings.get('speed_white')),
					}
					data.update(eng_settings)
					self._store_conversion_details(eventname, payload=data)

				# One or many "conv_cut" lines with the cutting parameters
				if 'vector' in details and details['vector']:
					eventname = ak.CONV_CUT

					for color_settings in details['vector']:
						data = {
							'svgDPI': details['svgDPI'],
							'mpr': self._calculate_mpr_value(color_settings.get('intensity'), color_settings.get('feedrate'), color_settings.get('passes')),
						}
						data.update(color_settings)
						self._store_conversion_details(eventname, payload=data)

				# One or many "design_file" lines with the design details
				if 'design_files' in details and details['design_files']:
					eventname = ak.DESIGN_FILE
					for design_file in details['design_files']:
						data = {}
						data.update(design_file)
						self._store_conversion_details(eventname, payload=data)

		except Exception as e:
			self._logger.exception('Error during store_conversion_details: {}'.format(e.message))

	def _store_conversion_details(self, eventname, payload=None):
		data = {
			# Here we save the event so we can extract it later and add it to the analytics line (later we can't know it)
			ak.EVENT: eventname,
		}
		if payload is not None:
			data.update(payload)
		self._storedConversions.append(data)

	@staticmethod
	def _calculate_mpr_value(intensity, speed, passes=1):
		if intensity and speed and passes:
			mpr = round(float(intensity) / float(speed) * int(passes), 2)
		else:
			mpr = None

		return mpr

	def _write_conversion_details(self):
		try:
			for conversion_details in self._storedConversions:
				event = conversion_details[ak.EVENT]
				conversion_details.pop(ak.EVENT)
				self._write_jobevent(event, conversion_details)
			self._storedConversions = list()

		except Exception as e:
			self._logger.exception('Error during write_conversion_details: {}'.format(e.message))

	def _write_deviceinfo(self, event, payload=None):
		try:
			data = dict()
			# TODO add data validation/preparation here
			if payload is not None:
				data[ak.DATA] = payload
			self._write_event(ak.TYPE_DEVICE_EVENT, event, self._analytics_log_version, payload=data)
		except Exception as e:
			self._logger.exception('Error during write_device_info: {}'.format(e.message))

	def _write_log_event(self, event, payload=None, analytics=False):
		try:
			data = dict()
			# TODO add data validation/preparation here
			if payload is not None:
				data[ak.DATA] = payload
			self._write_event(ak.TYPE_LOG_EVENT, event, self._analytics_log_version, payload=data, analytics=analytics)
		except Exception as e:
			self._logger.exception('Error during _write_log_event: {}'.format(e.message), analytics=analytics)

	def _write_frontend_event(self, event, payload=None):
		try:
			data = dict()
			if payload is not None:
				data[ak.DATA] = payload
			self._write_event(ak.TYPE_FRONTEND, event, self._analytics_log_version, payload=data, analytics=True)

		except Exception as e:
			self._logger.exception('Error during _write_log_event: {}'.format(e.message), analytics=True)

	def _write_jobevent(self, event, payload=None):
		try:
			# TODO add data validation/preparation here
			data = dict(job_id=self._current_job_id)

			if payload is not None:
				data[ak.DATA] = payload

			if event in (ak.LASERTEMP_SUM, ak.INTENSITY_SUM):
				data[ak.DATA][ak.LASERHEAD_VERSION] = self._getLaserHeadVersion()
				data[ak.DATA][ak.LASERHEAD_SERIAL] = self._laserheadHandler.get_current_used_lh_data()['serial']

			_jobevent_type = ak.TYPE_JOB_EVENT
			self._write_event(_jobevent_type, event, self._analytics_log_version, payload=data)
		except Exception as e:
			self._logger.exception('Error during write_jobevent: {}'.format(e.message))

	def update_cam_session_id(self, lid_state):
		if self._camAnalyticsOn:
			if lid_state == 'lid_opened':
				self._current_cam_session_id = 'c_{}_{}'.format(self._getSerialNumber(), time.time())

	def write_pic_prep_event(self, payload=None):
		try:
			if self._camAnalyticsOn:
				data = dict()
				data[ak.CAM_SESSION_ID] = self._current_cam_session_id
				# TODO add data validation/preparation here
				if 'precision' in payload:
					del payload['precision']
				if 'corners_calculated' in payload:
					del payload['corners_calculated']
				if 'undistorted_saved' in payload:
					del payload['undistorted_saved']
				if 'high_precision' in payload:
					del payload['high_precision']
				if 'markers_recognized' in payload:
					del payload['markers_recognized']

				if payload is not None:
					data[ak.DATA] = payload

				self._write_event(ak.TYPE_CAM_EVENT, ak.PIC_PREP, self._analytics_log_version, payload=data)
		except Exception as e:
			self._logger.exception('Error during write_cam_event: {}'.format(e.message))

	def write_cam_event(self, eventname, payload=None):
		try:
			if self._camAnalyticsOn:
				data = dict()

				if payload is not None:
					data[ak.DATA] = payload

				self._write_event(ak.TYPE_CAM_EVENT, eventname, self._analytics_log_version, payload=data)
		except Exception as e:
			self._logger.exception('Error during write_cam_event: {}'.format(e.message))

	def _write_event(self, typename, eventname, version, payload=None, analytics=False):
		try:
			data = {
				ak.SERIALNUMBER: self._getSerialNumber(),
				ak.TYPE: typename,
				ak.VERSION: version,
				ak.EVENT: eventname,
				ak.TIMESTAMP: time.time(),
				ak.NTP_SYNCED: _mrbeam_plugin_implementation.is_time_ntp_synced(),
				ak.SESSION_ID: self._session_id,
				ak.VERSION_MRBEAM_PLUGIN: _mrbeam_plugin_implementation._plugin_version,
				ak.SOFTWARE_TIER: self._settings.get(["dev", "software_tier"]),
			}
			if payload is not None:
				data.update(payload)
			self._append_data_to_file(data)
		except Exception as e:
			self._logger.error('Error during _write_event: {}'.format(e.message), analytics=analytics)

	def write_final_dust(self, dust_start, dust_start_ts, dust_end, dust_end_ts):
		"""
		Sends dust values after print_done (the final dust profile). This is to check how fast dust is getting less in the machine
		and to check for filter full later.
		:param dust_start: dust_value at state print_done
		:param dust_start_ts: timestamp of dust_value at state print done
		:param dust_end: dust_value at job_done
		:param dust_end_ts: timestamp at dust_value at job_done
		:return:
		"""
		dust_duration = round(dust_end_ts - dust_start_ts, 4)
		dust_difference = round(dust_end - dust_start, 5)
		dust_per_time = dust_difference / dust_duration
		self._logger.debug(
			"dust extraction time {} from {} to {} (difference: {},gradient: {})".format(dust_duration, dust_start,
			                                                                             dust_end, dust_difference,
			                                                                             dust_per_time))

		data = {
			ak.DUST_START: dust_start,
			ak.DUST_END: dust_end,
			ak.DUST_START_TS: dust_start_ts,
			ak.DUST_END_TS: dust_end_ts,
			ak.DUST_DURATION: dust_duration,
			ak.DUST_DIFF: dust_difference,
			ak.DUST_PER_TIME: dust_per_time
		}
		self._write_dust_log(data)

	def add_dust_value(self, dust_value):
		"""
		:param dust_value:
		:return:
		"""
		if self._analyticsOn and self._current_dust_collector is not None:
			try:
				self._current_dust_collector.addValue(dust_value)
			except Exception as e:
				self._logger.exception('Error during add_dust_value: {}'.format(e.message))

	def add_laser_temp_value(self, laser_temp):
		"""
		:param laser_temp:
		:return:
		"""
		if self._analyticsOn and self._current_lasertemp_collector is not None:
			try:
				self._current_lasertemp_collector.addValue(laser_temp)
			except Exception as e:
				self._logger.exception('Error during add_laser_temp_value: {}'.format(e.message))

	def add_laser_intensity_value(self, laser_intensity):
		"""
		Laser intensity.
		:param laser_intensity: 0-255. Zero means laser is off
		"""
		if self._analyticsOn and self._current_intensity_collector is not None:
			try:
				self._current_intensity_collector.addValue(laser_intensity)
			except Exception as e:
				self._logger.exception('Error during add_laser_intensity_value: {}'.format(e.message))

	def _write_dust_log(self, data):
		try:
			if self._analyticsOn:
				self._write_jobevent(ak.FINAL_DUST, payload=data)
		except Exception as e:
			self._logger.exception('Error during write dust_log: {}'.format(e.message))

	def write_fan_rpm_test(self, data):
		try:
			if self._analyticsOn:
				self._write_jobevent(ak.FAN_RPM_TEST, payload=data)
		except Exception as e:
			self._logger.exception('Error during write_fan_50_test: {}'.format(e.message))

	def _init_jsonfile(self):
		open(self._jsonfile, 'w+').close()
		data = {
			ak.LASERHEAD_VERSION: self._getLaserHeadVersion(),
		}
		self._write_deviceinfo(ak.INIT, payload=data)
		self._write_current_software_status()

	def _write_new_line(self):
		if self._analyticsOn:
			try:
				if not os.path.isfile(self._jsonfile):
					self._init_jsonfile()
				with open(self._jsonfile, 'a') as f:
					f.write('\n')
			except Exception as e:
				self._logger.exception('Error while writing newline: {}'.format(e.message), analytics=False)

	def _append_data_to_file(self, data):
		if self._analyticsOn:
			try:
				if not os.path.isfile(self._jsonfile):
					self._init_jsonfile()
				dataString = json.dumps(data, sort_keys=False) + '\n'
				with open(self._jsonfile, 'a') as f:
					f.write(dataString)
			except Exception as e:
				self._logger.exception('Error while writing data: {}'.format(e.message), analytics=False)

	def initial_analytics_procedure(self, consent):
		if consent == 'agree':
			self.analytics_user_permission_change(True)
			self.process_analytics_files()
			FileUploader.upload_now(self._plugin)

		elif consent == 'disagree':
			self.analytics_user_permission_change(False)
			self.delete_analytics_files()

	def delete_analytics_files(self):
		self._logger.info("Deleting analytics files...")
		folder = ak.ANALYTICS_FOLDER
		for analytics_file in os.listdir(folder):
			file_path = os.path.join(folder, analytics_file)
			try:
				if os.path.isfile(file_path) and "analytics" in analytics_file:
					os.unlink(file_path)
					self._logger.info('File deleted: {file}'.format(file=file_path))
			except Exception as e:
				self._logger.exception('Error when deleting file {file}: {error}'.format(file=file_path, error=e))

	def process_analytics_files(self):
		self._logger.info("Processing analytics files...")
		folder = ak.ANALYTICS_FOLDER
		for analytics_file in os.listdir(folder):
			file_path = os.path.join(folder, analytics_file)
			try:
				if os.path.isfile(file_path) and "analytics" in analytics_file:
					# open + remove file_names + save
					for idx, line in enumerate(fileinput.input(file_path, inplace=1)):
						line = re.sub(r"\"filename\": \"[^\"]+\"", "", line)
						sys.stdout.write(line)
					self._logger.info('File processed: {file}'.format(file=file_path))
			except Exception as e:
				self._logger.exception(
					'Error when processing line {line} of file {file}: {e}'.format(line=idx, file=file_path, e=e))
