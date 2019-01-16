#!/usr/bin/env python

import requests
import time
import os
import sys
import threading
try:
	from octoprint_mrbeam.mrb_logger import mrb_logger
except:
	import logging
from octoprint_mrbeam.util.cmd_exec import exec_cmd


TOKEN_URL           = "https://europe-west1-mrb-analytics.cloudfunctions.net/get_upload_tocken"
UPLOAD_URL_TEMPLATE = "https://storage-upload.googleapis.com/{bucket}"





class FileUploader(object):

	STATUS_QUEUED =     'queued'
	STATUS_INIT =       'init'
	STATUS_VERIFY =     'verify'
	STATUS_GET_TOKEN =  'get_token'
	STATUS_UPLOAD =     'upload_file'
	STATUS_REMOVE =     'remove_file'
	STATUS_DONE =       'done'

	FILE_UPLOAD_DELAY_AFTER_INIT_DEFAULT = 15.0
	MIN_LIN_COUNT_TO_UPLOAD = 10


	def __init__(self,
	             analytics_dir,
	             delete_on_success=False,
	             delay=None,
	             analytics_files_prefix=None,
	             analytics_files_suffix=None,
	             logger=None):
		self._logger = logger or mrb_logger("octoprint.plugins.mrbeam.analytics.uploader")
		self.delay = delay or self.FILE_UPLOAD_DELAY_AFTER_INIT_DEFAULT
		self.analytics_dir = analytics_dir
		self.analytics_files_prefix = analytics_files_prefix
		self.analytics_files_suffix = analytics_files_suffix
		self.files = []
		self.queued_files = self._get_files_as_array(files)
		self.delete_on_success = delete_on_success
		self.status = {}
		self.err_state = False
		self.worker = None
		self.logrotation_scheduled = False
		self.current_analytics_file = None
		self.is_online = None


	def find_files_for_upload(self):
		files = []
		for f in os.listdir(self.analytics_dir):
			if (self.analytics_files_prefix is None or f.startswith(self.analytics_files_prefix)) \
					and (self.analytics_files_suffix is None or f.endswith(self.analytics_files_suffix)):
				full = os.path.join(self.analytics_dir, f)
				files.append(full)
		self._logger.debug("Files found in folder '%s': (%s) %s", self.analytics_dir, len(files), files)
		self.add_files(files)


	def add_files(self, files=[]):
		files = self._get_files_as_array(files)
		self._logger.debug("Adding files for upload: (%s) %s", len(files), files)
		self._init_status(files)
		self.queued_files.extend(files)
		self.run()


	def schedule_logrotation_and_startover(self, current_analytics_file=None):
		self.logrotation_scheduled = True
		self.current_analytics_file = current_analytics_file


	def run(self,  delay=None):
		if self.worker is None or not self.worker.isAlive():
			self.worker = threading.Thread(target=self._run_threaded, args=[delay])
			self.worker.name = 'AnalyticsUploader'
			self.worker.daemon = True # !!!!
			self.worker.start()
		return self


	def _run_threaded(self, delay):
		try:
			my_delay = self.delay if delay is None else delay
			time.sleep(self.delay)
			self.files = self.queued_files
			self.queued_files = []

			for my_file in self.files:
				self.set_status(my_file, state=self.STATUS_INIT)

			self._logger.debug("Files upload starting... files: (%s) %s", len(self.files), self.files)

			for my_file in self.files:
				succ = self.handle_single_file(my_file)

			self.files = []
			if self.queued_files:
				# if more files were added manually
				self._run_threaded(delay=0.0)
			elif self.logrotation_scheduled:
				self.logrotation_scheduled = False
				if self.test_online:
					self._logger.debug("We're online: logrotating and uploading current analytics file.")
					self._do_analytics_logrotate()
					self.find_files_for_upload()
					self._run_threaded(delay=0.0)
				else:
					self._logger.debug("We're not online, not logrotating current analytics file.")
			else:
				self.log_status()

		except:
			self._logger.exception("Exception in FileUploader.run_threaded() ")


	def handle_single_file(self, my_file):
		succ = None
		self._logger.debug("Handling file: {}".format(self.get_status(my_file)))

		self.verify_file(my_file)
		if self.is_state_ok(my_file):

			token_data = self.get_token(my_file)
			if self.is_state_ok(my_file):

				self.upload_file(my_file, token_data)
				if self.is_state_ok(my_file):

					self.remove_file(my_file)
					if self.is_state_ok(my_file):
						# done
						self.set_status(my_file, state=self.STATUS_DONE, succ=True)

		if self.is_state_ok(my_file):
			succ = True
			self._logger.debug("Handled file successfully: {}".format(self.get_status(my_file)))
		else:
			succ = False
			self._logger.warn("Handled file with error: {}".format(self.get_status(my_file)))

		return succ


	def get_token(self, my_file):
		self.set_status(my_file, state=self.STATUS_GET_TOKEN)

		try:
			params = self._get_system_properties()
			params['type'] = 'analytics'
			r = requests.get(TOKEN_URL, params=params)
			if r.status_code == requests.codes.ok:
				self.is_online = True
				j = r.json()
				if 'key' in j:
					self.set_status(my_file, remote_name=j['key'])
				return j
			else:
				self.is_online = False
				text = r.text if 'text' in r else ''
				err = "get_token failed: {} {}".format(r.status_code, text)
				self.set_status(my_file, succ=False, err=err)
		except Exception as e:
			self._logger.exception("Exception while loading upload_token %s:", my_file)
			err = "get_token for {} failed with exception: {}: {}".format(my_file, type(e).__name__, e)
			self.set_status(my_file, succ=False, err=err)


	def upload_file(self, my_file, token_data):
		self.set_status(my_file, state=self.STATUS_UPLOAD)

		upload_url = UPLOAD_URL_TEMPLATE.format(bucket=token_data['bucket'])
		post_params = token_data['request_params']
		files = {'file': open(my_file, 'rb')}

		try:
			r = requests.post(upload_url, data=post_params, files=files)
			self._logger.debug("Analytics file upload: %s, file: %s", r.status_code, my_file)
			if r.status_code in (requests.codes.ok, requests.codes.no_content):
				self.is_online = True
				return True
			else:
				self.is_online = False
				err = "upload_file failed: {}".format(r.status_code)
				self.set_status(my_file, succ=False, err=err)
		except Exception as e:
			self._logger.exception("Exception while upload_file %s:", my_file)
			err = "upload_file {} failed with exception: {}: {}".format(my_file, type(e).__name__, e)
			self.set_status(my_file, succ=False, err=err)


	def remove_file(self, my_file):
		self.set_status(my_file, state=self.STATUS_REMOVE)

		try:
			if self.delete_on_success:
				os.remove(my_file)
				self._logger.debug("File removed: %s", my_file)
			else:
				new_file = os.path.join(os.path.dirname(my_file), '_{}'.format(os.path.basename(my_file)))
				os.rename(my_file, new_file)
				self._logger.debug("File renamed to: %s", new_file)
		except Exception as e:
			self._logger.exception("Exception while remove_file %s:", my_file)
			err = "remove_file {} failed with exception: {}: {}".format(my_file, type(e).__name__, e)
			self.set_status(my_file, succ=False, err=err)


	def verify_file(self, my_file):
		self.set_status(my_file, state=self.STATUS_VERIFY)
		if not os.path.isfile(my_file) and my_file in self.status:
			self.set_status(my_file, succ=False, err="File not found")


	def test_online(self, force=False):
		res = self.is_online
		if self.is_online is None or force:
			res = False
			try:
				params = self._get_system_properties()
				params['type'] = 'ping'
				r = requests.get(TOKEN_URL, params=params)
				if r.status_code == requests.codes.ok:
					res = True
				else:
					res = False
			except:
				res = False
			self.is_online = res
		return res


	def log_status(self):
		ok = 0
		err = 0
		for k,v in self.status.iteritems():
			if v['succ']:
				ok += 1
			else:
				err += 1
		self._logger.info("Analytics file upload finished. Files: %s (ok: %s, failed: %s) Details: %s", len(self.status), ok, err, self.status)

	def _do_analytics_logrotate(self):
		long_enough = False
		if self.current_analytics_file is not None:
			ca_full = os.path.join(self.analytics_dir, self.current_analytics_file)
			long_enough = self._has_file_more_lines_than(ca_full, self.MIN_LIN_COUNT_TO_UPLOAD)
		if long_enough:
			ok = exec_cmd('sudo logrotate --force /etc/logrotate.d/analytics')
			if not ok:
				self._logger.warn("Unable to logrotate analytics file.")
		else:
			self._logger.debug("Current analytics file too short: not rotating.")


	def _has_file_more_lines_than(self, my_file, max_lines):
		res = False
		if my_file is not None and os.path.isfile(my_file):
			with open(my_file) as f:
				for i, l in enumerate(f):
					if i > max_lines:
						res = True
						break
		return res


	def _get_system_properties(self):
		return dict(env=_mrbeam_plugin_implementation.get_env(),
					version=_mrbeam_plugin_implementation._plugin_version,
					name=_mrbeam_plugin_implementation.getHostname(),
					serial=_mrbeam_plugin_implementation._serial_num
		            )


	def _get_files_as_array(self, files):
		if isinstance(files, basestring):
			files = [files]
		return files


	def _init_status(self, files):
		for my_file in files:
			self.status[my_file] = dict(file=my_file,
			                            status=self.STATUS_QUEUED,
			                            succ=None,
			                            err=None,
			                            remote_name=None,
			                            logrotate_if_online=False)


	def set_status(self, my_file, state=None, succ=None, err=None, remote_name=None, logrotate_if_online=None):
		if state is not None:
			self.status[my_file]['status'] = state
		if succ is not None:
			self.status[my_file]['succ'] = succ
		if err is not None:
			self.status[my_file]['err'] = err
		if remote_name is not None:
			self.status[my_file]['remote_name'] = remote_name
		if logrotate_if_online is not None:
			self.status[my_file]['logrotate_if_online'] = logrotate_if_online


	def get_status(self, my_file):
		return self.status[my_file]


	def is_state_ok(self, my_file):
		return self.status[my_file]['succ'] is not False



def my_callback(success, err=None):
	print("Success: {} {}".format(success, err))




