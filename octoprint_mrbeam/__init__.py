# coding=utf-8
from __future__ import absolute_import

import __builtin__
import copy
import json
import os
import pprint
import socket
import threading
import time
import shlex
import collections
from subprocess import check_output

import octoprint.plugin
import requests
from flask import request, jsonify, make_response, url_for
from flask.ext.babel import gettext
from octoprint.filemanager import ContentTypeDetector, ContentTypeMapping
from octoprint.server import NO_CONTENT
from octoprint.server.util.flask import restricted_access, get_json_command_from_request, \
	add_non_caching_response_headers, firstrun_only_access
from octoprint.util import dict_merge
from octoprint.settings import settings, default_settings

from octoprint_mrbeam.iobeam.iobeam_handler import ioBeamHandler, IoBeamEvents
from octoprint_mrbeam.iobeam.onebutton_handler import oneButtonHandler
from octoprint_mrbeam.iobeam.interlock_handler import interLockHandler
from octoprint_mrbeam.iobeam.lid_handler import lidHandler
from octoprint_mrbeam.iobeam.temperature_manager import temperatureManager
from octoprint_mrbeam.iobeam.dust_manager import dustManager
from octoprint_mrbeam.analytics.analytics_handler import analyticsHandler
from octoprint_mrbeam.led_events import LedEventListener
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.mrb_logger import init_mrb_logger, mrb_logger
from .profile import laserCutterProfileManager, InvalidProfileError, CouldNotOverwriteError, Profile
from .software_update_information import get_update_information



# this is a easy&simple way to access the plugin and all injections everywhere within the plugin
__builtin__._mrbeam_plugin_implementation = None


