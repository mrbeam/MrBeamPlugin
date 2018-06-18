import time
import json
import os.path
from datetime import datetime
from value_collector import ValueCollector

from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint.events import Events as OctoPrintEvents
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from analytics_keys import AnalyticsKeys as ak

# singleton
_instance = None
def analyticsHandler(plugin):
	global _instance
	if _instance is None:
		_instance = AnalyticsHandler(plugin._event_bus, plugin._settings)
	return _instance

def existing_analyticsHandler():
	"""
	Returns AnalyticsHandler instance only if it's already initialized. None otherwise
	:return: None or AnalyticsHandler instance
	"""
	global _instance
	return _instance


class AnalyticsHandler(object):
	def __init__(self, event_bus, settings):
		self._event_bus = event_bus
		self._settings = settings

		self._logger = mrb_logger("octoprint.plugins.mrbeam.analyticshandler")

		self._analyticsOn = self._settings.get(['analytics','job_analytics'])
		self._camAnalyticsOn = self._settings.get(['analytics','cam_analytics'])

		self._current_job_id = None
		self._isJobPaused = False
		self._isCoolingPaused = False
		self._isJobDone = False

		self._current_dust_collector = None
		self._current_cam_session_id = None
		self._current_intensity_collector = None
		self._current_lasertemp_collector = None

		self._storedConversions = list()

		self._jobevent_log_version = 3
		self._conversion_log_version = 2
		self._deviceinfo_log_version = 2
		self._dust_log_version = 2
		self._cam_event_log_version = 2

		analyticsfolder = os.path.join(self._settings.getBaseFolder("base"), self._settings.get(['analytics','folder']))
		if not os.path.isdir(analyticsfolder):
			os.makedirs(analyticsfolder)

		self._jsonfile = os.path.join(analyticsfolder, self._settings.get(['analytics','filename']))
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
		self._event_bus.subscribe(MrBeamEvents.PRINT_PROGRESS, self._event_print_progress)
		self._event_bus.subscribe(MrBeamEvents.LASER_COOLING_PAUSE, self._event_laser_cooling_pause)
		self._event_bus.subscribe(MrBeamEvents.LASER_COOLING_RESUME, self._event_laser_cooling_resume)
		self._event_bus.subscribe(MrBeamEvents.LASER_JOB_DONE, self._event_laser_job_done)
		self._event_bus.subscribe(OctoPrintEvents.STARTUP, self._event_startup)
		self._event_bus.subscribe(OctoPrintEvents.SHUTDOWN, self._event_shutdown)


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
		days_passed = (now_date-lm_date).days

		return days_passed

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

	def _event_startup(self,event,payload):
		self._write_deviceinfo(ak.STARTUP)

	def _event_shutdown(self,event,payload):
		self._write_deviceinfo(ak.SHUTDOWN)

	def write_flash_grbl(self, from_version, to_version, succesful):
		payload = dict(
			from_version=from_version,
			to_version=to_version,
			succesful=succesful)
		self._write_deviceinfo(ak.FLASH_GRBL, payload=payload)


	def _event_print_started(self, event, payload):
		filename = os.path.basename(payload['file'])
		self._current_job_id = 'j_{}_{}'.format(self._getSerialNumber(),time.time())
		self._init_collectors()
		self._isJobPaused = False
		self._isCoolingPaused = False
		self._isJobDone = False
		self._write_conversion_details()
		self._write_jobevent(ak.PRINT_STARTED, {ak.FILENAME: filename})

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
		if not self._isJobPaused: #prevent multiple printPaused events per Job
			self._write_jobevent(ak.PRINT_PAUSED, payload={ak.JOB_DURATION: int(round(payload['time']))})
			self._isJobPaused = True

	def _event_print_resumed(self, event, payload):
		if self._isJobPaused:  #prevent multiple printResume events per Job
			self._write_jobevent(ak.PRINT_RESUMED, payload={ak.JOB_DURATION: int(round(payload['time']))})
			self._isJobPaused = False

	def _event_print_done(self, event, payload):
		if not self._isJobDone:
			self._isJobDone = True #prevent two jobDone events per Job
			self._write_jobevent(ak.PRINT_DONE, payload={ak.JOB_DURATION: int(round(payload['time']))})
			self._write_collectors()

	def _write_collectors(self):
		self._write_jobevent(ak.DUST_SUM,payload=self._current_dust_collector.getSummary())
		self._write_jobevent(ak.INTENSITY_SUM,payload=self._current_intensity_collector.getSummary())
		self._write_jobevent(ak.LASERTEMP_SUM, payload=self._current_lasertemp_collector.getSummary())

	def _cleanup(self):
		self._current_job_id = None
		self._current_dust_collector = None
		self._current_intensity_collector = None
		self._current_lasertemp_collector = None

	def _event_laser_job_done(self, event, payload):
		if self._current_job_id is not None:
			self._write_jobevent(ak.LASERJOB_DONE)
			self._cleanup()

	def _event_print_failed(self, event, payload):
		if self._current_job_id is not None:
			self._write_jobevent(ak.PRINT_FAILED, payload={ak.JOB_DURATION: int(round(payload['time']))})
			self._write_collectors()
			self._cleanup()

	def _event_print_cancelled(self, event, payload):
		if self._current_job_id is not None:
			self._write_jobevent(ak.PRINT_CANCELLED, payload={ak.JOB_DURATION: int(round(payload['time']))})
			self._write_collectors()
			self._cleanup()

	def _event_print_progress(self, event, payload):
		data = {
			ak.PROGRESS_PERCENT: payload['progress'],
			ak.PROGRESS_LASER_TEMPERATURE: self._current_lasertemp_collector.get_latest_value(),
			ak.PROGRESS_LASER_INTENSITY: self._current_intensity_collector.get_latest_value(),
			ak.PROGRESS_DUST_VALUE: self._current_dust_collector.get_latest_value(),
			ak.JOB_DURATION: int(round(payload['time']))
		}
		self._write_jobevent(ak.PRINT_PROGRESS, data)

	def _event_laser_cooling_pause(self, event, payload):
		if not self._isCoolingPaused:
			data = {
				ak.LASERTEMP : None
			}
			if self._current_lasertemp_collector:
				data[ak.LASERTEMP] = self._current_lasertemp_collector.get_latest_value()
			self._write_jobevent(ak.COOLING_START,payload=data)
			self._isCoolingPaused = True

	def _event_laser_cooling_resume(self, event, payload):
		if self._isCoolingPaused:
			data = {
				ak.LASERTEMP : None
			}
			if self._current_lasertemp_collector:
				data[ak.LASERTEMP] = self._current_lasertemp_collector.get_latest_value()
			self._write_jobevent(ak.COOLING_DONE,payload=data)
			self._isCoolingPaused = False

	def write_cam_update(self,newMarkers,newCorners):
		try:
			if self._camAnalyticsOn:
				data = {
					ak.MARKERS:newMarkers,
					ak.CORNERS:newCorners
				}
				self.write_cam_event(ak.CAM_CALIBRATION, payload=data)
		except Exception as e:
			self._logger.error('Error during write_cam_update: {}'.format(e.message))

	def store_conversion_details(self, details):
		try:
			if self._analyticsOn:
				if 'engrave' in details and details['engrave'] == True and 'raster' in details:
					eventname = ak.CONV_ENGRAVE
					data = {
						'svgDPI': details['svgDPI']
					}
					data.update(details['raster'])
					self._store_conversion_details(eventname,payload=data)
					# self._write_jobevent(eventname,payload=data)

				if 'vector' in details and details['vector'] != []:
					eventname = ak.CONV_CUT
					for color_settings in details['vector']:
						data = {
							'svgDPI': details['svgDPI']
						}
						data.update(color_settings)
						self._store_conversion_details(eventname,payload=data)
						# self._write_jobevent(eventname,payload=data)
		except Exception as e:
			self._logger.error('Error during store_conversion_details: {}'.format(e.message))

	def _store_conversion_details(self,eventname,payload=None):
		data = {
			ak.SERIALNUMBER: self._getSerialNumber(),
			ak.TYPE: ak.JOB_EVENT,
			ak.VERSION: self._conversion_log_version,
			ak.EVENT: eventname,
			ak.TIMESTAMP: time.time(),
			ak.JOB_ID: None
		}
		if payload is not None:
			data.update(payload)
		self._storedConversions.append(data)


	def _write_conversion_details(self):
		try:
			for d in self._storedConversions:
				# TODO Check Magic Number 10min Q: How long can a conversion be stored for one job?
				if time.time() - d[ak.TIMESTAMP] < 600:
					d[ak.JOB_ID] = self._current_job_id
				self._append_data_to_file(d)
			self._storedConversions = list()
		except Exception as e:
			self._logger.error('Error during write_conversion_details: {}'.format(e.message))

	def _write_deviceinfo(self,event,payload=None):
		try:
			data = dict()
			# TODO add data validation/preparation here
			if payload is not None:
				data[ak.DATA] = payload
			self._write_event(ak.DEVICE_EVENT, event, self._deviceinfo_log_version, payload=data)
		except Exception as e:
			self._logger.error('Error during write_device_info: {}'.format(e.message))

	def _write_jobevent(self,event,payload=None):
		try:
			#TODO add data validation/preparation here
			data = dict(job_id = self._current_job_id)

			if event in (ak.LASERTEMP_SUM,ak.INTENSITY_SUM):
				data[ak.LASERHEAD_VERSION] = self._getLaserHeadVersion()

			if payload is not None:
				data[ak.DATA] = payload

			_jobevent_type = ak.JOB_EVENT
			self._write_event(_jobevent_type, event, self._jobevent_log_version, payload=data)
		except Exception as e:
			self._logger.error('Error during write_jobevent: {}'.format(e.message))

	def update_cam_session_id(self, lid_state):
		if self._camAnalyticsOn:
			if lid_state == 'lid_opened':
				self._current_cam_session_id = 'c_{}_{}'.format(self._getSerialNumber(),time.time())

	def write_pic_prep_event(self,payload=None):
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

				self._write_event(ak.CAM_EVENT, ak.PIC_PREP, self._cam_event_log_version, payload=data)
		except Exception as e:
			self._logger.error('Error during write_cam_event: {}'.format(e.message))

	def write_cam_event(self, eventname, payload=None):
		try:
			if self._camAnalyticsOn:
				data = dict()

				if payload is not None:
					data[ak.DATA] = payload

				self._write_event(ak.CAM_EVENT, eventname, self._cam_event_log_version, payload=data)
		except Exception as e:
			self._logger.error('Error during write_cam_event: {}'.format(e.message))

	def _write_event(self, typename, eventname, version, payload=None):
		try:
			data = {
				ak.SERIALNUMBER: self._getSerialNumber(),
				ak.TYPE: typename,
				ak.VERSION: version,
				ak.EVENT: eventname,
				ak.TIMESTAMP: time.time()
			}
			if payload is not None:
				data.update(payload)
			self._append_data_to_file(data)
		except Exception as e:
			self._logger.error('Error during _write_event: {}'.format(e.message))

	def write_final_dust(self,dust_start, dust_start_ts, dust_end, dust_end_ts):
		"""
		Sends dust values after print_done (the final dust profile). This is to check how fast dust is getting less in the machine
		and to check for filter full later.
		:param dust_start: dust_value at state print_done
		:param dust_start_ts: timestamp of dust_value at state print done
		:param dust_end: dust_value at job_done
		:param dust_end_ts: timestamp at dust_value at job_done
		:return:
		"""
		dust_duration = round(dust_end_ts - dust_start_ts,4)
		dust_difference = round(dust_end - dust_start,5)
		dust_per_time =  dust_difference / dust_duration
		self._logger.debug("dust extraction time {} from {} to {} (difference: {},gradient: {})".format(dust_duration, dust_start, dust_end,dust_difference, dust_per_time))

		data = {
			ak.DUST_START : dust_start,
			ak.DUST_END : dust_end,
			ak.DUST_START_TS : dust_start_ts,
			ak.DUST_END_TS : dust_end_ts,
			ak.DUST_DURATION : dust_duration,
			ak.DUST_DIFF : dust_difference,
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
				self._logger.error('Error during add_dust_value: {}'.format(e.message))

	def add_laser_temp_value(self,laser_temp):
		"""
		:param laser_temp:
		:return:
		"""
		if self._analyticsOn and self._current_lasertemp_collector is not None:
			try:
				self._current_lasertemp_collector.addValue(laser_temp)
			except Exception as e:
				self._logger.error('Error during add_laser_temp_value: {}'.format(e.message))

	def add_laser_intensity_value(self, laser_intensity):
		"""
		Laser intensity.
		:param laser_intensity: 0-255. Zero means laser is off
		"""
		if self._analyticsOn and self._current_intensity_collector is not None:
			try:
				self._current_intensity_collector.addValue(laser_intensity)
			except Exception as e:
				self._logger.error('Error during add_laser_intensity_value: {}'.format(e.message))

	def _write_dust_log(self, data):
		try:
			if self._analyticsOn:
				self._write_jobevent(ak.FINAL_DUST,payload=data)
		except Exception as e:
			self._logger.error('Error during write dust_log: {}'.format(e.message))

	def _init_jsonfile(self):
		open(self._jsonfile, 'w+').close()
		data = {
			ak.HOSTNAME: self._getHostName(),
			ak.SERIALNUMBER: self._getSerialNumber(),
			ak.LASERHEAD_VERSION: self._getLaserHeadVersion()
		}
		self._write_deviceinfo(ak.INIT,payload=data)
		self._write_current_software_status()

	def _append_data_to_file(self, data):
		try:
			if not os.path.isfile(self._jsonfile):
				self._init_jsonfile()
			dataString = json.dumps(data) + '\n'
			with open(self._jsonfile, 'a') as f:
				f.write(dataString)
		except Exception as e:
			self._logger.error('Error during init json: {}'.format(e.message))
