# coding=utf-8

import netifaces
import requests
import os
from threading import Timer

from analytics_keys import AnalyticsKeys as ak
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.util.cmd_exec import exec_cmd, exec_cmd_output


class TimerHandler:
	DISK_SPACE_TIMER = 3.0
	IP_ADDRESSES_TIMER = 15.0
	SELF_CHECK_TIMER = 20.0
	INTERNET_CONNECTION_TIMER = 25.0
	FS_CHECKSUMS = 3.0

	SELF_CHECK_USER_AGENT = 'MrBeamPlugin self check'

	def __init__(self, plugin):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.analytics.timerhandler")
		self._plugin = plugin

		self._timers = []

	def start_timers(self):
		try:
			self._timers = []
			self._timers.append(Timer(self.DISK_SPACE_TIMER, self._disk_space))
			self._timers.append(Timer(self.IP_ADDRESSES_TIMER, self._ip_addresses))
			self._timers.append(Timer(self.SELF_CHECK_TIMER, self._http_self_check))
			self._timers.append(Timer(self.INTERNET_CONNECTION_TIMER, self._internet_connection))
			self._timers.append(Timer(self.FS_CHECKSUMS, self._fs_checksums))

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
						for tmp in addresses[netifaces.AF_INET]:
							ip = tmp['addr']

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

							if interface not in payload:
								payload[interface] = []
							payload[interface].append({
								ak.Device.Request.IP: ip,
								ak.Device.Request.RESPONSE: response,
								ak.Device.Request.ELAPSED_S: elapsed_seconds,
								ak.Device.ERROR: err,
							})

			self._plugin.analytics_handler.add_http_self_check(payload)

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
			self._plugin.analytics_handler.add_internet_connection(payload)

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
					payload[interface]['IPv4'] = []
					for idx, addr in enumerate(addresses[netifaces.AF_INET]):
						payload[interface]['IPv4'].append(addr['addr'])
				if netifaces.AF_INET6 in addresses:
					payload[interface]['IPv6'] = []
					for idx, addr in enumerate(addresses[netifaces.AF_INET6]):
						payload[interface]['IPv6'].append(addr['addr'])

			self._plugin.analytics_handler.add_ip_addresses(payload)

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
			self._plugin.analytics_handler.add_disk_space(disk_space)

		except Exception as e:
			self._logger.exception('Exception during the _disk_space check: {}'.format(e))

	def _fs_checksums(self):
		try:
			# must end with /
			folders = ['/home/pi/site-packages/octoprint_mrbeam/',
			           '/home/pi/dist-packages/iobeam/',
			           ]
			res = {}

			# self._logger.info("ANDYTEST cmd: %s", exec_cmd_output("which find", shell=True))
			# self._logger.info("ANDYTEST cmd: %s", exec_cmd_output("which md5sum", shell=True))

			for my_folder in folders:
				# self._logger.info("ANDYTEST cmd: %s", exec_cmd_output("ll {}".format(my_folder), shell=True))
				cmd = 'find "{folder}" -type f -exec md5sum {{}} \; | sort -k 2 | md5sum'.format(folder=my_folder)
				# cmd = 'find "{folder}" -type f -exec md5sum {{}} \;'.format(folder=my_folder)
				self._logger.info("ANDYTEST _fs_checksums: cmd: %s", cmd)
				out, code = exec_cmd_output(cmd, shell=True)
				if out:
					res[my_folder] = out.replace("  -", '').strip()
			self._logger.info("ANDYTEST _fs_checksums: %s", res)
		except:
			self._logger.exception("Exception in _fs_checksums(): ")