class MrBeamPlugin(octoprint.plugin.SettingsPlugin,
                   octoprint.plugin.AssetPlugin,
				   octoprint.plugin.UiPlugin,
                   octoprint.plugin.TemplatePlugin,
				   octoprint.plugin.BlueprintPlugin,
				   octoprint.plugin.SimpleApiPlugin,
				   octoprint.plugin.EventHandlerPlugin,
				   octoprint.plugin.ProgressPlugin,
				   octoprint.plugin.WizardPlugin,
				   octoprint.plugin.SlicerPlugin,
				   octoprint.plugin.ShutdownPlugin):

	# CONSTANTS
	ENV_LOCAL =        "local"
	ENV_LASER_SAFETY = "laser_safety"
	ENV_ANALYTICS =    "analytics"

	LASERSAFETY_CONFIRMATION_STORAGE_URL = 'https://script.google.com/a/macros/mr-beam.org/s/AKfycby3Y1RLBBiGPDcIpIg0LHd3nwgC7GjEA4xKfknbDLjm3v9-LjG1/exec'
	USER_SETTINGS_KEY_MRBEAM = 'mrbeam'
	USER_SETTINGS_KEY_TIMESTAMP = 'ts'
	USER_SETTINGS_KEY_VERSION = 'version'
	USER_SETTINGS_KEY_LASERSAFETY_CONFIRMATION_SENT_TO_CLOUD = ['lasersafety', 'sent_to_cloud']
	USER_SETTINGS_KEY_LASERSAFETY_CONFIRMATION_SHOW_AGAIN = ['lasersafety', 'show_again']



	def __init__(self):
		self.laserCutterProfileManager = None
		self._slicing_commands = dict()
		self._slicing_commands_mutex = threading.Lock()
		self._cancelled_jobs = []
		self._cancelled_jobs_mutex = threading.Lock()
		self._CONVERSION_PARAMS_PATH = "/tmp/conversion_parameters.json"  # TODO add proper path there
		self._cancel_job = False
		self.print_progress_last = -1
		self.slicing_progress_last = -1
		self._logger = mrb_logger("octoprint.plugins.mrbeam")

	def initialize(self):
		init_mrb_logger(self._printer)
		self.laserCutterProfileManager = laserCutterProfileManager()
		self._logger = mrb_logger("octoprint.plugins.mrbeam")
		self._branch = self.getBranch()
		self._hostname = self.getHostname()
		self._octopi_info = self.get_octopi_info()
		self._serial = self.getMrBeamSerial()
		self._do_initial_log()
		try:
			pluginInfo = self._plugin_manager.get_plugin_info("netconnectd")
			if pluginInfo is None:
				self._logger.warn("NetconnectdPlugin not available. Wifi configuration not possible.")
		except Exception as e:
			self._logger.exception("Exception while getting NetconnectdPlugin pluginInfo")

		self._oneButtonHandler = oneButtonHandler(self)
		self._interlock_handler = interLockHandler(self)
		self._lid_handler = lidHandler(self)
		self._analytics_handler = analyticsHandler(self)
		self._led_eventhandler = LedEventListener(self._event_bus, self._printer)
		# start iobeam socket only once other handlers are already inittialized so that we can handle info mesage
		self._ioBeam = ioBeamHandler(self._event_bus, self._settings.get(["dev", "sockets", "iobeam"]))
		self._temperatureManager = temperatureManager()
		self._dustManager = dustManager()


	def _do_initial_log(self):
		msg = "MrBeam Plugin"
		msg += " version:" + self._plugin_version
		msg += ", branch:" + self._branch
		msg += ", host:" + self._hostname
		msg += ", serial:" + self._serial
		msg += ", env:" + self.get_env()
		msg += " ("+self.ENV_LOCAL+':'+self.get_env(self.ENV_LOCAL)
		msg += ","+self.ENV_LASER_SAFETY+':'+self.get_env(self.ENV_LASER_SAFETY)
		msg += ","+self.ENV_ANALYTICS+':'+self.get_env(self.ENV_ANALYTICS)+')'
		msg += ", octopi:" + str(self._octopi_info)
		self._logger.info(msg, terminal=True)

		msg = "MrBeam Lasercutter Profile: %s" % self.laserCutterProfileManager.get_current_or_default()
		self._logger.info(msg, terminal=True)


	def _convert_profiles(self, profiles):
		result = dict()
		for identifier, profile in profiles.items():
			result[identifier] = self._convert_profile(profile)
		return result

	def _convert_profile(self, profile):
		default = self.laserCutterProfileManager.get_default()["id"]
		current = self.laserCutterProfileManager.get_current_or_default()["id"]

		converted = copy.deepcopy(profile)
		converted["resource"] = url_for(".laserCutterProfilesGet", identifier=profile["id"], _external=True)
		converted["default"] = (profile["id"] == default)
		converted["current"] = (profile["id"] == current)
		return converted

	##~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		# Max img size: 2592x1944. Change requires rebuild of lens_correction_*.npz and machine recalibration.
		image_default_width = 2048
		image_default_height = 1536

		return dict(
			current_profile_id="_mrbeam_junior", # yea, this needs to be like this
			svgDPI=90,
			beta_label="",
			dev=dict(
				debug=False, # deprected
				terminalMaxLines = 2000,
				env = "PROD",
				# env_overrides = dict(
				# 	analytics = "DEV",
				# 	laser_safety = "DEV",
				# 	local =  "DEV"
				# ),
				iobeam_disable_warnings = False
			),
			analyticsEnabled=False,  # frontend analytics Mixpanel
			analyticsfolder="analytics",  # laser job analytics base folder (.octoprint/...)
			cam=dict(
				enabled=True,
				image_correction_enabled = True,
				cam_img_width = image_default_width,
				cam_img_height = image_default_height,
				# todo CLEM add NPZ folder and pic_settings, calib output folder etc.
				frontendUrl="/downloads/files/local/cam/beam-cam.jpg",
				localFilePath="cam/beam-cam.jpg",
				localUndistImage="cam/undistorted.jpg",
				keepOriginals=False,
				# TODO: we nee a better and unified solution for our custom paths. Some day...
				correctionSettingsFile='{}/cam/pic_settings.yaml'.format(settings().getBaseFolder('base')),
				correctionTmpFile='{}/cam/last_markers.json'.format(settings().getBaseFolder('base')),
				lensCalibrationFile='{}/cam/lens_correction_{}x{}.npz'.format(settings().getBaseFolder('base'), image_default_width, image_default_height),
			),
			gcode_nextgen = dict(
				enabled = True,
				precision = 0.05,
				optimize_travel = True,
				small_paths_first = True,
				clip_working_area = False
			)
		)

	def on_settings_load(self):
		return dict(
			current_profile_id=self._settings.get(["current_profile_id"]),
			svgDPI=self._settings.get(['svgDPI']),
			analyticsEnabled=self._settings.get(['analyticsEnabled']),
			cam=dict(enabled=self._settings.get(['cam', 'enabled']),
					 frontendUrl=self._settings.get(['cam', 'frontendUrl'])),
			dev=dict(
				env = self._settings.get(['dev', 'env']),
				softwareTier = self._settings.get(["dev", "software_tier"]),
				terminalMaxLines = self._settings.get(['dev', 'terminalMaxLines'])),
			gcode_nextgen=dict(
				enabled = self._settings.get(['gcode_nextgen', 'enabled']),
				precision = self._settings.get(['gcode_nextgen', 'precision']),
				optimize_travel = self._settings.get(['gcode_nextgen', 'optimize_travel']),
				small_paths_first = self._settings.get(['gcode_nextgen', 'small_paths_first']),
				clip_working_area = self._settings.get(['gcode_nextgen', 'clip_working_area'])
			)
		)

	def on_settings_save(self, data):
		if "workingAreaWidth" in data and data["workingAreaWidth"]:
			self._settings.set(["workingAreaWidth"], data["workingAreaWidth"])
		if "zAxis" in data:
			self._settings.set_boolean(["zAxis"], data["zAxis"])
		if "svgDPI" in data:
			self._settings.set_int(["svgDPI"], data["svgDPI"])

		selectedProfile = self.laserCutterProfileManager.get_current_or_default()
		self._settings.set(["current_profile_id"], selectedProfile['id'])

	def on_shutdown(self):
		self._logger.debug("Mr Beam Plugin stopping...")
		self._ioBeam.shutdown()
		self._lid_handler.shutdown()
		self._temperatureManager.shutdown()
		self._dustManager.shutdown()
		time.sleep(2)
		self._logger.info("Mr Beam Plugin stopped.")

	##~~ AssetPlugin mixin

	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/lasercutterprofiles.js","js/mother_viewmodel.js", "js/mrbeam.js","js/color_classifier.js",
				"js/working_area.js", "js/camera.js", "js/lib/snap.svg-min.js", "js/snap-dxf.js", "js/render_fills.js", "js/path_convert.js",
				"js/matrix_oven.js", "js/drag_scale_rotate.js",	"js/convert.js", "js/snap_gc_plugin.js", "js/gcode_parser.js", "js/gridify.js",
				"js/lib/photobooth_min.js", "js/svg_cleaner.js", "js/loginscreen_viewmodel.js",
				"js/wizard_acl.js", "js/netconnectd_wrapper.js", "js/lasersaftey_viewmodel.js",
				"js/ready_to_laser_viewmodel.js", "js/lib/screenfull.min.js","js/settings/camera_calibration.js",
				"js/path_magic.js", "js/lib/simplify.js", "js/lib/clipper.js", "js/laser_job_done_viewmodel.js"],
			css=["css/mrbeam.css", "css/svgtogcode.css", "css/ui_mods.css", "css/quicktext-fonts.css"],
			less=["less/mrbeam.less"]
		)

	##~~ UiPlugin mixin

	def will_handle_ui(self, request):
		# returns True as Mr Beam Plugin should be always displayed
		return True

	def on_ui_render(self, now, request, render_kwargs):
		# if will_handle_ui returned True, we will now render our custom index
		# template, using the render_kwargs as provided by OctoPrint
		from flask import make_response, render_template

		firstRun = render_kwargs['firstRun']

		enable_accesscontrol = self._user_manager.enabled
		accesscontrol_active = enable_accesscontrol and self._user_manager.hasBeenCustomized()

		selectedProfile = self.laserCutterProfileManager.get_current_or_default()
		enable_focus = selectedProfile["focus"]
		safety_glasses = selectedProfile["glasses"]
		# render_kwargs["templates"]["settings"]["entries"]["serial"][1]["template"] = "settings/serialconnection.jinja2"

		wizard = render_kwargs["templates"] is not None and bool(render_kwargs["templates"]["wizard"]["order"])

		if render_kwargs["templates"]["wizard"]["entries"]:
			if render_kwargs["templates"]["wizard"]["entries"]["firstrunstart"]:
				render_kwargs["templates"]["wizard"]["entries"]["firstrunstart"][1]["template"] = "wizard/firstrun_start.jinja2"
			if render_kwargs["templates"]["wizard"]["entries"]["firstrunend"]:
				render_kwargs["templates"]["wizard"]["entries"]["firstrunend"][1]["template"] = "wizard/firstrun_end.jinja2"

		display_version_string = "{} on {}".format(self._plugin_version, self._hostname)
		if self._branch:
			display_version_string = "{} ({} branch) on {}".format(self._plugin_version, self._branch, self._hostname)

		render_kwargs.update(dict(
							 webcamStream=self._settings.get(["cam", "frontendUrl"]),
							 enableFocus=enable_focus,
							 safetyGlasses=safety_glasses,
							 enableTemperatureGraph=False,
							 enableAccessControl=enable_accesscontrol,
							 accessControlActive=accesscontrol_active,
							 enableSdSupport=False,
							 gcodeMobileThreshold=0,
							 gcodeThreshold=0,
							 wizard=wizard,
							 now=now,
							 beamosVersion= dict(
								number = self._plugin_version,
								branch= self._branch,
								display_version = display_version_string,
							 	image = self._octopi_info),
							 ),
							 env= dict(
								 env=self.get_env(),
								 local=self.get_env(self.ENV_LOCAL),
								 laser_safety=self.get_env(self.ENV_LASER_SAFETY),
								 analytics=self.get_env(self.ENV_ANALYTICS)
							 ),
							 displayName=self.getDisplayName(self._hostname),
							 hostname=self._hostname,
							 serial=self._serial,
							 analyticsEnabled=self._settings.get(["analyticsEnabled"]),
							 beta_label=self._settings.get(['beta_label']),
						 )
		r = make_response(render_template("mrbeam_ui_index.jinja2", **render_kwargs))

		if firstRun:
			r = add_non_caching_response_headers(r)
		return r

	##~~ TemplatePlugin mixin

	def get_template_configs(self):
		result = [
			dict(type='settings', name="SVG Settings", template='settings/svgtogcode_settings.jinja2', suffix="_conversion", custom_bindings=False)
			# disabled in appearance
			# dict(type='settings', name="Serial Connection DEV", template='settings/serialconnection_settings.jinja2', suffix='_serialconnection', custom_bindings=False, replaces='serial')
		 ]
		if not self.is_prod_env('local'):
			result.extend([
				dict(type='settings', name="Machine Profiles DEV", template='settings/lasercutterprofiles_settings.jinja2', suffix="_lasercutterprofiles", custom_bindings=False),
				dict(type='settings', name="Camera Calibration DEV", template='settings/camera_settings.jinja2', suffix="_camera", custom_bindings=True),
        		dict(type='settings', name="Camera Calibration", template='settings/camera_settings.jinja2', suffix="_camera", custom_bindings=True),
			])
		result.extend(self._get_wizard_template_configs())
		return result


	def _get_wizard_template_configs(self):
		required = self._get_subwizard_attrs("_is_", "_wizard_required")
		names = self._get_subwizard_attrs("_get_", "_wizard_name")
		additional = self._get_subwizard_attrs("_get_", "_additional_wizard_template_data")

		result = list()
		for key, method in required.items():
			if not method():
				continue

			if not key in names:
				continue

			name = names[key]()
			if not name:
				continue

			config = dict(type="wizard", name=name, template="wizard/wizard_{}.jinja2".format(key), div="wizard_plugin_corewizard_{}".format(key))
			if key in additional:
				additional_result = additional[key]()
				if additional_result:
					config.update(additional_result)
			result.append(config)

		return result

	#~~ WizardPlugin API

	def is_wizard_required(self):
		# self._logger.info("ANDYTEST is_wizard_required")
        #
		# methods = self._get_subwizard_attrs("_is_", "_wizard_required")
        #
		# result = self._settings.global_get(["server", "firstRun"])
		# if result:
		# 	# don't even go here if firstRun is false
		# 	result = any(map(lambda m: m(), methods.values()))
		# if result:
		# 	self._logger.info("Setup Wizard showing")
		# return result
		return self.isFirstRun()

	def get_wizard_details(self):
		return dict()

	def get_wizard_version(self):
		return 12

	def on_wizard_finish(self, handled):
		self._logger.info("Setup Wizard finished.")
		# map(lambda m: m(handled), self._get_subwizard_attrs("_on_", "_wizard_finish").values())


	# ~~ Wifi subwizard

	def _is_wifi_wizard_required(self):
		result = False
		try:
			pluginInfo = self._plugin_manager.get_plugin_info("netconnectd")
			if pluginInfo is not None:
				status = pluginInfo.implementation._get_status()
				result = not status["connections"]["wifi"]
		except Exception as e:
			self._logger.exception("Exception while reading wifi state from netconnectd:")

		self._logger.debug("_is_wifi_wizard_required() %s", result)
		return result

	def _get_wifi_wizard_details(self):
		return dict()

	def _get_wifi_additional_wizard_template_data(self):
		return dict(mandatory=False, suffix="_wifi")

	def _get_wifi_wizard_name(self):
		return gettext("Wifi Setup")

	# def _on_wifi_wizard_finish(self, handled):
	# 	self._log.info("ANDYTEST _on_wifi_wizard_finish() handled: " + str(handled));

	#~~ ACL subwizard

	def _is_acl_wizard_required(self):
		result = self._user_manager.enabled and not self._user_manager.hasBeenCustomized()
		self._logger.debug("_is_acl_wizard_required() %s", result)
		return result

	def _get_acl_wizard_details(self):
		return dict()

	def _get_acl_additional_wizard_template_data(self):
		return dict(mandatory=False, suffix="_acl")


	def _get_acl_wizard_name(self):
		return gettext("Access Control")

	# def _on_acl_wizard_finish(self, handled):
	# 	self._log.info("ANDYTEST _on_acl_wizard_finish() test handled: " + str(handled));


	# ~~ Saftey subwizard

	def _is_lasersafety_wizard_required(self):
		return True

	def _get_lasersafety_wizard_details(self):
		return dict()

	def _get_lasersafety_additional_wizard_template_data(self):
		return dict(mandatory=False, suffix="_lasersafety")

	def _get_lasersafety_wizard_name(self):
		return gettext("Laser Safety")

	# def _on_acl_wizard_finish(self, handled):
	# 	self._log.info("ANDYTEST _on_acl_wizard_finish() test handled: " + str(handled));




	@octoprint.plugin.BlueprintPlugin.route("/acl", methods=["POST"])
	def acl_wizard_api(self):
		from flask import request
		from octoprint.server.api import NO_CONTENT

		if not(self.isFirstRun() and self._user_manager.enabled and not self._user_manager.hasBeenCustomized()):
			return make_response("Forbidden", 403)

		data = request.values
		if hasattr(request, "json") and request.json:
			data = request.json
		else:
			return make_response("Unable to interprete request", 400)

		if 	"user" in data.keys() and "pass1" in data.keys() and \
				"pass2" in data.keys() and data["pass1"] == data["pass2"]:
			# configure access control
			self._logger.debug("acl_wizard_api() creating admin user: %s", data["user"])
			self._settings.global_set_boolean(["accessControl", "enabled"], True)
			self._user_manager.enable()
			self._user_manager.addUser(data["user"], data["pass1"], True, ["user", "admin"], overwrite=True)
		else:
			return make_response("Unable to interprete request", 400)

		self._settings.save()
		return NO_CONTENT


	@octoprint.plugin.BlueprintPlugin.route("/wifi", methods=["POST"])
	def wifi_wizard_api(self):
		from flask import request
		from octoprint.server.api import NO_CONTENT

		# accept requests only while setup wizard is active
		if not self.isFirstRun() or not self._is_wifi_wizard_required():
			return make_response("Forbidden", 403)

		data = None
		command = None
		try:
			data = request.json
			command = data["command"]
		except:
			return make_response("Unable to interprete request", 400)

		self._logger.debug("wifi_wizard_api() command: %s, data: %s", command,  pprint.pformat(data))

		result = None
		try:
			pluginInfo = self._plugin_manager.get_plugin_info("netconnectd")
			if pluginInfo is None:
				self._logger.warn("wifi_wizard_api() NetconnectdPlugin not available.")
			else:
				result = pluginInfo.implementation.on_api_command(command, data, adminRequired=False)
		except Exception as e:
			self._logger.exception("Exception while executing wifi command '%s' in netconnectd: " +
					   "(This might be totally ok since this plugin throws an exception if we were rejected by the " +
					   "wifi for invalid password or other non-exceprional things.)", command)
			return make_response(e.message, 500)

		self._logger.debug("wifi_wizard_api() result: %s", result)
		if result is None:
			return NO_CONTENT
		return result

	# simpleApiCommand: lasersafety_confirmation; simpleApiCommand: lasersafety_confirmation;
	def lasersafety_wizard_api(self, data):
		from flask.ext.login import current_user
		from octoprint.server.api import NO_CONTENT

		# get JSON from request data, or send user back home
		data = request.values
		if hasattr(request, "json") and request.json:
			data = request.json
		else:
			return make_response("Unable to interprete request", 400)

		# check if username is ok
		username = data.get('username', '')
		if current_user is None \
				or current_user.is_anonymous() \
				or not current_user.is_user() \
				or not current_user.is_active() \
				or current_user.get_name() != username:
			return make_response("Invalid user", 403)

		showAgain = bool(data.get('showAgain', True))

		# see if we nee to send this to the cloud
		submissionDate = self.getUserSetting(username, self.USER_SETTINGS_KEY_LASERSAFETY_CONFIRMATION_SENT_TO_CLOUD, -1)
		force = bool(data.get('force', False))
		needSubmission = submissionDate <= 0 or force
		if needSubmission:
			# get cloud env to use
			debug = self.get_env(self.ENV_LASER_SAFETY)

			payload = {'ts': data.get('ts', ''),
					   'email': data.get('username', ''),
					   'serial': self._serial,
					   'hostname': self._hostname}

			if debug is not None and debug != "PROD":
				payload['debug'] = debug
				self._logger.debug("LaserSafetyNotice - debug flag: %s", debug)

			if force:
				payload['force'] = force
				self._logger.debug("LaserSafetyNotice - force flag: %s", force)

			self._logger.debug("LaserSafetyNotice - cloud request: url: %s, payload: %s",
							   self.LASERSAFETY_CONFIRMATION_STORAGE_URL, payload)

			# actual request
			successfullySubmitted = False
			responseCode = ''
			responseFull = ''
			httpCode = -1
			try:
				r = requests.post(self.LASERSAFETY_CONFIRMATION_STORAGE_URL, data=payload)
				responseCode = r.text.lstrip().split(' ', 1)[0]
				responseFull = r.text
				httpCode = r.status_code
				if responseCode == 'OK' or responseCode == 'OK_DEBUG':
					successfullySubmitted = True
			except Exception as e:
				responseCode = "EXCEPTION"
				responseFull = str(e.args)

			submissionDate = time.time() if successfullySubmitted else -1
			showAgain = showAgain if successfullySubmitted else True
			self.setUserSetting(username, self.USER_SETTINGS_KEY_LASERSAFETY_CONFIRMATION_SENT_TO_CLOUD, submissionDate)
			self.setUserSetting(username, self.USER_SETTINGS_KEY_LASERSAFETY_CONFIRMATION_SHOW_AGAIN, showAgain)

			# and drop a line into the log on info level this is important
			self._logger.info("LaserSafetyNotice: confirmation response: (%s) %s, submissionDate: %s, showAgain: %s, full response: %s",
							  httpCode, responseCode, submissionDate, showAgain, responseFull)
		else:
			self._logger.info("LaserSafetyNotice: confirmation already sent. showAgain: %s", showAgain)
			self.setUserSetting(username, self.USER_SETTINGS_KEY_LASERSAFETY_CONFIRMATION_SHOW_AGAIN, showAgain)

		if needSubmission and not successfullySubmitted:
			return make_response("Failed to submit laser safety confirmation to cloud.", 901)
		else:
			return NO_CONTENT

	#~~ helpers

	def _get_subwizard_attrs(self, start, end, callback=None):
		result = dict()

		for item in dir(self):
			if not item.startswith(start) or not item.endswith(end):
				continue

			key = item[len(start):-len(end)]
			if not key:
				continue

			attr = getattr(self, item)
			if callable(callback):
				callback(key, attr)
			result[key] = attr

		return result


	# helper method to write data to user settings
	# this makes sure it's always written into a mrbeam folder and
	# a last updated timestamp as well as the mrbeam pluin version are added
	def setUserSetting(self, username, key, value):
		if not isinstance(key, list):
			key = [key]
		self._user_manager.changeUserSetting(username, [self.USER_SETTINGS_KEY_MRBEAM] + key, value)
		self._user_manager.changeUserSetting(username, [self.USER_SETTINGS_KEY_MRBEAM, self.USER_SETTINGS_KEY_TIMESTAMP], time.time())
		self._user_manager.changeUserSetting(username, [self.USER_SETTINGS_KEY_MRBEAM, self.USER_SETTINGS_KEY_VERSION], self._plugin_version)

	# reads a value from usersettings mrbeam category
	def getUserSetting(self, username, key, default):
		if not isinstance(key, list):
			key = [key]
		result = self._user_manager.getUserSetting(username, [self.USER_SETTINGS_KEY_MRBEAM] + key)

		if result is None:
			result = default
		return result


	##~~ BlueprintPlugin mixin

	# disable default api key check for all blueprint routes.
	# use @restricted_access, @firstrun_only_access to check permissions
	def is_blueprint_protected(self):
		return False


	@octoprint.plugin.BlueprintPlugin.route("/calibration", methods=["GET"])
	#@firstrun_only_access
	def calibration_wrapper(self):
		from flask import request
		from octoprint.server.api import NO_CONTENT
		from flask import make_response, render_template
		from octoprint.server import debug, LOCALES, VERSION, DISPLAY_VERSION, UI_API_KEY, BRANCH

		display_version_string = "{} on {}".format(self._plugin_version, self._hostname)
		if self._branch:
			display_version_string = "{} ({} branch) on {}".format(self._plugin_version, self._branch, self._hostname)

		render_kwargs = dict(debug=debug,
							firstRun=self.isFirstRun(),
							version=dict(number=VERSION, display=DISPLAY_VERSION, branch=BRANCH),
							uiApiKey=UI_API_KEY,
							templates=dict(tab=[]),
							pluginNames=dict(),
							locales=dict(),
							supportedExtensions=[],
							beamosVersion= dict(
								number = self._plugin_version,
								branch= self._branch,
								display_version = display_version_string,
							 	image = self._octopi_info),
							 env= dict(
								 env=self.get_env(),
								 local=self.get_env(self.ENV_LOCAL),
							 ),
							 displayName=self.getDisplayName(self._hostname),
							 hostname=self._hostname,
							 serial=self._serial,
							 beta_label=self._settings.get(['beta_label']),
							 e='null',
							 gcodeThreshold=0, #legacy
							 gcodeMobileThreshold=0, #legacy
						 )
		r = make_response(render_template("initial_calibration.jinja2", **render_kwargs))

		r = add_non_caching_response_headers(r)
		return r

	### Initial Camera Calibration - START ###
	# The next two calls are needed for first-run and initial camera calibration

	@octoprint.plugin.BlueprintPlugin.route("/take_undistorted_picture", methods=["GET"])
	#@firstrun_only_access
	def takeUndistortedPictureForInitialCalibration(self):
		self._logger.debug("INITIAL TAKE PICTURE")
		self.take_undistorted_picture()
		return NO_CONTENT


	@octoprint.plugin.BlueprintPlugin.route("/send_calibration_markers", methods=["POST"])
	#@firstrun_only_access
	def sendInitialCalibrationMarkers(self):
		if not "application/json" in request.headers["Content-Type"]:
			return make_response("Expected content-type JSON", 400)

		try:
			json_data = request.json
		except JSONBadRequest:
			return make_response("Malformed JSON body in request", 400)

		self._logger.debug("INITIAL camera_calibration_markers() data: {}".format(json_data))


		if not "result" in json_data or not all(k in json_data['result'] for k in ['newCorners','newMarkers']):
			return make_response("No profile included in request", 400)

		self.camera_calibration_markers(json_data)
		return NO_CONTENT

	### Initial Camera Calibration - END ###

	# Laser cutter profiles
	@octoprint.plugin.BlueprintPlugin.route("/profiles", methods=["GET"])
	@restricted_access
	def laserCutterProfilesList(self):
		all_profiles = self.laserCutterProfileManager.get_all()
		return jsonify(dict(profiles=self._convert_profiles(all_profiles)))

	@octoprint.plugin.BlueprintPlugin.route("/profiles", methods=["POST"])
	@restricted_access
	def laserCutterProfilesAdd(self):
		if not "application/json" in request.headers["Content-Type"]:
			return make_response("Expected content-type JSON", 400)

		try:
			json_data = request.json
		except JSONBadRequest:
			return make_response("Malformed JSON body in request", 400)

		if not "profile" in json_data:
			return make_response("No profile included in request", 400)

		base_profile = self.laserCutterProfileManager.get_default()
		if "basedOn" in json_data and isinstance(json_data["basedOn"], basestring):
			other_profile = self.laserCutterProfileManager.get(json_data["basedOn"])
			if other_profile is not None:
				base_profile = other_profile

		if "id" in base_profile:
			del base_profile["id"]
		if "name" in base_profile:
			del base_profile["name"]
		if "default" in base_profile:
			del base_profile["default"]

		new_profile = json_data["profile"]
		make_default = False
		if "default" in new_profile:
			make_default = True
			del new_profile["default"]

		profile = dict_merge(base_profile, new_profile)
		try:
			saved_profile = self.laserCutterProfileManager.save(profile, allow_overwrite=False, make_default=make_default)
		except InvalidProfileError:
			return make_response("Profile is invalid", 400)
		except CouldNotOverwriteError:
			return make_response("Profile already exists and overwriting was not allowed", 400)
		else:
			return jsonify(dict(profile=self._convert_profile(saved_profile)))

	@octoprint.plugin.BlueprintPlugin.route("/profiles/<string:identifier>", methods=["GET"])
	def laserCutterProfilesGet(self, identifier):
		profile = self.laserCutterProfileManager.get(identifier)
		if profile is None:
			return make_response("Unknown profile: %s" % identifier, 404)
		else:
			return jsonify(self._convert_profile(profile))

	@octoprint.plugin.BlueprintPlugin.route("/profiles/<string:identifier>", methods=["DELETE"])
	@restricted_access
	def laserCutterProfilesDelete(self, identifier):
		self.laserCutterProfileManager.remove(identifier)
		return NO_CONTENT

	@octoprint.plugin.BlueprintPlugin.route("/profiles/<string:identifier>", methods=["PATCH"])
	@restricted_access
	def laserCutterProfilesUpdate(self, identifier):
		if not "application/json" in request.headers["Content-Type"]:
			return make_response("Expected content-type JSON", 400)

		try:
			json_data = request.json
		except JSONBadRequest:
			return make_response("Malformed JSON body in request", 400)

		if not "profile" in json_data:
			return make_response("No profile included in request", 400)

		profile = self.laserCutterProfileManager.get(identifier)
		if profile is None:
			profile = self.laserCutterProfileManager.get_default()

		new_profile = json_data["profile"]
		new_profile = dict_merge(profile, new_profile)

		make_default = False
		if "default" in new_profile:
			make_default = True
			del new_profile["default"]

		# edit width and depth in grbl firmware
		### TODO queue the commands if not in locked or operational mode
		if make_default or (self.laserCutterProfileManager.get_current_or_default()['id'] == identifier):
			if self._printer.is_locked() or self._printer.is_operational():
				if "volume" in new_profile:
					if "width" in new_profile["volume"]:
						width = float(new_profile['volume']['width'])
						if identifier == "_mrbeam_senior":
							width *= 2
						width += float(new_profile['volume']['origin_offset_x'])
						self._printer.commands('$130=' + str(width))
						time.sleep(0.1) ### TODO find better solution then sleep
					if "depth" in new_profile["volume"]:
						depth = float(new_profile['volume']['depth'])
						if identifier == "_mrbeam_senior":
							depth *= 2
						depth += float(new_profile['volume']['origin_offset_y'])
						self._printer.commands('$131=' + str(depth))

		new_profile["id"] = identifier

		try:
			saved_profile = self.laserCutterProfileManager.save(new_profile, allow_overwrite=True, make_default=make_default)
		except InvalidProfileError:
			return make_response("Profile is invalid", 400)
		except CouldNotOverwriteError:
			return make_response("Profile already exists and overwriting was not allowed", 400)
		else:
			return jsonify(dict(profile=self._convert_profile(saved_profile)))


	@octoprint.plugin.BlueprintPlugin.route("/generate_calibration_markers_svg", methods=["GET"])
	@restricted_access
	def generateCalibrationMarkersSvg(self):
		profile = self.laserCutterProfileManager.get_current_or_default()
		print profile
		xmin = '0'
		ymin = '0'
		homing_pulloff = 1.1 # TODO get this magic number from the machine profile.
		xmax = str(profile['volume']['width'] - homing_pulloff)
		ymax = str(profile['volume']['depth'] - homing_pulloff)
		svg = """<svg id="calibration_markers-0" viewBox="%(xmin)s %(ymin)s %(xmax)s %(ymax)s" height="%(ymax)smm" width="%(xmax)smm">
		<path id="NE" d="M%(xmax)s %(ymax)sl-20,0 5,-5 -10,-10 10,-10 10,10 5,-5 z" style="stroke:#000000; stroke-width:1px; fill:none;" />
		<path id="NW" d="M%(xmin)s %(ymax)sl20,0 -5,-5 10,-10 -10,-10 -10,10 -5,-5 z" style="stroke:#000000; stroke-width:1px; fill:none;" />
		<path id="SW" d="M%(xmin)s %(ymin)sl20,0 -5,5 10,10 -10,10 -10,-10 -5,5 z" style="stroke:#000000; stroke-width:1px; fill:none;" />
		<path id="SE" d="M%(xmax)s %(ymin)sl-20,0 5,5 -10,10 10,10 10,-10 5,5 z" style="stroke:#000000; stroke-width:1px; fill:none;" />
		</svg>"""  % {'xmin': xmin, 'xmax': xmax, 'ymin': ymin, 'ymax': ymax}

