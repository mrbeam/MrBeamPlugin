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
from threading import Timer, Thread
from Queue import Queue

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
	QUEUE_MAXSIZE = 100

	def __init__(self, plugin):
		self._plugin = plugin
		self._event_bus = plugin._event_bus
		self._settings = plugin._settings
		self._laserhead_handler = laserheadHandler(plugin)  # TODO IRATXE: This is still not initialized in the plugin
		self._snr = plugin.getSerialNum()

		self._logger = mrb_logger("octoprint.plugins.mrbeam.analytics.analyticshandler")

		self._analytics_enabled = self._settings.get(['analyticsEnabled'])
		if self._analytics_enabled is None:
			self._no_choice_made = True
		else:
			self._no_choice_made = False

		self._session_id = "{uuid}@{serial}".format(serial=self._snr, uuid=uuid.uuid4().hex)

		self._current_job_id = None
		self._is_job_paused = False
		self._is_cooling_paused = False
		self._is_job_done = False

		self._current_dust_collector = None
		self._current_cam_session_id = None
		self._current_intensity_collector = None
		self._current_lasertemp_collector = None
		self._current_cpu_data = None
		self._current_job_time_estimation = None

		self._analytics_log_version = 8  # bumped in 0.3.2.1 TODO IRATXE: move iwo

		self.event_waiting_for_terminal_dump = None

		self._logger.info("Analytics analyticsEnabled: %s, sid: %s", self._analytics_enabled, self._session_id)

		self.analytics_folder = os.path.join(self._settings.getBaseFolder("base"),
											 self._settings.get(['analytics', 'folder']))
		if not os.path.isdir(self.analytics_folder):
			os.makedirs(self.analytics_folder)

		# It uploads any previous analytics, unless the user didn't make a choice yet
		if not self._no_choice_made:
			FileUploader.upload_now(self._plugin)

		self._jsonfile = os.path.join(self.analytics_folder, self._settings.get(['analytics', 'filename']))

		self._shutdown_signaled = False  # TODO IRATXE: keep or not

		self._analytics_queue = Queue(maxsize=self.QUEUE_MAXSIZE)
		self._analytics_writer = Thread(target=self._write_queue_to_analyitcs_file)
		if self._analytics_enabled:
			self._activate_analytics()

	def shutdown(self, *args):  # TODO IRATXE: keep or not?
		self._logger.debug("shutdown() args: %s", args)
		global _instance
		_instance = None
		self._shutdown_signaled = True

	def _activate_analytics(self):
		# if not os.path.isfile(self._jsonfile):
		# 	self._init_jsonfile()

		# Restart queue if the analytics were disabled before
		if not self._no_choice_made:
			self._analytics_queue = Queue(self.QUEUE_MAXSIZE)
		else:
			self._no_choice_made = False

		# Start writer thread
		self._analytics_writer.daemon = True  # TODO IRATXE: keep or not?
		self._analytics_writer.start()

		# Subscribe to OctoPrint and Mr Beam events
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
		self._event_bus.subscribe(MrBeamEvents.ANALYTICS_DATA, self._add_other_plugin_data)
		self._event_bus.subscribe(MrBeamEvents.JOB_TIME_ESTIMATED, self._event_job_time_estimated)

	def analytics_user_permission_change(self, analytics_enabled):
		self._logger.info("analytics user permission change: analyticsEnabled=%s", analytics_enabled)

		if analytics_enabled:
			self._analytics_enabled = True
			self._settings.set_boolean(["analyticsEnabled"], True)
			self._activate_analytics()
			self._add_device_event(ak.ANALYTICS_ENABLED, payload=dict(enabled=True))
		else:
			# can not log this since the user just disagreed
			# self._add_device_event(ak.ANALYTICS_ENABLED, payload=dict(enabled=False))
			self._analytics_enabled = False
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
			component=component or self._plugin._identifier,
			component_version=component_version or self._plugin._plugin_version
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

		if wait_for_terminal_dump:  # If it is a e.g. GRBL error, we will have to wait some time for the whole dump
			self.event_waiting_for_terminal_dump = dict(
				payload=payload,
			)
		else:
			self._add_log_event(ak.EVENT_LOG, payload=payload, analytics=False)

	def log_terminal_dump(self, dump):  # Will be used with e.g. GRBL errors
		if self.event_waiting_for_terminal_dump is not None:
			payload = self.event_waiting_for_terminal_dump['payload']
			payload['terminal_dump'] = dump
			self._add_log_event(ak.EVENT_LOG, payload=payload, analytics=False)
			self.event_waiting_for_terminal_dump = None
		else:
			self._logger.warn(
				"log_terminal_dump() called but no foregoing event tracked. self.event_waiting_for_terminal_dump is "
				"None. ignoring this dump.")

	def add_cpu_log(self, temp, throttle_alerts):
		try:
			data = {'temp': temp,
					'throttle_alerts': throttle_alerts}
			self._add_log_event(ak.LOG_CPU, payload=data)
		except Exception as e:
			self._logger.exception('Error during add_cpu_log: {}'.format(e.message), analytics=True)

	def add_camera_session(self, errors):
		try:
			self._logger.info(errors)
			success = True
			if errors:
				success = False
			data = {
				'success': success,
				'err': errors,
			}
			self._add_log_event(ak.CAMERA, payload=data)

		except Exception as e:
			self._logger.exception('Error during log_camera_error: {}'.format(e.message), analytics=True)

	def add_frontend_event(self, event, payload=None):
		try:
			self._add_frontend_event(event, payload=payload)
		except Exception as e:
			self._logger.exception('Error during add_frontend_event: {}'.format(e.message), analytics=True)

	def add_os_health_log(self, data):
		try:
			self._add_log_event(ak.OS_HEALTH, payload=data)
		except Exception as e:
			self._logger.exception('Error during add_frontend_event: {}'.format(e.message), analytics=True)

	def _init_event_timers(self):
		# disk_space --> 3s
		t1 = Timer(self.DISK_SPACE_TIMER, self._add_disk_space)
		t1.start()

		# ips --> 15s
		t2 = Timer(self.IP_ADDRESSES_TIMER, self._add_ip_addresses)
		t2.start()

		# http_self_check task --> 20s
		t3 = Timer(self.SELF_CHECK_TIMER, self._add_http_self_check_event)
		t3.start()

		# internet_connection --> 25s
		t4 = Timer(self.INTERNET_CONNECTION_TIMER, self._add_internet_connection_event)
		t4.start()

	def _event_startup(self, event, payload):
		# self._add_new_line()
		self._add_to_queue('\n')
		payload = {
			ak.LASERHEAD_SERIAL: self._laserhead_handler.get_current_used_lh_data()['serial'],
			ak.ENV: self._plugin.get_env(),
			ak.USERS: len(self._plugin._user_manager._users)
		}
		self._add_device_event(ak.STARTUP, payload=payload)
		self._init_event_timers()

	def _event_shutdown(self, event, payload):
		self._add_device_event(ak.SHUTDOWN)

	def add_grbl_flash_event(self, from_version, to_version, successful, err=None):
		payload = dict(
			from_version=from_version,
			to_version=to_version,
			succesful=successful,
			err=err)
		self._add_device_event(ak.FLASH_GRBL, payload=payload)

	def add_mrbeam_usage(self, usage_data):
		self._add_device_event(ak.MRBEAM_USAGE, payload=usage_data)

	def _add_http_self_check_event(self):
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

			self._add_device_event(ak.HTTP_SELF_CHECK, payload=payload)

		except:
			self._logger.exception('Exception when performing the http self check')

	def _add_internet_connection_event(self):
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
			self._add_device_event(ak.INTERNET_CONNECTION, payload=payload)
		except:
			self._logger.exception('Exception while performing the internet check')

	def _add_ip_addresses(self):
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

			self._add_device_event(ak.IPS, payload=payload)

		except:
			self._logger.exception('Exception when recording the IP addresses')

	def _add_disk_space(self):
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
			self._add_device_event(ak.DISK_SPACE, payload=disk_space)

		except:
			self._logger.exception('Exception when saving info about the disk space')

	def add_laserhead_info(self):
		try:
			lh = self._laserhead_handler.get_current_used_lh_data()
			settings = self._laserhead_handler.get_correction_settings()
			laserhead_info = {
				ak.LASERHEAD_SERIAL: lh['serial'],
				ak.POWER_65: lh['info']['p_65'],
				ak.POWER_75: lh['info']['p_75'],
				ak.POWER_85: lh['info']['p_85'],
				ak.CORRECTION_FACTOR: lh['info']['correction_factor'],
				ak.CORRECTION_ENABLED: settings['correction_enabled'],
				ak.CORRECTION_OVERRIDE: settings['correction_factor_override'],
			}
			self._add_device_event(ak.LASERHEAD_INFO, payload=laserhead_info)

		except:
			self._logger.exception('Exception when saving info about the laserhead')

	def _event_print_started(self, event, payload):
		# If there's no job_id, it may be a gcode file (no slicing), so we have to start the job here
		if not self._current_job_id:
			self._init_new_job()
		self._current_cpu_data = Cpu(state='laser', repeat=True)
		self._init_collectors()
		self._is_job_paused = False
		self._is_cooling_paused = False
		self._is_job_done = False
		self._add_job_event(ak.PRINT_STARTED)

	def _init_collectors(self):
		self._current_dust_collector = ValueCollector('DustColl')
		self._current_intensity_collector = ValueCollector('IntensityColl')
		self._current_lasertemp_collector = ValueCollector('TempColl')

	def _event_print_paused(self, event, payload):
		# TODO add how it has been paused (lid_opened during job, frontend, onebutton)
		"""
		Cooling: payload holds some information if it was a cooling_pause or not. Lid/Button: Currently there is no
		way to know other than checking the current state: _mrbeam_plugin_implementation._ioBeam
		.is_interlock_closed()
		"""
		if not self._is_job_paused:  # prevent multiple printPaused events per Job
			self._add_job_event(ak.PRINT_PAUSED, payload={ak.JOB_DURATION: int(round(payload['time']))})
			self._is_job_paused = True

	def _event_print_resumed(self, event, payload):
		if self._is_job_paused:  # prevent multiple printResume events per Job
			self._add_job_event(ak.PRINT_RESUMED, payload={ak.JOB_DURATION: int(round(payload['time']))})
			self._is_job_paused = False

	def _event_print_done(self, event, payload):
		if not self._is_job_done:
			self._is_job_done = True  # prevent two jobDone events per Job
			self._add_job_event(ak.PRINT_DONE, payload={ak.JOB_DURATION: int(round(payload['time'])),
														ak.JOB_TIME_ESTIMATION: int(
															 round(self._current_job_time_estimation))})
			self._add_collector_details()
			self._add_cpu_data(dur=payload['time'])

	def _add_collector_details(self):
		lh_info = {
			ak.LASERHEAD_VERSION: None,  # TODO should read from _laserhead_handler()
			ak.LASERHEAD_SERIAL: self._laserhead_handler.get_current_used_lh_data()['serial'],
		}

		self._add_job_event(ak.DUST_SUM, payload=self._current_dust_collector.getSummary())
		self._add_job_event(ak.INTENSITY_SUM, payload=self._current_intensity_collector.getSummary().update(lh_info))
		self._add_job_event(ak.LASERTEMP_SUM, payload=self._current_lasertemp_collector.getSummary().update(lh_info))

	def _add_cpu_data(self, dur=None):
		payload = self._current_cpu_data.get_cpu_data()
		payload['dur'] = dur
		self._add_job_event(ak.CPU_DATA, payload=payload)

	def _cleanup(self):
		self._current_job_id = None
		self._current_dust_collector = None
		self._current_intensity_collector = None
		self._current_lasertemp_collector = None
		self._current_cpu_data = None

	def _event_laser_job_done(self, event, payload):
		if self._current_job_id is not None:
			self._add_job_event(ak.LASERJOB_DONE)
			self._cleanup()
		FileUploader.upload_now(self._plugin, delay=5.0)

	def _event_print_failed(self, event, payload):
		if self._current_job_id is not None:
			self._add_job_event(ak.PRINT_FAILED, payload={ak.JOB_DURATION: int(round(payload['time']))})
			self._add_collector_details()
			self._add_cpu_data(dur=payload['time'])
			self._cleanup()

	def _event_print_cancelled(self, event, payload):
		if self._current_job_id is not None:
			self._add_job_event(ak.PRINT_CANCELLED, payload={ak.JOB_DURATION: int(round(payload['time']))})
			self._add_collector_details()
			self._add_cpu_data(dur=payload['time'])
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
		self._add_job_event(ak.PRINT_PROGRESS, data)

		if self._current_cpu_data:
			self._current_cpu_data.update_progress(payload['progress'])

	def _event_slicing_started(self, event, payload):
		self._init_new_job()
		self._add_job_event(ak.SLICING_STARTED)
		self._current_cpu_data = Cpu(state='slicing', repeat=False)

	def _init_new_job(self):
		self._current_job_id = 'j_{}_{}'.format(self._snr, time.time())
		self._add_job_event(ak.LASERJOB_STARTED)

	def _event_slicing_done(self, event, payload):
		if self._current_cpu_data:
			self._current_cpu_data.record_cpu_data()
			self._add_cpu_data(dur=payload['time'])
		self._add_job_event(ak.SLICING_DONE)

	def _event_laser_cooling_pause(self, event, payload):
		if not self._is_cooling_paused:
			data = {
				ak.LASERTEMP: None
			}
			if self._current_lasertemp_collector:
				data[ak.LASERTEMP] = self._current_lasertemp_collector.get_latest_value()
			self._add_job_event(ak.COOLING_START, payload=data)
			self._is_cooling_paused = True

	def _event_laser_cooling_resume(self, event, payload):
		if self._is_cooling_paused:
			data = {
				ak.LASERTEMP: None
			}
			if self._current_lasertemp_collector:
				data[ak.LASERTEMP] = self._current_lasertemp_collector.get_latest_value()
			self._add_job_event(ak.COOLING_DONE, payload=data)
			self._is_cooling_paused = False

	def _event_job_time_estimated(self, event, payload):
		self._current_job_time_estimation = payload['jobTimeEstimation']

	def _add_other_plugin_data(self, event, event_payload):
		try:
			if 'component' in event_payload and 'type' in event_payload and 'component_version' in event_payload:
				component = event_payload.get('component')
				type = event_payload.get('type')
				if type == ak.EVENT_LOG:
					data = event_payload.get('data', dict())
					data['component'] = component
					data['component_version'] = event_payload.get('component_version')
					self._add_log_event(ak.EVENT_LOG, payload=data)
				else:
					self._logger.warn("Unknown type: '%s' from component %s. payload: %s", type, component,
									  event_payload)
			elif 'plugin' in event_payload and 'event_name' in event_payload:
				plugin = event_payload.get('plugin')
				if plugin:
					eventname = event_payload.get('event_name')
					data = event_payload.get('data', None)
					self._add_event_to_queue(plugin, eventname, payload=dict(data=data))
				else:
					self._logger.warn("Invalid plugin: '%s'. payload: %s", plugin, event_payload)
			else:
				self._logger.warn("Invalid payload data in event %s", event)
		except Exception as e:
			self._logger.exception('Exception during _add_other_plugin_data: {}'.format(e.message))

	def add_iobeam_message_log(self, iobeam_version, message):
		data = dict(
			version=iobeam_version,
			message=message
		)
		self._add_log_event(ak.IOBEAM, payload=data)

	def add_ui_render_call_event(self, host, remote_ip, referrer, language):
		try:
			data = dict(
				host=host,
				remote_ip=remote_ip,
				referrer=referrer,
				language=language
			)
			self._add_event_to_queue(ak.TYPE_CONNECTIVITY_EVENT, ak.EVENT_UI_RENDER_CALL, payload=dict(data=data))
		except Exception as e:
			self._logger.exception('Exception during add_ui_render_call_event: {}'.format(e.message))

	def add_client_opened_event(self, remote_ip):
		try:
			data = dict(
				remote_ip=remote_ip
			)
			self._add_event_to_queue(ak.TYPE_CONNECTIVITY_EVENT, ak.EVENT_CLIENT_OPENED, payload=dict(data=data))
		except Exception as e:
			self._logger.exception('Exception during add_client_opened_event: {}'.format(e.message))

	def add_connections_state(self, connections):
		try:
			self._add_event_to_queue(ak.TYPE_CONNECTIVITY_EVENT, ak.CONNECTIONS_STATE, payload=dict(data=connections))
		except Exception as e:
			self._logger.exception('Exception during add_connections_state: {}'.format(e.message))

	def add_software_channel_switch_event(self, old_channel, new_channel):
		try:
			data = {
				ak.OLD_CHANNEL: old_channel,
				ak.NEW_CHANNEL: new_channel,
			}

			self._add_event_to_queue(ak.TYPE_DEVICE_EVENT, ak.SW_CHANNEL_SWITCH, payload=data)

		except Exception as e:
			self._logger.exception('Error during add_software_channel_switch_event: {}'.format(e.message))

	# TODO IRATXE: can we take this info from the backend direct
	def add_conversion_details(self, details):
		try:
			if 'material' in details:
				data = {
					'advanced_settings': details['advanced_settings']
				}
				data.update(details['material'])
				self._add_job_event(ak.LASER_JOB, payload=details['material'])  # TODO IRATXE: this event name does not make sense anymore

			# "conv_eng" line with the engraving parameters
			if 'engrave' in details and details['engrave'] and 'raster' in details:
				eng_settings = details['raster']

				data = {
					'svgDPI': details['svgDPI'],
					'mpr_black': self._calculate_mpr_value(eng_settings.get('intensity_black'),
														   eng_settings.get('speed_black')),
					'mpr_white': self._calculate_mpr_value(eng_settings.get('intensity_white'),
														   eng_settings.get('speed_white')),
				}
				data.update(eng_settings)
				self._add_job_event(ak.CONV_ENGRAVE, payload=data)

			# One or many "conv_cut" lines with the cutting parameters
			if 'vector' in details and details['vector']:
				event_name = ak.CONV_CUT

				for color_settings in details['vector']:
					data = {
						'svgDPI': details['svgDPI'],
						'mpr': self._calculate_mpr_value(color_settings.get('intensity'),
														 color_settings.get('feedrate'), color_settings.get('passes')),
					}
					data.update(color_settings)
					self._add_job_event(ak.CONV_CUT, payload=data)

			# One or many "design_file" lines with the design details
			if 'design_files' in details and details['design_files']:
				event_name = ak.DESIGN_FILE
				for design_file in details['design_files']:
					data = {}
					data.update(design_file)
					self._add_job_event(ak.DESIGN_FILE, payload=data)

		except Exception as e:
			self._logger.exception('Error during add_conversion_details: {}'.format(e.message))

	# TODO IRATXE: change to converter?
	@staticmethod
	def _calculate_mpr_value(intensity, speed, passes=1):
		if intensity and speed and passes:
			mpr = round(float(intensity) / float(speed) * int(passes), 2)
		else:
			mpr = None

		return mpr

	def _add_device_event(self, event, payload=None):
		self._add_event_to_queue(ak.TYPE_DEVICE_EVENT, event, payload=payload)

	def _add_log_event(self, event, payload=None, analytics=False):
		self._add_event_to_queue(ak.TYPE_LOG_EVENT, event, payload=payload, analytics=analytics)

	def _add_frontend_event(self, event, payload=None):
		self._add_event_to_queue(ak.TYPE_FRONTEND, event, payload=payload, analytics=True)

	def _add_job_event(self, event, payload=None):
		self._add_event_to_queue(ak.TYPE_JOB_EVENT, event, payload=payload)

	def _add_connectivity_event(self, event, payload):
		self._add_event_to_queue(ak.TYPE_CONNECTIVITY_EVENT, event, payload=payload)

	def _add_event_to_queue(self, event_type, event_name, payload=None, analytics=False):
		try:
			data = dict()
			if isinstance(payload, dict):
				data = payload

			event = {
				ak.SERIALNUMBER: self._snr,
				ak.TYPE: event_type,
				ak.VERSION: self._analytics_log_version,
				ak.EVENT: event_name,
				ak.TIMESTAMP: time.time(),
				ak.NTP_SYNCED: self._plugin.is_time_ntp_synced(),
				ak.SESSION_ID: self._session_id,
				ak.VERSION_MRBEAM_PLUGIN: self._plugin._plugin_version,
				ak.SOFTWARE_TIER: self._settings.get(["dev", "software_tier"]),
				ak.DATA: data,
			}

			if event_type == ak.TYPE_JOB_EVENT:
				event[ak.JOB_ID] = self._current_job_id

			self._add_to_queue(event)

		except Exception as e:
			self._logger.error('Error during _add_event_to_queue: {}'.format(e.message), analytics=analytics)

	def _add_to_queue(self, element):
		try:
			self._analytics_queue.put(element)
			self._logger.info('################## QUEUE: {}'.format(self._analytics_queue.qsize()))
		except Queue.Full:
			self._logger.info('Analytics queue max size reached ({}). Reinitializing...'.format(self.QUEUE_MAXSIZE))
			self._analytics_queue = Queue(maxsize=self.QUEUE_MAXSIZE)

	def add_final_dust_details(self, dust_start, dust_start_ts, dust_end, dust_end_ts):
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
		self._add_dust_log(data)
		self._add_job_event(ak.FINAL_DUST, payload=data)

	def collect_dust_value(self, dust_value):
		"""
		:param dust_value:
		:return:
		"""
		if self._current_dust_collector is not None:
			try:
				self._current_dust_collector.addValue(dust_value)
			except Exception as e:
				self._logger.exception('Error during collect_dust_value: {}'.format(e.message))

	def collect_laser_temp_value(self, laser_temp):
		"""
		:param laser_temp:
		:return:
		"""
		if self._current_lasertemp_collector is not None:
			try:
				self._current_lasertemp_collector.addValue(laser_temp)
			except Exception as e:
				self._logger.exception('Error during collect_laser_temp_value: {}'.format(e.message))

	def collect_laser_intensity_value(self, laser_intensity):
		"""
		Laser intensity.
		:param laser_intensity: 0-255. Zero means laser is off
		"""
		if self._current_intensity_collector is not None:
			try:
				self._current_intensity_collector.addValue(laser_intensity)
			except Exception as e:
				self._logger.exception('Error during save_laser_intensity_value: {}'.format(e.message))

	def add_fan_rpm_test(self, data):
		try:
			self._add_job_event(ak.FAN_RPM_TEST, payload=data)
		except Exception as e:
			self._logger.exception('Error during write_fan_50_test: {}'.format(e.message))

	def _init_json_file(self):
		open(self._jsonfile, 'w+').close()
		self._add_device_event(ak.INIT, payload={})

	# -------- WRITER THREAD (queue --> analytics file) ----------------------------------------------------------------
	def _write_queue_to_analyitcs_file(self):
		# while not self._shutdown_signaled: TODO IRATXE: keep or not
		while self._analytics_enabled:
			try:
				if not os.path.isfile(self._jsonfile):
					self._init_json_file()

				with open(self._jsonfile, 'a') as f:
					while not self._analytics_queue.empty():
						data = self._analytics_queue.get()
						data_string = json.dumps(data, sort_keys=False) + '\n'
						f.write(data_string)
						if 'e' in data:
							self._logger.info('################## WRITE -- {}'.format(data['e']))
						else:
							self._logger.info('################## WRITE -- {}'.format(data))

				time.sleep(0.1)

			except Exception as e:
				self._logger.exception('Error while writing data: {}'.format(e.message), analytics=False)

		self._logger.info('######################### SHUTDOOOOOOOWN')

	# -------- INITIAL ANALYTICS PROCEDURE -----------------------------------------------------------------------------
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
		folder = self.analytics_folder
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
		folder = self.analytics_folder
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
