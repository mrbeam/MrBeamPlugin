#!/usr/bin/env python

import requests
import os
import threading

try:
	from octoprint_mrbeam.mrb_logger import mrb_logger
except:
	import logging

TOKEN_URL = "https://europe-west1-mrb-analytics.cloudfunctions.net/get_upload_tocken"
UPLOAD_URL_TEMPLATE = "https://storage-upload.googleapis.com/{bucket}"

DELETE_FILES_AFTER_UPLOAD = True


class FileUploader:
	STATUS_INIT = 'init'
	STATUS_VERIFY = 'verify'
	STATUS_GET_TOKEN = 'get_token'
	STATUS_UPLOAD = 'upload_file'
	STATUS_REMOVE = 'remove_file'
	STATUS_DONE = 'done'

	def __init__(self, plugin, directory, file, upload_type, lock_file=None, unlock_file=None):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.analytics.uploader")
		self._plugin = plugin
		self.directory = directory
		self.file = file
		self.upload_type = upload_type
		self.delete_on_success = DELETE_FILES_AFTER_UPLOAD
		self.err_state = False
		self.worker = None
		self.lock_file = lock_file
		self.unlock_file = unlock_file

		self.status = dict(
			file=self.file,
			status=None,
			succ=None,
			err=None,
			remote_name=None,
		)

		self.start_uploader_thread()

	def is_active(self):
		return self.worker is not None and self.worker.isAlive()

	def start_uploader_thread(self):
		if self.worker is None or not self.worker.isAlive():
			self.worker = threading.Thread(target=self.upload_and_delete_file)
			self.worker.name = self.__class__.__name__  # Gets the name of the current class
			self.worker.daemon = True  # !!!!
			self.worker.start()
		return self

	def upload_and_delete_file(self):
		self._logger.debug("{} upload starting...".format(self.upload_type))
		self.status['state'] = self.STATUS_INIT
		self.lock_file()

		try:
			if self.file_exists():
				token_data = self.get_token()
				self.upload_file(token_data)
				self.remove_file()
				self._successful_upload_end()

			else:
				self._unsuccessful_upload_end('{} does not exist'.format(self.file))

		except Exception as e:
			self._unsuccessful_upload_end(e)

	def _successful_upload_end(self):
		self.status['state'] = self.STATUS_DONE
		self.status['succ'] = True
		self.unlock_file()

		self._logger.info('###################### SUCCESS!')
		self._logger.info('{up_type} file upload successful! - Status: {status}'.format(
			up_type=self.upload_type,
			status=self.status))

	def _unsuccessful_upload_end(self, err):
		self.status['err'] = err
		self.status['succ'] = False
		self.unlock_file()

		self._logger.info('###################### OH NO!')
		self._logger.exception('{up_type} file upload was not successful: {err} - Status: {status}'.format(
			up_type=self.upload_type,
			err=err,
			status=self.status))

	def get_token(self):
		self.status['state'] = self.STATUS_GET_TOKEN

		try:
			params = self._get_system_properties()
			params['type'] = self.upload_type

			r = requests.get(TOKEN_URL, params=params)
			if r.status_code == requests.codes.ok:
				token_data = r.json()
				self.status['remote_name'] = token_data.get('key', None)
			else:
				raise Exception('status_code {}'.format(r.status_code))

			return token_data

		except requests.ConnectionError as ce:
			raise Exception('ConnectionError during get_token: {}'.format(ce))

		except Exception as e:
			raise Exception('Exception during get_token: {}'.format(e))

	def upload_file(self, token_data):
		self.status['state'] = self.STATUS_UPLOAD

		try:
			upload_url = UPLOAD_URL_TEMPLATE.format(bucket=token_data['bucket'])
			post_params = token_data['request_params']
			files = {'file': open(self.file, 'rb')}

			r = requests.post(upload_url, data=post_params, files=files)
			if r.status_code not in (requests.codes.ok, requests.codes.no_content):
				raise Exception('status_code {}'.format(r.status_code))

			self._logger.info('{} uploaded!'.format(self.file))

		except Exception as e:
			raise Exception('Exception during upload_file: {}'.format(e))

	def remove_file(self):
		self.status['state'] = self.STATUS_REMOVE

		try:
			if self.delete_on_success:
				os.remove(self.file)
				self._logger.debug('{} removed!'.format(self.file))
			else:
				new_file = os.path.join(os.path.dirname(self.file), '_{}'.format(os.path.basename(self.file)))
				os.rename(self.file, new_file)
				self._logger.debug('{} file renamed to: {}'.format(self.upload_type, new_file))
		except Exception as e:
			raise Exception('Exception during remove_file: {}'.format(e))

	def file_exists(self):
		exists = True
		self.status['state'] = self.STATUS_VERIFY
		if not os.path.isfile(self.file):
			self.status['err'] = 'File not found'
			exists = False
		return exists

	def _get_system_properties(self):
		return dict(
			env=self._plugin.get_env(),
			version=self._plugin.get_plugin_version(),
			name=self._plugin.getHostname(),
			serial=self._plugin.getSerialNum(),
		)


# todo iratxe: test + private methods
class AnalyticsFileUploader(FileUploader):
	_instance = None

	def __init__(self, plugin):
		self._settings = plugin._settings
		self._analytics_handler = plugin.analytics_handler

		FileUploader.__init__(
			self,
			plugin,
			directory=self._analytics_handler.analytics_folder,
			file=self._analytics_handler.analytics_file,
			upload_type='analytics',
			lock_file=self._analytics_handler.pause_analytics_writer,
			unlock_file=self._analytics_handler.resume_analytics_writer,
		)

	@staticmethod
	def upload_now(plugin):
		if AnalyticsFileUploader._instance is None or not AnalyticsFileUploader._instance.is_active():
			mrb_logger("octoprint.plugins.mrbeam.analytics.uploader").info('############################# UPLOAD NOW!')  # todo iratxe
			AnalyticsFileUploader._instance = AnalyticsFileUploader(plugin)
			AnalyticsFileUploader._instance.start_uploader_thread()
			return