#'name': 'Dummy Laser',
#'volume': {'width': 500.0, 'depth': 390.0, 'height': 0.0, 'origin_offset_x': 1.1, 'origin_offset_y': 1.1},
#'model': 'X', 'id': 'my_default', 'glasses': False}

		target = 'local'
		filename = 'CalibrationMarkers.svg'

		class Wrapper(object):
			def __init__(self, filename, content):
				self.filename = filename
				self.content = content

			def save(self, absolute_dest_path):
				with open(absolute_dest_path, "w") as d:
					d.write(self.content)
					d.close()
		fileObj = Wrapper(filename, svg)
		try:
			self._file_manager.add_file(target, filename, fileObj, links=None, allow_overwrite=True)
		except Exception, e:
			return make_response("Failed to write file. Disk full?", 400)
		else:
			return jsonify(dict(calibration_marker_svg=filename, target=target))


	@octoprint.plugin.BlueprintPlugin.route("/convert", methods=["POST"])
	@restricted_access
	def gcodeConvertCommand(self):
		target = "local"

		# valid file commands, dict mapping command name to mandatory parameters
		valid_commands = {
			"convert": []
		}
		command, data, response = get_json_command_from_request(request, valid_commands)
		if response is not None:
			return response

		appendGcodeFiles = data['gcodeFilesToAppend']
		del data['gcodeFilesToAppend']

		if command == "convert":
			# TODO stripping non-ascii is a hack - svg contains lots of non-ascii in <text> tags. Fix this!
			svg = ''.join(i for i in data['svg'] if ord(i) < 128)  # strip non-ascii chars like €
			del data['svg']
			filename = target + "/temp.svg"

			class Wrapper(object):
				def __init__(self, filename, content):
					self.filename = filename
					self.content = content

				def save(self, absolute_dest_path):
					with open(absolute_dest_path, "w") as d:
						d.write(self.content)
						d.close()

			fileObj = Wrapper(filename, svg)
			self._file_manager.add_file(target, filename, fileObj, links=None, allow_overwrite=True)

			slicer = "svgtogcode"
			slicer_instance = self._slicing_manager.get_slicer(slicer)
			if slicer_instance.get_slicer_properties()["same_device"] and (
						self._printer.is_printing() or self._printer.is_paused()):
				# slicer runs on same device as OctoPrint, slicing while printing is hence disabled
				return make_response("Cannot convert while lasering due to performance reasons".format(**locals()), 409)

			import os
			if "gcode" in data.keys() and data["gcode"]:
				gcode_name = data["gcode"]
				del data["gcode"]
			else:
				name, _ = os.path.splitext(filename)
				gcode_name = name + ".gco"

			# append number if file exists
			name, ext = os.path.splitext(gcode_name)
			i = 1
			while self._file_manager.file_exists(target, gcode_name):
				gcode_name = name + '.' + str(i) + ext
				i += 1

			# prohibit overwriting the file that is currently being printed
			currentOrigin, currentFilename = self._getCurrentFile()
			if currentFilename == gcode_name and currentOrigin == target and (
						self._printer.is_printing() or self._printer.is_paused()):
				make_response("Trying to slice into file that is currently being printed: %s" % gcode_name, 409)

			select_after_slicing = False
			print_after_slicing = False

			#get job params out of data json
			overrides = dict()
			overrides['vector'] = data['vector']
			overrides['raster'] = data['raster']

			with open(self._CONVERSION_PARAMS_PATH, 'w') as outfile:
				json.dump(data, outfile)
				self._logger.info('Wrote job parameters to %s', self._CONVERSION_PARAMS_PATH)

			self._printer.set_colors(currentFilename, data['vector'])

			# callback definition
			def slicing_done(target, gcode_name, select_after_slicing, print_after_slicing, append_these_files):
				# append additioal gcodes
				output_path = self._file_manager.path_on_disk(target, gcode_name)
				with open(output_path, 'ab') as wfd:
					for f in append_these_files:
						path = self._file_manager.path_on_disk(f['origin'], f['name'])
						wfd.write("\n; " + f['name'] + "\n")

						with open(path, 'rb') as fd:
							shutil.copyfileobj(fd, wfd, 1024 * 1024 * 10)

						wfd.write("\nM05\n")  # ensure that the laser is off.
						self._logger.info("Slicing finished: %s" % path)

				if select_after_slicing or print_after_slicing:
					sd = False
					filenameToSelect = self._file_manager.path_on_disk(target, gcode_name)
					printer.select_file(filenameToSelect, sd, True)

			try:
				self._file_manager.slice(slicer, target, filename, target, gcode_name,
										 profile=None,#profile,
										 printer_profile_id=None, #printerProfile,
										 position=None, #position,
										 overrides=overrides,
										 callback=slicing_done,
										 callback_args=[target, gcode_name, select_after_slicing, print_after_slicing,
														appendGcodeFiles])
			except octoprint.slicing.UnknownProfile:
				return make_response("Profile {profile} doesn't exist".format(**locals()), 400)

			location = "test"  # url_for(".readGcodeFile", target=target, filename=gcode_name, _external=True)
			result = {
				"name": gcode_name,
				"origin": "local",
				"refs": {
					"resource": location,
					"download": url_for("index", _external=True) + "downloads/files/" + target + "/" + gcode_name
				}
			}

			r = make_response(jsonify(result), 202)
			r.headers["Location"] = location
			return r

		return NO_CONTENT

	@octoprint.plugin.BlueprintPlugin.route("/cancel", methods=["POST"])
	@restricted_access
	def cancelSlicing(self):
		self._cancel_job = True
		return NO_CONTENT

	##~~ SimpleApiPlugin mixin

	def get_api_commands(self):
		return dict(
			position=["x", "y"],
			feedrate=["value"],
			intensity=["value"],
			passes=["value"],
			lasersafety_confirmation=[],
			camera_calibration_markers=["result"],
			ready_to_laser=["ready"],
			debug_event=["event"],
			take_undistorted_picture=[]
		)

	def on_api_command(self, command, data):
		if command == "position":
			if isinstance(data["x"], (int, long, float)) and isinstance(data["y"], (int, long, float)):
				self._printer.position(data["x"], data["y"])
			else:
				return make_response("Not a number for one of the parameters", 400)
		elif command == "feedrate":
			self._printer.commands("/feedrate " + str(data["value"]))
		elif command == "intensity":
			self._printer.commands("/intensity " + str(data["value"]))
		elif command == "passes":
			self._printer.set_passes(data["value"])
		elif command == "lasersafety_confirmation":
			return self.lasersafety_wizard_api(data)
		elif command == "ready_to_laser":
			return self.ready_to_laser(data)
		elif command == "camera_calibration_markers":
			return self.camera_calibration_markers(data)
		elif command == "take_undistorted_picture":
			return self.take_undistorted_picture()
		elif command == "debug_event":
			return self.debug_event(data)
		return NO_CONTENT


	def debug_event(self, data):
		event = data['event']
		payload = data['payload'] if 'payload' in data else None
		self._logger.info("Fireing debug event: %s, payload: %s", event, payload)
		self._event_bus.fire(event, payload)
		return NO_CONTENT


	def ready_to_laser(self, data):
		self._logger.debug("ready_to_laser() data: %s", data)
		if 'dev_start_button' in data and data['dev_start_button']:
			if self.get_env(self.ENV_LOCAL).lower() == 'dev':
				self._logger.info("DEV dev_start_button pressed.")
				self._event_bus.fire(IoBeamEvents.ONEBUTTON_RELEASED, 1.1)
			else:
				self._logger.warn("DEV dev_start_button used while we're not in DEV mode. (ENV_LOCAL)")
				return make_response("BAD REQUEST - DEV mode only.", 400)
		elif 'ready' not in data or not data['ready']:
			self._oneButtonHandler.unset_ready_to_laser()

		return NO_CONTENT

	def take_undistorted_picture(self):
		self._logger.debug("New undistorted image is requested")
		image_response = self._lid_handler.set_save_undistorted()
		self._logger.debug("Image_Response: {}".format(image_response))
		return image_response

	def camera_calibration_markers(self, data):
		self._logger.debug("camera_calibration_markers() data: {}".format(data))

		# transform dict
		# todo replace/do better
		newCorners = {}
		for qd in data['result']['newCorners']:
			newCorners[qd] = [data['result']['newCorners'][qd]['x'],data['result']['newCorners'][qd]['y']]

		newMarkers = {}
		for qd in data['result']['newMarkers']:
			newMarkers[qd] = [data['result']['newMarkers'][qd]['x'],data['result']['newMarkers'][qd]['y']]

		pic_settings_path = self._settings.get(["cam", "correctionSettingsFile"])
		pic_settings = self._load_profile(pic_settings_path)

		pic_settings['cornersFromImage'] = newCorners
		pic_settings['calibMarkers'] = newMarkers
		pic_settings['calibration_updated'] = True

		self._logger.debug('picSettings new to save: {}'.format(pic_settings))
		self._save_profile(pic_settings_path,pic_settings)

		# todo delete old undistorted image, still needed?

		return NO_CONTENT


	##~~ SlicerPlugin API

	def is_slicer_configured(self):
		return True

	def get_slicer_properties(self):
		return dict(
			type="svgtogcode",
			name="svgtogcode",
			same_device=True,
			progress_report=True
		)

	def get_slicer_default_profile(self):
		path = self._settings.get(["default_profile"])
		if not path:
			path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "profiles", "default.profile.yaml")
		return self.get_slicer_profile(path)

	def get_slicer_profile(self, path):
		profile_dict = self._load_profile(path)

		display_name = None
		description = None
		if "_display_name" in profile_dict:
			display_name = profile_dict["_display_name"]
			del profile_dict["_display_name"]
		if "_description" in profile_dict:
			description = profile_dict["_description"]
			del profile_dict["_description"]

		properties = self.get_slicer_properties()
		return octoprint.slicing.SlicingProfile(properties["type"], "unknown", profile_dict,
												display_name=display_name, description=description)

	def save_slicer_profile(self, path, profile, allow_overwrite=True, overrides=None):
		if os.path.exists(path) and not allow_overwrite:
			raise octoprint.slicing.ProfileAlreadyExists("cura", profile.name)

		new_profile = Profile.merge_profile(profile.data, overrides=overrides)

		if profile.display_name is not None:
			new_profile["_display_name"] = profile.display_name
		if profile.description is not None:
			new_profile["_description"] = profile.description

		self._save_profile(path, new_profile, allow_overwrite=allow_overwrite)

	def do_slice(self, model_path, printer_profile, machinecode_path=None, profile_path=None, position=None,
				 on_progress=None, on_progress_args=None, on_progress_kwargs=None):
		if not profile_path:
			profile_path = self._settings.get(["default_profile"])
		if not machinecode_path:
			path, _ = os.path.splitext(model_path)
			machinecode_path = path + ".gco"

		self._logger.info("Slicing %s to %s using profile stored at %s, %s" % (model_path, machinecode_path, profile_path, self._CONVERSION_PARAMS_PATH))

		# TODO remove profile dependency completely
		#profile = Profile(self._load_profile(profile_path))
		#params = profile.convert_to_engine2()

		def is_job_cancelled():
			if self._cancel_job:
				self._cancel_job = False
				self._logger.info("Conversion canceled")
				raise octoprint.slicing.SlicingCancelled

		# READ PARAMS FROM JSON
		params = dict()
		with open(self._CONVERSION_PARAMS_PATH) as data_file:
			params = json.load(data_file)
			#self._logger.debug("Read multicolor params %s" % params)

		dest_dir, dest_file = os.path.split(machinecode_path)
		params['directory'] = dest_dir
		params['file'] = dest_file
		params['noheaders'] = "true"  # TODO... booleanify

		if self._settings.get(["debug_logging"]):
			log_path = homedir + "/.octoprint/logs/svgtogcode.log"
			params['log_filename'] = log_path
		else:
			params['log_filename'] = ''

		try:
			from .gcodegenerator.converter import Converter

			is_job_cancelled() #check before conversion started

			#TODO implement cancelled_Jobs, to check if this particular Job has been canceled
			#TODO implement check "_cancel_job"-loop inside engine.convert(...), to stop during conversion, too
			engine = Converter(params, model_path)
			engine.convert(on_progress, on_progress_args, on_progress_kwargs)

			is_job_cancelled() #check if canceled during conversion

			return True, None  # TODO add analysis about out of working area, ignored elements, invisible elements, text elements
		except octoprint.slicing.SlicingCancelled as e:
			self._logger.info("Conversion cancelled")
			raise e
		except Exception as e:
			print e.__doc__
			print e.message
			self._logger.exception("Conversion error ({0}): {1}".format(e.__doc__, e.message))
			return False, "Unknown error, please consult the log file"

		finally:
			with self._cancelled_jobs_mutex:
				if machinecode_path in self._cancelled_jobs:
					self._cancelled_jobs.remove(machinecode_path)
			with self._slicing_commands_mutex:
				if machinecode_path in self._slicing_commands:
					del self._slicing_commands[machinecode_path]

			self._logger.info("-" * 40)

	def cancel_slicing(self, machinecode_path):
		self._logger.info("Canceling Routine: {}".format(machinecode_path))
		with self._slicing_commands_mutex:
			if machinecode_path in self._slicing_commands:
				with self._cancelled_jobs_mutex:
					self._cancelled_jobs.append(machinecode_path)
				self._slicing_commands[machinecode_path].terminate()
				self._logger.info("Cancelled slicing of %s" % machinecode_path)

	def _load_profile(self, path):
		import yaml
		profile_dict = dict()
		with open(path, "r") as f:
			try:
				profile_dict = yaml.safe_load(f)
			except:
				raise IOError("Couldn't read profile from {path}".format(path=path))
		return profile_dict

	def _save_profile(self, path, profile, allow_overwrite=True):
		import yaml
		with open(path, "wb") as f:
			yaml.safe_dump(profile, f, default_flow_style=False, indent="  ", allow_unicode=True)

	def _convert_to_engine(self, profile_path):
		profile = Profile(self._load_profile(profile_path))
		return profile.convert_to_engine()


	##~~ Event Handler Plugin API

	def on_event(self, event, payload):
		if payload is None or not isinstance(payload, collections.Iterable) or not 'log' in payload or payload['log']:
			self._logger.debug("on_event %s: %s", event, payload)


	##~~ Progress Plugin API

	def on_print_progress(self, storage, path, progress):
		flooredProgress = progress - (progress % 10)
		if (flooredProgress != self.print_progress_last):
			self.print_progress_last = flooredProgress
			self._event_bus.fire(MrBeamEvents.PRINT_PROGRESS, self.print_progress_last)

	def on_slicing_progress(self, slicer, source_location, source_path, destination_location, destination_path, progress):
		flooredProgress = progress - (progress % 10)
		if (flooredProgress != self.slicing_progress_last):
			self.slicing_progress_last = flooredProgress
			self._event_bus.fire(MrBeamEvents.SLICING_PROGRESS, self.slicing_progress_last)

	##~~ Softwareupdate hook

	def get_update_information(self):
		# calling from .software_update_information import get_update_information
		return get_update_information(self)

	# inject a Laser object instead the original Printer from standard.py
	def laser_factory(self, components, *args, **kwargs):
		from .printer import Laser
		return Laser(components['file_manager'], components['analysis_queue'], laserCutterProfileManager())

	def laser_filemanager(self, *args, **kwargs):
		def _image_mime_detector(path):
			p = path.lower()
			if p.endswith('.jpg') or p.endswith('.jpeg') or p.endswith('.jpe'):
				return 'image/jpeg'
			elif p.endswith('.png'):
				return 'image/png'
			elif p.endswith('.gif'):
				return 'image/gif'
			elif p.endswith('.bmp'):
				return 'image/bmp'
			elif p.endswith('.pcx'):
				return 'image/x-pcx'
			elif p.endswith('.'):
				return 'image/webp'

		return dict(
			# extensions for image / 3d model files
			model=dict(
				# TODO enable once 3d support is ready
				#stl=ContentTypeMapping(["stl"], "application/sla"),
				image=ContentTypeDetector(['jpg', 'jpeg', 'jpe', 'png', 'gif', 'bmp', 'pcx', 'webp'], _image_mime_detector),
				svg=ContentTypeMapping(["svg"], "image/svg+xml"),
				dxf=ContentTypeMapping(["dxf"], "application/dxf"),
			),
			# extensions for printable machine code
			machinecode=dict(
				gcode=ContentTypeMapping(["gcode", "gco", "g", "nc"], "text/plain")
			)
		)

	def bodysize_hook(self, current_max_body_sizes, *args, **kwargs):
		return [("POST", r"/convert", 10 * 1024 * 1024)]

	def _getCurrentFile(self):
		currentJob = self._printer.get_current_job()
		if currentJob is not None and "file" in currentJob.keys() and "name" in currentJob["file"] and "origin" in \
				currentJob["file"]:
			return currentJob["file"]["origin"], currentJob["file"]["name"]
		else:
			return None, None

	def getHostname(self):
		'''
		Get device hostnema like 'MrBeam2-F930'
		:return: String hostname or empty string
		'''
		hostname = '';
		try:
			hostname = socket.gethostname()
		except:
			hostname = ERROR.HOSTNAME
		return hostname

	def getDisplayName(self, hostName):
		code = None
		name = "Mr Beam II {}"
		preFix = "MrBeam2-"
		if hostName.startswith(preFix):
			code = hostName.replace(preFix, "")
			return name.format(code)
		else:
			return name.format(hostName)

	def getMrBeamSerial(self):
		return "{pi_serial}-{device_series}".format(
			pi_serial=self.getPiSerial(),
			device_series=self._get_val_from_device_info('device_series'))

	def getPiSerial(self):
		'''
		Get RaspberryPi's serial number from cpuinfo file
		:deprected: use getMrBeamSerial() instead
		:return: String serial or ('0000000000000000' or 'ERROR000000000')
		'''
		# Extract serial from cpuinfo file
		cpuserial = "0000000000000000"
		try:
			f = open('/proc/cpuinfo', 'r')
			for line in f:
				if line[0:6] == 'Serial':
					cpuserial = line[10:26]
			f.close()
			cpuserial = cpuserial.upper()
		except Exception as e:
			cpuserial = "ERROR000000000"

		return cpuserial

	def getBranch(self):
		'''
		DEPRECTED
		:return:
		'''
		branch = ''
		try:
			command = "git branch | grep '*'"
			output = check_output(command, shell=True)
			branch = output[1:].strip()
		except Exception as e:
			# 	self._logger.debug("getBranch: unable to exceute 'git branch' due to exception: %s", e)
			pass

		if not branch:
			try:
				command = "cd /home/pi/MrBeamPlugin/; git branch | grep '*'"
				output = check_output(command, shell=True)
				branch = output[1:].strip()
			except Exception as e:
				# 	self._logger.debug("getBranch: unable to exceute 'cd /home/pi/MrBeamPlugin/; git branch' due to exception: %s", e)
				pass

		return branch

	def get_octopi_info(self):
		return self._get_val_from_device_info('octopi')
		# try:
		# 	with open('/etc/octopi_flavor', 'r') as myfile:
		# 		flavor = myfile.read().replace('\n', '')
		# 	with open('/etc/octopi_datetime', 'r') as myfile:
		# 		datetime = myfile.read().replace('\n', '')
		# 	return "{} {}".format(flavor, datetime)
		# except Exception as e:
		# 	# self._logger.exception("Can't read OctoPi image info due to exception:", e)
		# 	pass
		# return None

	def _get_val_from_device_info(self, key):
		device_info_file = '/etc/mrbeam'
		try:
			with open(device_info_file, 'r') as f:
				for line in f:
					line = line.strip()
					token = line.split('=')
					if len(token) >= 2 and token[0] == key:
						return token[1]
		except Exception as e:
			self._logger.error("Can't read device_info_file '%s' due to exception: %s", device_info_file, e)
		return None


	def isFirstRun(self):
		return self._settings.global_get(["server", "firstRun"])

	def is_prod_env(self, type=None):
		return self.get_env(type) == 'prod'

	def get_env(self, type=None):
		result = self._settings.get(["dev", "env"])
		if type is not None:
			if type == self.ENV_LASER_SAFETY:
				type_env = self._settings.get(["dev", "cloud_env"]) # deprected flag
			else:
				type_env = self._settings.get(["dev", "env_overrides", type])
			if type_env is not None:
				result = type_env
		return result


