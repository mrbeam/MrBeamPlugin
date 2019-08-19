import netifaces
import requests
import os
from threading import Timer

from analytics_keys import AnalyticsKeys as ak
from octoprint_mrbeam.mrb_logger import mrb_logger


class TimerHandler:
	DISK_SPACE_TIMER = 3.0
	IP_ADDRESSES_TIMER = 15.0
	SELF_CHECK_TIMER = 20.0
	INTERNET_CONNECTION_TIMER = 25.0

	SELF_CHECK_USER_AGENT = 'MrBeamPlugin self check'

	def __init__(self):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.analytics.timerhandler")

		self._timers = []

	def start_timers(self):
		try:
			self._timers = []
			self._timers.append(Timer(self.DISK_SPACE_TIMER, self._disk_space))
			self._timers.append(Timer(self.IP_ADDRESSES_TIMER, self._ip_addresses))
			self._timers.append(Timer(self.SELF_CHECK_TIMER, self._http_self_check))
			self._timers.append(Timer(self.INTERNET_CONNECTION_TIMER, self._internet_connection))

			for timer in self._timers:
				timer.start()

		except RuntimeError as e:
			self._logger.exception('Exception during start_timers: {}'.format(e))

	def cancel_timers(self):
		try:
			for timer in self._timers:
				timer.cancel()

		except RuntimeError as e:
			self._logger.exception('Exception during cancel_timers: {}'.format(e))

	def _http_self_check(self):
		try:
			payload = dict()
			interfaces = netifaces.interfaces()
			err = None
			elapsed_seconds = None

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
							ak.Device.Request.IP: ip,
							ak.Device.Request.RESPONSE: response,
							ak.Device.Request.ELAPSED_S: elapsed_seconds,
							ak.Device.ERROR: err,
						}

			_mrbeam_plugin_implementation._analytics_handler.add_http_self_check(payload)

		except Exception as e:
			self._logger.exception('Exception during the _http_self_check: {}'.format(e))

	def _internet_connection(self):
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
				ak.Device.Request.RESPONSE: response,
				ak.Device.ERROR: err,
				ak.Device.Request.CONNECTION: connection,
			}
			_mrbeam_plugin_implementation._analytics_handler.add_internet_connection(payload)

		except Exception as e:
			self._logger.exception('Exception during the _internet_connection check: {}'.format(e))

	def _ip_addresses(self):
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

			_mrbeam_plugin_implementation._analytics_handler.add_ip_addresses(payload)

		except Exception as e:
			self._logger.exception('Exception during the _ip_addresses check: {}'.format(e))

	def _disk_space(self):
		try:
			statvfs = os.statvfs('/')
			total_space = statvfs.f_frsize * statvfs.f_blocks
			available_space = statvfs.f_frsize * statvfs.f_bavail  # Available space for non-super users
			used_percent = round((total_space - available_space) * 100 / total_space)

			disk_space = {
				ak.Device.Usage.TOTAL_SPACE: total_space,
				ak.Device.Usage.AVAILABLE_SPACE: available_space,
				ak.Device.Usage.USED_SPACE: used_percent,
			}
			_mrbeam_plugin_implementation._analytics_handler.add_disk_space(disk_space)

		except Exception as e:
			self._logger.exception('Exception during the _disk_space check: {}'.format(e))
