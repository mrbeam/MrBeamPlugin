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

		if plugin.lh['serial']:
			self._laser_head_serial = plugin.lh['serial']
		else:
			self._laser_head_serial = 'no_serial'

		self.start_time_total = -1
		self.start_time_laser_head = -1
		self.start_time_prefilter = -1
		self.start_time_carbon_filter = -1
		self.start_time_gantry = -1

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
			self._get_duration_humanreadable(self._usage_data['laser_head'][self._laser_head_serial]['job_time']), \
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

		# Initialize prefilter in case it wasn't stored already --> From the total usage
		if 'prefilter' not in self._usage_data:
			self._usage_data['prefilter'] = {}
			self._usage_data['prefilter']['complete'] = self._usage_data['total']['complete']
			self._usage_data['prefilter']['job_time'] = self._usage_data['total']['job_time']
			self._logger.info("Initializing prefilter usage time: {usage}".format(
				usage=self._usage_data['prefilter']['job_time']))

		# Initialize carbon_filter in case it wasn't stored already --> From the total usage
		if 'carbon_filter' not in self._usage_data:
			self._usage_data['carbon_filter'] = {}
			self._usage_data['carbon_filter']['complete'] = self._usage_data['total']['complete']
			self._usage_data['carbon_filter']['job_time'] = self._usage_data['total']['job_time']
			self._logger.info("Initializing carbon filter usage time: {usage}".format(
				usage=self._usage_data['carbon_filter']['job_time']))

		# Initialize new laser heads
		self._logger.info("################# IRATXE event_start {}".format(self._laser_head_serial))
		if 'laser_head' not in self._usage_data:
			self._usage_data['laser_head'] = {}
			# TODO IRATXE: remove laser_heads?

		if self._laser_head_serial not in self._usage_data['laser_head']:
			self._usage_data['laser_head'][self._laser_head_serial] = {}
			if self._laser_head_serial == 'no_serial':
				self._usage_data['laser_head'][self._laser_head_serial]['complete'] = self._usage_data['total']['complete']
				self._usage_data['laser_head'][self._laser_head_serial]['job_time'] = self._usage_data['total']['job_time']
			else:
				# TODO IRATXE: what if it's an old laserhead?
				self._usage_data['laser_head'][self._laser_head_serial]['complete'] = True
				self._usage_data['laser_head'][self._laser_head_serial]['job_time'] = 0

			self._logger.info("Initializing laser head ({lh}) usage time: {usage}".format(
				lh=self._laser_head_serial,
				usage=self._usage_data['laser_head'][self._laser_head_serial]['job_time']))

		# Initialize gantry in case it wasn't stored already --> From the total usage
		if 'gantry' not in self._usage_data:
			self._usage_data['gantry'] = {}
			self._usage_data['gantry']['complete'] = self._usage_data['total']['complete']
			self._usage_data['gantry']['job_time'] = self._usage_data['total']['job_time']
			self._logger.info("Initializing gantry usage time: {usage}".format(
				usage=self._usage_data['gantry']['job_time']))

		self.start_time_prefilter = self._usage_data['prefilter']['job_time']
		self.start_time_carbon_filter = self._usage_data['carbon_filter']['job_time']
		self.start_time_laser_head = self._usage_data['laser_head'][self._laser_head_serial]['job_time']
		self.start_time_gantry = self._usage_data['gantry']['job_time']

	def event_write(self, event, payload):
		if self.start_time_total >= 0:
			self._set_time(payload['time'])

	def event_stop(self, event, payload):
		if self.start_time_total >= 0:
			self._set_time(payload['time'])
			self.start_time_total = -1
			self.start_time_laser_head = -1
			self.start_time_prefilter = -1
			self.start_time_carbon_filter = -1
			self.start_time_gantry = -1

	def _set_time(self, job_duration):
		if job_duration is not None and job_duration > 0.0:
			self._usage_data['total']['job_time'] = self.start_time_total + job_duration
			self._usage_data['laser_head'][self._laser_head_serial]['job_time'] = self.start_time_laser_head + job_duration
			self._usage_data['prefilter']['job_time'] = self.start_time_prefilter + job_duration
			self._usage_data['carbon_filter']['job_time'] = self.start_time_prefilter + job_duration
			self._usage_data['gantry']['job_time'] = self.start_time_prefilter + job_duration
			self._write_usage_data()

	def reset_prefilter_usage(self):
		self._usage_data['prefilter']['job_time'] = 0
		self.start_time_prefilter = -1
		self._write_usage_data()

	def reset_carbon_filter_usage(self):
		self._usage_data['carbon_filter']['job_time'] = 0
		self.start_time_prefilter = -1
		self._write_usage_data()

	def reset_gantry_usage(self):
		self._usage_data['gantry']['job_time'] = 0
		self.start_time_prefilter = -1
		self._write_usage_data()

	def get_prefilter_usage(self):
		if 'prefilter' in self._usage_data:
			return self._usage_data['prefilter']['job_time']
		else:
			return 0

	def get_carbon_filter_usage(self):
		if 'carbon_filter' in self._usage_data:
			return self._usage_data['carbon_filter']['job_time']
		else:
			return 0

	def get_laser_head_usage(self):
		if 'laser_head' in self._usage_data and self._laser_head_serial in self._usage_data['laser_head']:
			return self._usage_data['laser_head'][self._laser_head_serial]['job_time']
		else:
			return 0

	def get_gantry_usage(self):
		if 'gantry' in self._usage_data:
			return self._usage_data['gantry']['job_time']
		else:
			return 0

	def get_total_usage(self):
		if 'total' in self._usage_data:
			return self._usage_data['total']['job_time']
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
			'prefilter': {
				'job_time': 0.0,
				'complete': self._plugin.isFirstRun(),
			},
			'carbon_filter': {
				'job_time': 0.0,
				'complete': self._plugin.isFirstRun(),
			},
			'gantry': {
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

