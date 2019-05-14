import os
import time
import yaml

from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint.events import Events as OctoPrintEvents
from octoprint_mrbeam.mrbeam_events import MrBeamEvents

# singleton
_instance = None
def usageHandler(plugin):
	global _instance
	if _instance is None:
		_instance = UsageHandler(plugin)
	return _instance


class UsageHandler(object):
	def __init__(self, plugin):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.analytics.usage")
		self._plugin = plugin
		self._event_bus = plugin._event_bus
		self._settings = plugin._settings
		self._plugin_version = plugin._plugin_version
		self._device_serial = plugin.getSerialNum()

		self.start_time_total = -1
		self.start_time_air_filter = -1
		self.start_time_laserhead = -1

		analyticsfolder = os.path.join(self._settings.getBaseFolder("base"), self._settings.get(['analytics','folder']))
		if not os.path.isdir(analyticsfolder):
			os.makedirs(analyticsfolder)
		self._storage_file = os.path.join(analyticsfolder, self._settings.get(['analytics','usage_filename']))
		self._backup_file =  os.path.join(analyticsfolder, self._settings.get(['analytics','usage_backup_filename']))

		self._usage_data = None
		self._load_usage_data()
		self._subscribe()
		self.log_usage()

	def log_usage(self):
		self._logger.info("Usage: total: {}, current laser head: {} - {}".format( \
			self._get_duration_humanreadable(self._usage_data['total']['job_time']), \
			# self._get_duration_humanreadable(self._usage_data['air_filter']['job_time']), \
			self._get_duration_humanreadable(self._usage_data['laser_heads'][-1]['job_time']), \
			self._usage_data))

	def _subscribe(self):
		self._event_bus.subscribe(OctoPrintEvents.PRINT_STARTED, self.event_start)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_PAUSED, self.event_write) # cooling breaks also send a regular pause event
		self._event_bus.subscribe(OctoPrintEvents.PRINT_DONE, self.event_stop)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_FAILED, self.event_stop)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_CANCELLED, self.event_stop)
		self._event_bus.subscribe(MrBeamEvents.PRINT_PROGRESS, self.event_write)

	def event_start(self, event, payload):
		self._load_usage_data()
		self.start_time_total = self._usage_data['total']['job_time']
		self.start_time_laserhead = self._usage_data['laser_heads'][-1]['job_time']

		# Initialize air_filter in case it wasn't stored already --> From the total usage
		if 'air_filter' not in self._usage_data:
			self._usage_data['air_filter'] = {}
			self._usage_data['air_filter']['complete'] = self._usage_data['total']['complete']
			self._usage_data['air_filter']['job_time'] = self._usage_data['total']['job_time']
			self._logger.info("Initializing air filter usage time: {usage}".format(usage=self._usage_data['air_filter']['job_time']))
		self.start_time_air_filter = self._usage_data['air_filter']['job_time']

	def event_write(self, event, payload):
		if self.start_time_total >= 0:
			self._set_time(payload['time'])

	def event_stop(self, event, payload):
		if self.start_time_total >= 0 :
			self._set_time(payload['time'])
			self.start_time_total = -1
			self.start_time_air_filter = -1
			self.start_time_laserhead = -1

	def _set_time(self, job_duration):
		if job_duration is not None and job_duration > 0.0:
			self._usage_data['total']['job_time'] = self.start_time_total + job_duration
			self._usage_data['laser_heads'][-1]['job_time'] = self.start_time_laserhead + job_duration
			self._usage_data['air_filter']['job_time'] = self.start_time_air_filter + job_duration
			self._write_usage_data()

	def reset_air_filter_usage(self):
		self._usage_data['air_filter']['job_time'] = 0
		self.start_time_air_filter = -1
		self._write_usage_data()

	def get_air_filter_usage(self):
		if 'air_filter' in self._usage_data:
			return self._usage_data['air_filter']['job_time']
		else:
			return 0

	def _load_usage_data(self):
		success = False
		recovery_try = False
		if os.path.isfile(self._storage_file):
			try:
				data = None
				with open(self._storage_file, 'r') as stream:
					data = yaml.safe_load(stream)
				if self._validate_data(data):
					self._usage_data = data
					success = True
					self._write_usage_data(file=self._backup_file)
			except:
				self._logger.error("Can't read _storage_file file: %s", self._storage_file)

		if not success:
			self._logger.warn("Trying to recover from _backup_file file: %s", self._backup_file)
			recovery_try = True
			if os.path.isfile(self._backup_file):
				try:
					data = None
					with open(self._backup_file, 'r') as stream:
						data = yaml.safe_load(stream)
					if self._validate_data(data):
						data['restored'] = data['restored'] + 1 if 'restored' in data else 1
						self._usage_data = data
						success = True
						self._write_usage_data()
						self._logger.info("Recovered from _backup_file file. Yayy!")
				except:
					self._logger.error("Can't read _backup_file file.")

		if not success:
			self._logger.warn("Resetting usage data. (marking as incomplete)")
			self._usage_data = self._get_usage_data_template()
			if recovery_try:
				self._write_usage_data()


	def _write_usage_data(self, file=None):
		self._usage_data['version'] = self._plugin_version
		self._usage_data['ts'] = time.time()
		self._usage_data['serial'] = self._device_serial
		file = self._storage_file if file is None else file
		try:
			with open(file, 'w') as outfile:
				yaml.dump(self._usage_data, outfile, default_flow_style=False)
		except:
			self._logger.exception("Can't write file %s due to an exception: ", file)

	def _get_usage_data_template(self):
		return {
			'total': {
				'job_time': 0.0,
				'complete': self._plugin.isFirstRun(),
			},
			'air_filter': {
				'job_time': 0.0,
				'complete': self._plugin.isFirstRun(),
			},
			'laser_heads': [
				{
					'job_time': 0.0,
					'complete': self._plugin.isFirstRun()
				}
			],
			'first_write': time.time(),
			'restored': 0,
			'version': '0.0.0',
			'ts': 0.0,
			'serial': self._device_serial
		}

	def _validate_data(self, data):
		return (data is not None \
		        and len(data) > 0 \
		        and 'version' in data \
		        and 'ts' in data \
		        and 'serial' in data \
		        and 'total' in data \
		        and len(data['total']) > 0 \
		        and 'job_time' in data['total'] \
		        and 'laser_heads' in data \
		        and len(data['laser_heads']) > 0 \
		        and 'job_time' in data['laser_heads'][-1])

	def _get_duration_humanreadable(self, seconds):
		seconds = seconds if seconds else 0
		m, s = divmod(seconds, 60)
		h, m = divmod(m, 60)
		return "%d:%02d:%02d" % (h, m, s)

