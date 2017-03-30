# coding=utf-8
from __future__ import absolute_import


# import logging as log
from subprocess import check_output

import octoprint.plugin
import flask

from octoprint.util import dict_merge
from octoprint.server import NO_CONTENT
from octoprint.events import Events

from .profile import LaserCutterProfileManager, InvalidProfileError, CouldNotOverwriteError, Profile
from octoprint_mrbeam.iobeam_handler import ioBeamHandler
from octoprint_mrbeam.led_events import LedEventListener

import copy
import time
import os
import logging
import threading
import json
from octoprint.server.util.flask import restricted_access, get_json_command_from_request, add_non_caching_response_headers
from octoprint.server import admin_permission
from octoprint.filemanager import ContentTypeDetector, ContentTypeMapping
from flask.ext.babel import gettext
from flask import Blueprint, request, jsonify, make_response, url_for


import pprint
import requests
import socket



class MrBeamPlugin(octoprint.plugin.SettingsPlugin,
                   octoprint.plugin.AssetPlugin,
				   octoprint.plugin.UiPlugin,
                   octoprint.plugin.TemplatePlugin,
				   octoprint.plugin.BlueprintPlugin,
				   octoprint.plugin.SimpleApiPlugin,
				   octoprint.plugin.EventHandlerPlugin,
				   octoprint.plugin.ProgressPlugin,
				   octoprint.plugin.WizardPlugin,
				   octoprint.plugin.SlicerPlugin):

	# CONSTANTS

	GLOBAL_SETTINGS_KEY_DEVEL_MRBEAM_CLOUD_ENV = ["devel", "mrbeam", "cloud_env"]
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

	def initialize(self):
		self.laserCutterProfileManager = LaserCutterProfileManager(self._settings)
		self._logger = logging.getLogger("octoprint.plugins.mrbeam")
		self._branch = self.getBranch()
		self._hostname = self.getHostname()
		self._logger.info("MrBeam Plugin initialize()  version: %s, branch: %s, host: %s",
						  self._plugin_version, self._branch, self._hostname)
		try:
			pluginInfo = self._plugin_manager.get_plugin_info("netconnectd")
			if pluginInfo is None:
				self._logger.warn("NetconnectdPlugin not available. Wifi configuration not possible.")
		except Exception as e:
			self._logger.exception("Exception while getting NetconnectdPlugin pluginInfo")

		self._eventManagerMrb = ioBeamHandler(self._event_bus)
		self._led_eventhandler = LedEventListener(self._printer, self._event_bus)


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
		return dict(
			current_profile_id="_mrbeam_junior",
			defaultIntensity=500,
			defaultFeedrate=300,
			svgDPI=90,
			svgtogcode_debug_logging=False,
			showlasersafety=False,
			glasses=False,
			camera_offset_x=0,
			camera_offset_y=0,
			camera_scale=1,
			camera_rotation=0
		)

	def on_settings_load(self):
		return dict(
			current_profile_id=self._settings.get(["current_profile_id"]),
			defaultIntensity=self._settings.get(['defaultIntensity']),
			defaultFeedrate=self._settings.get(['defaultFeedrate']),
			svgDPI=self._settings.get(['svgDPI']),
			svgtogcode_debug_logging=self._settings.get(['svgtogcode_debug_logging']),
			showlasersafety=self._settings.get(['showlasersafety']),
			glasses=self._settings.get(['glasses']),
			camera_offset_x=self._settings.get(['camera_offset_x']),
			camera_offset_y=self._settings.get(['camera_offset_y']),
			camera_scale=self._settings.get(['camera_scale']),
			camera_rotation=self._settings.get(['camera_rotation']),
			)

	def on_settings_save(self, data):
		if "workingAreaWidth" in data and data["workingAreaWidth"]:
			self._settings.set(["workingAreaWidth"], data["workingAreaWidth"])
		if "zAxis" in data:
			self._settings.set_boolean(["zAxis"], data["zAxis"])
		if "defaultIntensity" in data:
			self._settings.set_int(["defaultIntensity"], data["defaultIntensity"])
		if "defaultFeedrate" in data:
			self._settings.set_int(["defaultFeedrate"], data["defaultFeedrate"])
		if "svgDPI" in data:
			self._settings.set_int(["svgDPI"], data["svgDPI"])
		if "camera_offset_x" in data:
			self._settings.set_int(["camera_offset_x"], data["camera_offset_x"])
		if "camera_offset_y" in data:
			self._settings.set_int(["camera_offset_y"], data["camera_offset_y"])
		if "camera_scale" in data:
			self._settings.set_float(["camera_scale"], data["camera_scale"])
		if "camera_rotation" in data:
			self._settings.set_float(["camera_rotation"], data["camera_rotation"])
		if "svgtogcode_debug_logging" in data:
			self._settings.set_boolean(["svgtogcode_debug_logging"], data["svgtogcode_debug_logging"])

		selectedProfile = self.laserCutterProfileManager.get_current_or_default()
		self._settings.set(["current_profile_id"], selectedProfile['id'])

	##~~ AssetPlugin mixin

	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/lasercutterprofiles.js","js/mother_viewmodel.js", "js/mrbeam.js","js/color_classifier.js",
				"js/working_area.js", "js/camera.js", "js/lib/snap.svg-min.js", "js/render_fills.js", "js/path_convert.js",
				"js/matrix_oven.js", "js/drag_scale_rotate.js",	"js/convert.js", "js/gcode_parser.js",
				"js/lib/photobooth_min.js", "js/svg_cleaner.js", "js/loginscreen_viewmodel.js",
				"js/wizard_acl.js", "js/netconnectd_wrapper.js", "js/lasersaftey_viewmodel.js"],
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
			render_kwargs["templates"]["wizard"]["entries"]["firstrunstart"][1]["template"] = "wizard/firstrun_start.jinja2"
			render_kwargs["templates"]["wizard"]["entries"]["firstrunend"][1]["template"] = "wizard/firstrun_end.jinja2"

		render_kwargs.update(dict(
							 webcamStream=self._settings.global_get(["webcam", "stream"]),
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
								display_version = "{} ({} branch) on {}".format(
									self._plugin_version, self._branch, self._hostname) if self._branch else (self._plugin_version, self._hostname)
								)
							 ))
		r = make_response(render_template("mrbeam_ui_index.jinja2", **render_kwargs))

		if firstRun:
			r = add_non_caching_response_headers(r)
		return r

	##~~ TemplatePlugin mixin

	def get_template_configs(self):
		return [
			dict(type='settings', name="Machine Profiles", template='settings/lasercutterprofiles_settings.jinja2', suffix="_lasercutterprofiles", custom_bindings=False),
			dict(type='settings', name="SVG Conversion", template='settings/svgtogcode_settings.jinja2', suffix="_conversion", custom_bindings=False),
			dict(type='settings', name="Camera Calibration", template='settings/camera_settings.jinja2', suffix="_camera", custom_bindings=True),
			dict(type='settings', name="Serial Connection", template='settings/serialconnection_settings.jinja2', suffix='_serialconnection', custom_bindings=False, replaces='serial')
		] + self._get_wizard_template_configs()

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
		from octoprint.server.api import valid_boolean_trues, NO_CONTENT

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
		from octoprint.server.api import valid_boolean_trues, NO_CONTENT

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
		from octoprint.server.api import valid_boolean_trues, NO_CONTENT

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
		if submissionDate <= 0 or force:
			# get cloud env to use
			debug = self._settings.global_get(self.GLOBAL_SETTINGS_KEY_DEVEL_MRBEAM_CLOUD_ENV)

			payload = {'ts': data.get('ts', ''),
					   'email': data.get('username', ''),
					   'serial': self.getPiSerial(),
					   'hostname': self._hostname}

			if debug is not None and debug != "prod":
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

	# Laser cutter profiles
	@octoprint.plugin.BlueprintPlugin.route("/profiles", methods=["GET"])
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
		### TODO queu the commands if not in locked or operational mode
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
			import re
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
			lasersafety_confirmation=[]
		)

	def on_api_command(self, command, data):
		import flask
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
			self.lasersafety_wizard_api(data)
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
		# self._logger.debug("on_event %s: %s", event, payload)
		pass

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
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
		# for details.
		return dict(
			mrbeam=dict(
				displayName="Mr Beam Laser Cutter",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="mrbeam",
				repo="MrBeamPlugin",
				branch="develop",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/mrbeam/MrBeamPlugin/archive/{target_version}.zip"
			)
		)

	# inject a Laser object instead the original Printer from standard.py
	def laser_factory(self, components, *args, **kwargs):
		from .printer import Laser
		return Laser(components['file_manager'], components['analysis_queue'], components['printer_profile_manager'])

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
				svg=ContentTypeMapping(["svg"], "image/svg+xml")
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
		hostname = '';
		try:
			hostname = socket.gethostname()
		except:
			hostname = ERROR.HOSTNAME
		return hostname


	def getPiSerial(self):
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
		branch = ''
		try:
			command = "git branch | grep '*'"
			output = check_output(command, shell=True)
			branch = output[1:].strip()
		except Exception as e:
			True
			# 	self._logger.debug("getBranch: unable to exceute 'git branch' due to exception: %s", e)

		if not branch:
			try:
				command = "cd /home/pi/MrBeamPlugin/; git branch | grep '*'"
				output = check_output(command, shell=True)
				branch = output[1:].strip()
			except Exception as e:
				True
				# 	self._logger.debug("getBranch: unable to exceute 'cd /home/pi/MrBeamPlugin/; git branch' due to exception: %s", e)

		return branch


	def isFirstRun(self):
		return self._settings.global_get(["server", "firstRun"])


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.