# this is for the command line interface we're providing
def clitest_commands(cli_group, pass_octoprint_ctx, *args, **kwargs):
	import click
	import sys
	import requests.exceptions
	import octoprint_client as client

	# > octoprint plugins mrbeam:debug_event MrBeamDebugEvent -p 42
	# remember to activate venv where MrBeamPlugin is installed in
	@click.command("debug_event")
	@click.argument("event", default="MrBeamDebugEvent")
	@click.option("--payload", "-p", default=None, help="optinal payload string")
	def debug_event_command(event, payload):
		if payload is not None:
			payload_numer = None
			try:
				payload_numer = int(payload)
			except:
				try:
					payload_numer = float(payload)
				except:
					pass
			if payload_numer is not None:
				payload = payload_numer

		params = dict(command="debug_event", event=event, payload=payload)
		client.init_client(cli_group.settings)

		click.echo("Firing debug event - params: {}".format(params))
		r = client.post_json("/api/plugin/mrbeam", data=params)
		try:
			r.raise_for_status()
		except requests.exceptions.HTTPError as e:
			click.echo("Could not fire event, got {}".format(e))
			sys.exit(1)

	return [debug_event_command]


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.

__plugin_name__ = "Mr Beam Laser Cutter"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = MrBeamPlugin()
	__builtin__._mrbeam_plugin_implementation = __plugin_implementation__
	# MRBEAM_PLUGIN_IMPLEMENTATION = __plugin_implementation__

	global __plugin_settings_overlay__
	__plugin_settings_overlay__ = dict(
		plugins=dict(
			_disabled=['cura', 'pluginmanager', 'announcements', 'corewizard']   # eats dict | pfad.yml | callable
			# _disabled=['cura', 'pluginmanager', 'announcements', 'corewizard', 'mrbeam']  # eats dict | pfad.yml | callable
		),
		terminalFilters = [
			dict(name="Filter beamOS messages", regex="^([0-9,.: ]+ [A-Z]+ mrbeam)", activated=False),
			dict(name="Filter _COMM_ messages", regex="^([0-9,.: ]+ _COMM_)", activated=True),
			dict(name="Filter _COMM_ except Gcode", regex="^([0-9,.: ]+ _COMM_: (Send: \?|Recv: ok|Recv: <))", activated=False),
		],
		appearance=dict(components=dict(
			order=dict(
				# to debug: "_logger.info("ANDYTEST templates: %s", templates)" to views.py:_process_templates() at the very end
				wizard=["plugin_mrbeam_wifi", "plugin_mrbeam_acl", "plugin_mrbeam_lasersafety"],
				settings = ['plugin_softwareupdate', 'accesscontrol', 'plugin_netconnectd', 'plugin_mrbeam_conversion', 'terminalfilters', 'logs']
			),
			disabled=dict(
				wizard=['plugin_softwareupdate'],
				settings=['serial', 'webcam']
			)
		)),
		server = dict(commands=dict(
			serverRestartCommand = "sudo systemctl restart octoprint.service",
			systemRestartCommand = "sudo shutdown -r now",
			systemShutdownCommand = "sudo shutdown -h now"
		))
		# )),
		# system=dict(actions=[
		# 	dict(action="iobeam restart", name="iobeam restart", command="sudo systemctl restart iobeam.service"),
		# 	dict(action="ledstrips restart", name="ledstrips restart",
		# 	     command="sudo systemctl restart mrbeam_ledstrips.service && sleep 1 &&  mrbeam_ledstrips_cli ClientConected"),
		# 	dict(action="fan auto", name="fan auto", command="iobeam_info fan:auto"),
		# 	dict(action="fan off", name="fan off", command="iobeam_info fan:off")
		# ])
	)

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.printer.factory": __plugin_implementation__.laser_factory,
		"octoprint.filemanager.extension_tree": __plugin_implementation__.laser_filemanager,
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.server.http.bodysize": __plugin_implementation__.bodysize_hook,
		"octoprint.cli.commands": clitest_commands

	}