__plugin_name__ = "Mr Beam Laser Cutter"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = MrBeamPlugin()

	global __plugin_settings_overlay__
	__plugin_settings_overlay__ = dict(
		plugins=dict(
			_disabled=['cura', 'pluginmanager', 'announcements', 'corewizard']   # eats dict | pfad.yml | callable
			# _disabled=['cura', 'pluginmanager', 'announcements', 'corewizard', 'mrbeam']  # eats dict | pfad.yml | callable
		),
		terminalFilters=[
			{"name": "Suppress position requests", "regex": "(Send: \?)"},
			{"name": "Suppress confirmations", "regex": "(Recv: ok)"},
			{"name": "Suppress status messages", "regex": "(Recv: <)"},
		],
		appearance=dict(components=dict(
			order=dict(
				# to debug: pprint(templates['wizard']) to views.py:_process_templates() at the very end
				wizard=["plugin_mrbeam_wifi", "plugin_mrbeam_acl", "plugin_mrbeam_lasersafety"]
			),
			disabled=dict(
				wizard=['plugin_softwareupdate']
			)
		))
	)

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.printer.factory": __plugin_implementation__.laser_factory,
		"octoprint.filemanager.extension_tree": __plugin_implementation__.laser_filemanager,
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.server.http.bodysize": __plugin_implementation__.bodysize_hook
		#"octoprint.server.http.routes": __plugin_implementation__.serve_url
	}

