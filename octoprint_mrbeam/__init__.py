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
import collections
from subprocess import check_output

import octoprint.plugin
import requests
from flask import request, jsonify, make_response, url_for
from flask.ext.babel import gettext
from octoprint.filemanager import ContentTypeDetector, ContentTypeMapping
from octoprint.server import NO_CONTENT
from octoprint.server.util.flask import restricted_access, get_json_command_from_request, \
	add_non_caching_response_headers
from octoprint.util import dict_merge
from octoprint.settings import settings
from octoprint.events import Events as OctoPrintEvents

from octoprint_mrbeam.iobeam.iobeam_handler import ioBeamHandler, IoBeamEvents
from octoprint_mrbeam.iobeam.onebutton_handler import oneButtonHandler
from octoprint_mrbeam.iobeam.interlock_handler import interLockHandler
from octoprint_mrbeam.iobeam.lid_handler import lidHandler
from octoprint_mrbeam.iobeam.temperature_manager import temperatureManager
from octoprint_mrbeam.iobeam.dust_manager import dustManager
from octoprint_mrbeam.analytics.analytics_handler import analyticsHandler
from octoprint_mrbeam.analytics.usage_handler import usageHandler
from octoprint_mrbeam.led_events import LedEventListener
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.mrb_logger import init_mrb_logger, mrb_logger
from octoprint_mrbeam.migrate import migrate
from octoprint_mrbeam.printing.profile import laserCutterProfileManager, InvalidProfileError, CouldNotOverwriteError, Profile
from octoprint_mrbeam.software_update_information import get_update_information, switch_software_channel, software_channels_available, SW_UPDATE_TIER_PROD, SW_UPDATE_TIER_BETA
from octoprint_mrbeam.support import set_support_mode
from octoprint_mrbeam.util.cmd_exec import exec_cmd, exec_cmd_output
from octoprint_mrbeam.cli import get_cli_commands
from .materials import materials
from octoprint_mrbeam.gcodegenerator.jobtimeestimation import JobTimeEstimation



# this is a easy&simple way to access the plugin and all injections everywhere within the plugin
__builtin__._mrbeam_plugin_implementation = None
__builtin__.__package_path__ = os.path.dirname(__file__)


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
				   octoprint.plugin.ShutdownPlugin,
				   octoprint.plugin.EnvironmentDetectionPlugin):

	# CONSTANTS
	DEVIE_INFO_FILE = '/etc/mrbeam'

	ENV_PROD =         "PROD"
	ENV_DEV  =         "DEV"

	# local envs are deprecated
	ENV_LOCAL =        "local"
	ENV_LASER_SAFETY = "laser_safety"
	ENV_ANALYTICS =    "analytics"

	LASERSAFETY_CONFIRMATION_DIALOG_VERSION  = "0.3"

	LASERSAFETY_CONFIRMATION_STORAGE_URL = 'https://script.google.com/a/macros/mr-beam.org/s/AKfycby3Y1RLBBiGPDcIpIg0LHd3nwgC7GjEA4xKfknbDLjm3v9-LjG1/exec'
	USER_SETTINGS_KEY_MRBEAM = 'mrbeam'
	USER_SETTINGS_KEY_TIMESTAMP = 'ts'
	USER_SETTINGS_KEY_VERSION = 'version'
	USER_SETTINGS_KEY_LASERSAFETY_CONFIRMATION_SENT_TO_CLOUD = ['lasersafety', 'sent_to_cloud']
	USER_SETTINGS_KEY_LASERSAFETY_CONFIRMATION_SHOW_AGAIN = ['lasersafety', 'show_again']

	CUSTOM_MATERIAL_STORAGE_URL = 'https://script.google.com/a/macros/mr-beam.org/s...' # TODO

	BOOT_GRACE_PERIOD = 15 # seconds
	TIME_NTP_SYNC_CHECK_FAST_COUNT =  20
	TIME_NTP_SYNC_CHECK_INTERVAL_FAST =  10.0
	TIME_NTP_SYNC_CHECK_INTERVAL_SLOW = 120.0


	def __init__(self):
		self._shutting_down = False
		self._slicing_commands = dict()
		self._slicing_commands_mutex = threading.Lock()
		self._cancelled_jobs = []
		self._cancelled_jobs_mutex = threading.Lock()
		self._CONVERSION_PARAMS_PATH = "/tmp/conversion_parameters.json"  # TODO add proper path there
		self._cancel_job = False
		self.print_progress_last = -1
		self.slicing_progress_last = -1
		self._logger = mrb_logger("octoprint.plugins.mrbeam")
		self._hostname = None
		self._serial_num = None
		self._device_info = dict()
		self._grbl_version = None
		self._stored_frontend_notifications = []
		self._device_series = self._get_val_from_device_info('device_series')  # '2C'
		self.called_hosts = []

		self._boot_grace_period_counter = 0
		self._start_boot_grace_period_thread()

		self._time_ntp_synced = False
		self._time_ntp_check_count = 0
		self._time_ntp_check_last_ts = 0.0
		self._time_ntp_shift = 0.0
		self.lh = dict(serial=None, p_65=None, p_75=None, p_85=None, correction_factor=None, correction_enabled=None)


		# MrBeam Events needs to be registered in OctoPrint in order to be send to the frontend later on
		MrBeamEvents.register_with_octoprint()

	# inside initialize() OctoPrint is already loaded, not assured during __init__()!
	def initialize(self):
		init_mrb_logger(self._printer)
		self._logger = mrb_logger("octoprint.plugins.mrbeam")
		self._branch = self.getBranch()
		self._octopi_info = self.get_octopi_info()
		self._serial_num = self.getSerialNum()

		self._analytics_handler = analyticsHandler(self)

		self.focusReminder = self._settings.get(['focusReminder'])

		self._initialize_lh()

		self.start_time_ntp_timer()

		# do migration if needed
		migrate(self)

		self.set_serial_setting()

		# Enable or disable internal support user.
		self.support_mode = set_support_mode(self)

		self.laserCutterProfileManager = laserCutterProfileManager()

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
		self._usageHandler = usageHandler(self)
		self._led_eventhandler = LedEventListener(self._event_bus, self._printer)
		# start iobeam socket only once other handlers are already inittialized so that we can handle info mesage
		self._ioBeam = ioBeamHandler(self._event_bus, self._settings.get(["dev", "sockets", "iobeam"]))
		self._temperatureManager = temperatureManager()
		self._dustManager = dustManager()
		self.jobTimeEstimation = JobTimeEstimation(self._event_bus)

	def _initialize_lh(self):
		self.lh['serial'] = self._settings.get(["laserhead", "serial"])
		self.lh['correction_factor'] = self._settings.get(["laserhead", "correction", "factor"])
		self.lh['correction_factor_override'] = self._settings.get(["laserhead", "correction", "factor_override"])
		self.lh['correction_enabled'] = self._settings.get(["laserhead", "correction", "enabled"])
		self.lh['p_65'] = self._settings.get(["laserhead", "p_65"])
		self.lh['p_75'] = self._settings.get(["laserhead", "p_75"])
		self.lh['p_85'] = self._settings.get(["laserhead", "p_85"])

	def _do_initial_log(self):
		"""
		Kicks an identifying log line
		Was really important before we had
		@see self.get_additional_environment()
		"""
		msg = "MrBeam Plugin"
		msg += " version:{}".format(self._plugin_version)
		msg += ", host:{}".format(self.getHostname())
		msg += ", serial:{}".format(self.getSerialNum())
		msg += ", software_tier:{}".format(self._settings.get(["dev", "software_tier"]))
		msg += ", env:{}".format(self.get_env())
		msg += ", beamOS-image:{}".format(self._octopi_info)
		msg += ", grbl_version_lastknown:{}".format(self._settings.get(["grbl_version_lastknown"]))
		msg += ", laserhead-serial:{}".format(self.lh['serial'])
		self._logger.info(msg, terminal=True)

		msg = "MrBeam Lasercutter Profile: %s" % self.laserCutterProfileManager.get_current_or_default()
		self._logger.info(msg, terminal=True)

		if self.is_vorlon_enabled():
			self._logger.warn("!!! VORLON is enabled !!!!", terminal=True)

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

	def get_additional_environment(self):
		"""
		Mixin: octoprint.plugin.EnvironmentDetectionPlugin
		:return: dict of environment data
		"""
		return dict(version=self._plugin_version,
		            host=self.getHostname(),
		            serial=self._serial_num,
		            software_tier=self._settings.get(["dev", "software_tier"]),
		            env=self.get_env(),
		            beamOS_image=self._octopi_info,
		            grbl_version_lastknown=self._settings.get(["grbl_version_lastknown"]),
		            laserhead_serial=self.lh['serial'])

	##~~ SettingsPlugin mixin
	def get_settings_version(self):
		return 2

	def get_settings_defaults(self):
		# Max img size: 2592x1944. Change requires rebuild of lens_correction_*.npz and machine recalibration.
		image_default_width = 2048
		image_default_height = 1536

		return dict(
			current_profile_id="_mrbeam_junior", # yea, this needs to be like this # 2018: not so sure anymore...
			svgDPI=90,
			dxfScale=1,
			beta_label="",
			job_time = 0.0,
			terminal=False,
			terminal_show_checksums = True,
			vorlon=False,
			converter_min_required_disk_space=100 * 1024 * 1024, # 100MB, in theory 371MB is the maximum expected file size for full working area engraving at highest resolution.
			dev=dict(
				debug=False, # deprected
				terminalMaxLines = 2000,
				env = self.ENV_PROD,
				load_gremlins = False,
				software_tier = SW_UPDATE_TIER_PROD,
				iobeam_disable_warnings = False, # for develpment on non-MrBeam devices
				suppress_migrations = False,     # for develpment on non-MrBeam devices
				support_mode = False,
				grbl_auto_update_enabled = True
			),
			laserhead=dict(
				correction=dict(
					enabled=True,
					factor=1,
					factor_override=None,
					gcode_intensity_limit=1700,
				),
				p_65=0,
				p_75=0,
				p_85=0,
				serial=None,
			),
			focusReminder=True,
			analyticsEnabled=None,
			analytics=dict(
				cam_analytics = False,
				folder = 'analytics', # laser job analytics base folder (.octoprint/...)
				filename = 'analytics_log.json',
				usage_filename = 'usage.yaml',
				usage_backup_filename = 'usage_bak.yaml'
			),
			cam=dict(
				enabled=True,
				image_correction_enabled = True,
				cam_img_width = image_default_width,
				cam_img_height = image_default_height,
				frontendUrl="/downloads/files/local/cam/beam-cam.jpg",
				localFilePath="cam/beam-cam.jpg",
				localUndistImage="cam/undistorted.jpg",
				keepOriginals=False,
				# TODO: we nee a better and unified solution for our custom paths. Some day...
				correctionSettingsFile='{}/cam/pic_settings.yaml'.format(settings().getBaseFolder('base')),
				correctionTmpFile='{}/cam/last_markers.json'.format(settings().getBaseFolder('base')),
				lensCalibrationFile='{}/cam/lens_correction_{}x{}.npz'.format(settings().getBaseFolder('base'), image_default_width, image_default_height),
				saveCorrectionDebugImages=False,
			),
			gcode_nextgen = dict(
				enabled = True,
				precision = 0.05,
				optimize_travel = True,
				small_paths_first = True,
				clip_working_area = True # https://github.com/mrbeam/MrBeamPlugin/issues/134
			),
			grbl_version_lastknown=None,
		)

	def on_settings_load(self):
		return dict(
			svgDPI=self._settings.get(['svgDPI']),
			dxfScale=self._settings.get(['dxfScale']),
			terminal=self._settings.get(['terminal']),
			terminal_show_checksums=self._settings.get(['terminal_show_checksums']),
			vorlon=self.is_vorlon_enabled(),
			analyticsEnabled=self._settings.get(['analyticsEnabled']),
			cam=dict(enabled=self._settings.get(['cam', 'enabled']),
					 frontendUrl=self._settings.get(['cam', 'frontendUrl'])),
			dev=dict(
				env = self._settings.get(['dev', 'env']),
				software_tier = self._settings.get(["dev", "software_tier"]),
				software_tiers_available=software_channels_available(self),
				terminalMaxLines = self._settings.get(['dev', 'terminalMaxLines'])),
			gcode_nextgen=dict(
				enabled = self._settings.get(['gcode_nextgen', 'enabled']),
				precision = self._settings.get(['gcode_nextgen', 'precision']),
				optimize_travel = self._settings.get(['gcode_nextgen', 'optimize_travel']),
				small_paths_first = self._settings.get(['gcode_nextgen', 'small_paths_first']),
				clip_working_area = self._settings.get(['gcode_nextgen', 'clip_working_area'])
			),
			software_update_branches = self.get_update_branch_info(),
			_version = self._plugin_version,
			focusReminder = self._settings.get(['focusReminder']),
			airFilterUsage = self._usageHandler.get_air_filter_usage(),
		)

	def on_settings_save(self, data):
		try:
			# self._logger.info("ANDYTEST on_settings_save() %s", data)
			if "svgDPI" in data:
				self._settings.set_int(["svgDPI"], data["svgDPI"])
			if "dxfScale" in data:
				self._settings.set_float(["dxfScale"], data["dxfScale"])
			if "terminal" in data:
				self._settings.set_boolean(["terminal"], data["terminal"])
			if "terminal_show_checksums" in data:
				self._settings.set_boolean(["terminal_show_checksums"], data["terminal_show_checksums"])
				self._printer._comm.set_terminal_show_checksums(data["terminal_show_checksums"])
			if "vorlon" in data:
				if data["vorlon"]:
					self._settings.set_float(["vorlon"], time.time())
					self._logger.warn("Enabling VORLON per user request.", terminal=True)
				else:
					self._settings.set_boolean(["vorlon"], False)
					self._logger.info("Disabling VORLON per user request.", terminal=True)
			if "gcode_nextgen" in data and isinstance(data['gcode_nextgen'],
			                                          collections.Iterable) and "clip_working_area" in data[
				'gcode_nextgen']:
				self._settings.set_boolean(["gcode_nextgen", "clip_working_area"],
				                           data['gcode_nextgen']['clip_working_area'])
			if "analyticsEnabled" in data:
				self._analytics_handler.analytics_user_permission_change(analytics_enabled=data['analyticsEnabled'])
			if "focusReminder" in data:
				self._settings.set_boolean(["focusReminder"], data["focusReminder"])
			if "dev" in data and "software_tier" in data['dev']:
				switch_software_channel(self, data["dev"]["software_tier"])
		except Exception as e:
			self._logger.exception("Exception in on_settings_save() ")
			raise e

	def on_shutdown(self):
		self._shutting_down = True
		self._logger.debug("Mr Beam Plugin stopping...")
		self._ioBeam.shutdown()
		self._lid_handler.shutdown()
		self._temperatureManager.shutdown()
		self._dustManager.shutdown()
		time.sleep(2)
		self._logger.info("Mr Beam Plugin stopped.")


	def set_serial_setting(self):
		self._settings.global_set(['serial', 'autoconnect'], True)
		self._settings.global_set(['serial', 'baudrate'], 115200)
		self._settings.global_set(['serial', 'port'], '/dev/ttyAMA0')

	##~~ AssetPlugin mixin

	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		assets = dict(
			js=["js/lasercutterprofiles.js",
			    "js/mother_viewmodel.js",
			    "js/mrbeam.js",
			    "js/color_classifier.js",
				"js/working_area.js",
				"js/camera.js",
				"js/lib/snap.svg-min.js",
				"js/lib/dxf.js",
				"js/snap-dxf.js",
				"js/render_fills.js",
				"js/path_convert.js",
				"js/matrix_oven.js",
				"js/unref.js",
				"js/drag_scale_rotate.js",
				"js/convert.js",
				"js/snap_gc_plugin.js",
				"js/gcode_parser.js",
				"js/gridify.js",
				# "js/lib/photobooth_min.js",
				"js/svg_cleaner.js",
				"js/loginscreen_viewmodel.js",
				"js/wizard_acl.js",
				"js/netconnectd_wrapper.js",
				"js/lasersaftey_viewmodel.js",
				"js/ready_to_laser_viewmodel.js",
				"js/lib/screenfull.min.js",
				"js/settings/camera_calibration.js",
				"js/path_magic.js",
				"js/lib/simplify.js",
				"js/lib/clipper.js",
				"js/lib/Color.js",
				"js/laser_job_done_viewmodel.js",
				"js/loadingoverlay_viewmodel.js",
				"js/wizard_whatsnew.js",
				"js/wizard_analytics.js",
				"js/software_channel_selector.js",
				"js/lib/hopscotch.js",
				"js/tour_viewmodel.js",
				"js/air_filter_usage.js",
				"js/feedback_widget.js",
				"js/material_settings.js",
				"js/analytics.js",
			    ],
			css=["css/mrbeam.css",
			     "css/svgtogcode.css",
			     "css/ui_mods.css",
			     "css/quicktext-fonts.css",
			     "css/sliders.css",
			     "css/hopscotch.min.css",
			     ],
			less=["less/mrbeam.less"]
		)
		if(self._settings.get(["dev", "load_gremlins"])):
			assets['js'].append('js/lib/gremlins.min.js')
		return assets

	##~~ UiPlugin mixin

	def will_handle_ui(self, request):
		# returns True as Mr Beam Plugin should be always displayed
		return True

	def on_ui_render(self, now, request, render_kwargs):
		# if will_handle_ui returned True, we will now render our custom index
		# template, using the render_kwargs as provided by OctoPrint
		from flask import make_response, render_template, g

		firstRun = render_kwargs['firstRun']
		language = g.locale.language if g.locale else "en"

		if request.headers.get('User-Agent') != self._analytics_handler.SELF_CHECK_USER_AGENT:
			self._track_ui_render_calls(request, language)

		enable_accesscontrol = self._user_manager.enabled
		accesscontrol_active = enable_accesscontrol and self._user_manager.hasBeenCustomized()

		selectedProfile = self.laserCutterProfileManager.get_current_or_default()
		enable_focus = selectedProfile["focus"]
		safety_glasses = selectedProfile["glasses"]
		# render_kwargs["templates"]["settings"]["entries"]["serial"][1]["template"] = "settings/serialconnection.jinja2"

		wizard = render_kwargs["templates"] is not None and bool(render_kwargs["templates"]["wizard"]["order"])


		if render_kwargs["templates"]["wizard"]["entries"]:
			if "firstrunstart" in render_kwargs["templates"]["wizard"]["entries"]:
				render_kwargs["templates"]["wizard"]["entries"]["firstrunstart"][1]["template"] = "wizard/firstrun_start.jinja2"
			if "firstrunend" in render_kwargs["templates"]["wizard"]["entries"]:
				render_kwargs["templates"]["wizard"]["entries"]["firstrunend"][1]["template"] = "wizard/firstrun_end.jinja2"

		display_version_string = "{} on {}".format(self._plugin_version, self.getHostname())
		if self._branch:
			display_version_string = "{} ({} branch) on {}".format(self._plugin_version, self._branch, self.getHostname())

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
							 language = language,

							 beamosVersionNumber = self._plugin_version,
							 beamosVersionBranch = self._branch,
							 beamosVersionDisplayVersion = display_version_string,
							 beamosVersionImage = self._octopi_info,
							 grbl_version=self._grbl_version,
							 laserhead_serial=self.lh['serial'],

							 env=self.get_env(),
							 env_local=self.get_env(self.ENV_LOCAL),
							 env_laser_safety=self.get_env(self.ENV_LASER_SAFETY),
							 env_analytics=self.get_env(self.ENV_ANALYTICS),

							 displayName=self.getDisplayName(),
							 hostname=self.getHostname(),
							 serial=self._serial_num,
							 software_tier=self._settings.get(["dev", "software_tier"]),
							 analyticsEnabled=self._settings.get(["analyticsEnabled"]),
							 beta_label=self.get_beta_label(),
							 terminalEnabled=self._settings.get(['terminal']) or self.support_mode,
							 vorlonEnabled=self.is_vorlon_enabled(),

							 lasersafety_confirmation_dialog_version  = self.LASERSAFETY_CONFIRMATION_DIALOG_VERSION,
							 lasersafety_confirmation_dialog_language = language
						 ))
		r = make_response(render_template("mrbeam_ui_index.jinja2", **render_kwargs))

		if firstRun:
			r = add_non_caching_response_headers(r)
		return r


	def _track_ui_render_calls(self, request, language):
		remote_ip = request.headers.get("X-Forwarded-For")
		if remote_ip is not None:
			my_call = dict(host=request.host,
			               ref=request.referrer,
			               remote_ip=remote_ip,
			               language=language)
			if not my_call in self.called_hosts:
				self.called_hosts.append(my_call)
				self._logger.info("First call received from: %s", my_call)
				self._logger.info("All unique calls: %s", self.called_hosts)
			self._analytics_handler.log_ui_render_calls(host=my_call['host'], remote_ip=my_call['remote_ip'], referrer=my_call['ref'], language=language)

	##~~ TemplatePlugin mixin

	def get_template_configs(self):
		result = [
			dict(type='settings', name=gettext("File Import Settings"), template='settings/svgtogcode_settings.jinja2', suffix="_conversion", custom_bindings=False),
            dict(type='settings', name=gettext("Camera Calibration"), template='settings/camera_settings.jinja2', suffix="_camera", custom_bindings=True),
            dict(type='settings', name=gettext("Debug"), template='settings/debug_settings.jinja2', suffix="_debug", custom_bindings=False),
            dict(type='settings', name=gettext("About This Mr Beam"), template='settings/about_settings.jinja2', suffix="_about", custom_bindings=False),
            dict(type='settings', name=gettext("Analytics"), template='settings/analytics_settings.jinja2', suffix="_analytics", custom_bindings=False),
			dict(type='settings', name=gettext("Reminders"), template='settings/reminders_settings.jinja2', suffix="_reminders", custom_bindings=False),
			dict(type='settings', name=gettext("Exhaust System"), template='settings/air_filter_settings.jinja2', suffix="_airfilter", custom_bindings=True),
      
			# disabled in appearance
			# dict(type='settings', name="Serial Connection DEV", template='settings/serialconnection_settings.jinja2', suffix='_serialconnection', custom_bindings=False, replaces='serial')
		 ]
		if not self.is_prod_env('local'):
			result.extend([
				dict(type='settings', name="DEV Machine Profiles", template='settings/lasercutterprofiles_settings.jinja2', suffix="_lasercutterprofiles", custom_bindings=False)
			])
		result.extend(self._get_wizard_template_configs())
		return result

	def get_template_vars(self):
		"""
		Needed to have analytigs settings page in German
		while we do not have real internationalization yet.
		"""
		from flask import g
		return dict(
			language = g.locale.language if g.locale else "en"
		)

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
		return True

	def get_wizard_details(self):
		return dict()

	def get_wizard_version(self):
		return 15 #random number. but we can't go down anymore, just up.

	def on_wizard_finish(self, handled):
		self._logger.info("Setup Wizard finished.")
		# map(lambda m: m(handled), self._get_subwizard_attrs("_on_", "_wizard_finish").values())


	# ~~ Wifi subwizard

	def _is_wifi_wizard_required(self):
		result = False
		if self.isFirstRun():
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


	# ~~ Saftey subwizard

	def _is_lasersafety_wizard_required(self):
		result = self.isFirstRun()
		self._logger.debug("_is_lasersafety_wizard_required() %s", result)
		return result

	def _get_lasersafety_wizard_details(self):
		return dict()

	def _get_lasersafety_additional_wizard_template_data(self):
		return dict(mandatory=False, suffix="_lasersafety")

	def _get_lasersafety_wizard_name(self):
		return gettext("Laser Safety")

	# ~~ Whats new subwizard

	def _is_whatsnew_0_wizard_required(self):
		result = not self.isFirstRun()
		self._logger.debug("_is_whatsnew_0_wizard_required() %s", result)
		return result

	def _get_whatsnew_0_wizard_details(self):
		return dict()

	def _get_whatsnew_0_additional_wizard_template_data(self):
		return dict(mandatory=False, suffix="_whatsnew_0")

	def _get_whatsnew_0_wizard_name(self):
		# jinja has some js that changes this to German if lang is 'de'
		return gettext("What's New")

	# def _is_whatsnew_1_wizard_required(self):
	# 	result = not self.isFirstRun()
	# 	self._logger.debug("_is_whatsnew_1_wizard_required() %s", result)
	# 	return result
	#
	# def _get_whatsnew_1_wizard_details(self):
	# 	return dict()
	#
	# def _get_whatsnew_1_additional_wizard_template_data(self):
	# 	return dict(mandatory=False, suffix="_whatsnew_1")
	#
	# def _get_whatsnew_1_wizard_name(self):
	# 	# jinja has some js that changes this to German if lang is 'de'
	# 	return gettext("New Mr Beam Status Light")

	# ~~ Analytics subwizard

	def _is_analytics_wizard_required(self):
		result = self._settings.get(['analyticsEnabled']) is None
		self._logger.debug("_is_analytics_wizard_required() %s", result)
		return result

	def _get_analytics_wizard_details(self):
		return dict()

	def _get_analytics_additional_wizard_template_data(self):
		return dict(mandatory=False, suffix="_analytics")

	def _get_analytics_wizard_name(self):
		# jinja has some js that changes this to German if lang is 'de'
		return gettext("Analytics")


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

		show_again = bool(data.get('show_again', True))
		dialog_language = data.get('dialog_language')

		# see if we nee to send this to the cloud
		submissionDate = self.getUserSetting(username, self.USER_SETTINGS_KEY_LASERSAFETY_CONFIRMATION_SENT_TO_CLOUD, -1)
		force = bool(data.get('force', False))
		needSubmission = submissionDate <= 0 or force
		if needSubmission:
			# get cloud env to use
			debug = self.get_env(self.ENV_LASER_SAFETY)

			payload = {'ts': data.get('ts', ''),
					   'email': data.get('username', ''),
					   'serial': self._serial_num,
					   'hostname': self.getHostname(),
			           'dialog_version': self.LASERSAFETY_CONFIRMATION_DIALOG_VERSION,
			           'dialog_language': dialog_language,
			           'plugin_version': self._plugin_version,
			           'software_tier': self._settings.get(["dev", "software_tier"]),
			           'env': self.get_env(),
			           }

			if debug is not None and debug.upper() != self.ENV_PROD:
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
			show_again = show_again if successfullySubmitted else True
			self.setUserSetting(username, self.USER_SETTINGS_KEY_LASERSAFETY_CONFIRMATION_SENT_TO_CLOUD, submissionDate)
			self.setUserSetting(username, self.USER_SETTINGS_KEY_LASERSAFETY_CONFIRMATION_SHOW_AGAIN, show_again)

			# and drop a line into the log on info level this is important
			self._logger.info("LaserSafetyNotice: confirmation response: (%s) %s, submissionDate: %s, showAgain: %s, full response: %s",
							  httpCode, responseCode, submissionDate, show_again, responseFull)
		else:
			self._logger.info("LaserSafetyNotice: confirmation already sent. showAgain: %s", show_again)
			self.setUserSetting(username, self.USER_SETTINGS_KEY_LASERSAFETY_CONFIRMATION_SHOW_AGAIN, show_again)

		if needSubmission and not successfullySubmitted:
			return make_response("Failed to submit laser safety confirmation to cloud.", 901)
		else:
			return NO_CONTENT

	# simpleApiCommand: custom_materials;
	def custom_materials(self, data):

		# self._logger.info("custom_material() request: %s", data)
		res = dict(
			custom_materials=[],
			put=0,
			deleted=0)

		try:
			if 'delete' in data:
				materials(self).delete_custom_material(data['delete'])

			if 'put' in data and isinstance(data['put'],dict):
				for key, m in data['put'].iteritems():
					materials(self).put_custom_material(key, m)

			res['custom_materials'] = materials(self).get_custom_materials()

		except:
			self._logger.exception("Exception while handling custom_materials(): ")
			return make_response("Error while handling custom_materials request.", 500)

		# self._logger.info("custom_material(): response: %s", data)
		return make_response(jsonify(res), 200)

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
		from flask import make_response, render_template
		from octoprint.server import debug, VERSION, DISPLAY_VERSION, UI_API_KEY, BRANCH

		display_version_string = "{} on {}".format(self._plugin_version, self.getHostname())
		if self._branch:
			display_version_string = "{} ({} branch) on {}".format(self._plugin_version, self._branch, self.getHostname())

		render_kwargs = dict(debug=debug,
		                     firstRun=self.isFirstRun(),
		                     version=dict(number=VERSION, display=DISPLAY_VERSION, branch=BRANCH),
		                     uiApiKey=UI_API_KEY,
		                     templates=dict(tab=[]),
		                     pluginNames=dict(),
		                     locales=dict(),
		                     supportedExtensions=[],
		                     # beamOS version
		                     beamosVersionNumber=self._plugin_version,
		                     beamosVersionBranch=self._branch,
		                     beamosVersionDisplayVersion=display_version_string,
		                     beamosVersionImage=self._octopi_info,
		                     # environement
		                     env=self.get_env(),
		                     env_local=self.get_env(self.ENV_LOCAL),
		                     env_laser_safety=self.get_env(self.ENV_LASER_SAFETY),
		                     env_analytics=self.get_env(self.ENV_ANALYTICS),
		                     #
		                     displayName=self.getDisplayName(),
		                     hostname=self.getHostname(),
		                     serial=self._serial_num,
		                     beta_label=self.get_beta_label(),
		                     e='null',
		                     gcodeThreshold=0,  #legacy
		                     gcodeMobileThreshold=0,  #legacy
		                     )
		r = make_response(render_template("initial_calibration.jinja2", **render_kwargs))

		r = add_non_caching_response_headers(r)
		return r

	### Initial Camera Calibration - START ###
	# The next two calls are needed for first-run and initial camera calibration

	@octoprint.plugin.BlueprintPlugin.route("/take_undistorted_picture", methods=["GET"])
	#@firstrun_only_access
	def takeUndistortedPictureForInitialCalibration(self):
		self._logger.info("INITIAL_CALIBRATION TAKE PICTURE")
		self.take_undistorted_picture(is_initial_calibration=True)
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
		#print profile
		xmin = '0'
		ymin = '0'
		xmax = str(profile['volume']['width'])
		ymax = str(profile['volume']['depth'])
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
				msg = "Cannot convert while lasering due to performance reasons".format(**locals())
				self._logger.error("gcodeConvertCommand: %s", msg)
				return make_response(msg, 409)

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
				msg = "Trying to slice into file that is currently being printed: {}".format(gcode_name)
				self._logger.error("gcodeConvertCommand: %s", msg)
				make_response(msg, 409)

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
				msg = "Profile {profile} doesn't exist".format(**locals())
				self._logger.error("gcodeConvertCommand: %s", msg)
				return make_response(msg, 400)

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
			ready_to_laser=[],
			cli_event=["event"],
			custom_materials=[],
			analytics_init=[], # user's analytics choice froom welcome wizard
			analytics_data=['event', 'payload'], # analytics data from the frontend
			take_undistorted_picture=[],  # see also takeUndistortedPictureForInitialCalibration() which is a BluePrint route
			focus_reminder=[],
			reset_air_filter_usage=[],
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
		elif command == "custom_materials":
			return self.custom_materials(data)
		elif command == "ready_to_laser":
			return self.ready_to_laser(data)
		elif command == "camera_calibration_markers":
			return self.camera_calibration_markers(data)
		elif command == "take_undistorted_picture":
			# see also takeUndistortedPictureForInitialCalibration() which is a BluePrint route
			return self.take_undistorted_picture(is_initial_calibration=False)
		elif command == "cli_event":
			return self.cli_event(data)
		elif command == "analytics_init":
			return self.analytics_init(data)
		elif command == "analytics_data":
			return self.analytics_data(data)
		elif command == "focus_reminder":
			return self.focus_reminder(data)
		elif command == "reset_air_filter_usage":
			return self._usageHandler.reset_air_filter_usage()
		return NO_CONTENT

	def analytics_init(self, data):
		if 'analyticsInitialConsent' in data:
			self._analytics_handler.initial_analytics_procedure(data['analyticsInitialConsent'])

	def analytics_data(self, data):
		event = data.get('event')
		payload = data.get('payload', dict())
		self._analytics_handler.log_frontend_event(event, payload)
		return NO_CONTENT

	def focus_reminder(self, data):
		if 'focusReminder' in data:
			self._settings.set_boolean(["focusReminder"], data['focusReminder'])
			self._settings.save()	# This is necessary because without it the value is not saved
		return NO_CONTENT


	def cli_event(self, data):
		event = data['event']
		payload = data['payload'] if 'payload' in data else None
		self._logger.info("Firing cli_event: %s, payload: %s", event, payload)
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
		elif 'rtl_cancel' in data and data['rtl_cancel']:
			self._oneButtonHandler.unset_ready_to_laser()
		return NO_CONTENT

	def take_undistorted_picture(self, is_initial_calibration):
		self._logger.debug("New undistorted image is requested. is_initial_calibration: %s", is_initial_calibration)
		image_response = self._lid_handler.take_undistorted_picture(is_initial_calibration)
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

		self._analytics_handler.write_cam_update(newMarkers,newCorners)

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
			# self._logger.debug("Read multicolor params %s" % params)

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
			from .gcodegenerator.converter import OutOfSpaceException

			is_job_cancelled() #check before conversion started

			profile = self.laserCutterProfileManager.get_current_or_default()
			maxWidth = profile['volume']['width']
			maxHeight = profile['volume']['depth']

			#TODO implement cancelled_Jobs, to check if this particular Job has been canceled
			#TODO implement check "_cancel_job"-loop inside engine.convert(...), to stop during conversion, too
			engine = Converter(params, model_path, workingAreaWidth = maxWidth, workingAreaHeight = maxHeight, min_required_disk_space=self._settings.get(['converter_min_required_disk_space']))
			engine.convert(is_job_cancelled, on_progress, on_progress_args, on_progress_kwargs)

			is_job_cancelled() #check if canceled during conversion

			return True, None  # TODO add analysis about out of working area, ignored elements, invisible elements, text elements
		except octoprint.slicing.SlicingCancelled as e:
			self._logger.info("Conversion cancelled")
			raise e
		except OutOfSpaceException as e:
			msg = "{}: {}".format(type(e).__name__, e)
			self._logger.exception("Conversion failed: {0}".format(msg))
			return False, msg
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
			self._logger.info("on_event() %s: %s", event, payload)

		if event == OctoPrintEvents.ERROR:
			self._logger.error("on_event() Error Event! Message: %s", payload['error'])

		if event == OctoPrintEvents.CLIENT_OPENED:
			self._analytics_handler.log_client_opened(payload.get('remoteAddress', None))
			self.fire_event(MrBeamEvents.MRB_PLUGIN_VERSION, payload=dict(version=self._plugin_version))
			self._replay_stored_frontend_notification()

		if event == OctoPrintEvents.CONNECTED and 'grbl_version' in payload:
			self._grbl_version = payload['grbl_version']
			if self._grbl_version != self._settings.get(["grbl_version_lastknown"]):
				self._settings.set(["grbl_version_lastknown"], self._grbl_version, force=True)
				self._logger.info("grbl_version_lastknown updated to: %s", self._grbl_version)


	def fire_event(self, event, payload=None):
		'''
		Fire an event into octoPrint's event system and adds mrb_check as payload
		:param event:
		:param payload: payload. If None, a payload object with mrb_state is added
		'''
		if payload is None:
			payload = dict()
		if not 'mrb_state' in payload:
			payload["mrb_state"] = self.get_mrb_state()
		self._logger.info("fire_event() event:%s, payload:%s", event, payload)
		self._event_bus.fire(event, payload)


	##~~ Progress Plugin API

	def on_print_progress(self, storage, path, progress):
		# TODO: this method should be moved into printer.py or comm_acc2 or so.
		flooredProgress = progress - (progress % 10)
		if (flooredProgress != self.print_progress_last):
			self.print_progress_last = flooredProgress
			print_time = None
			lines_total = None
			lines_read = None
			lines_remaining = None
			lines_recovered = None
			if self._printer and self._printer._comm is not None:
				print_time = self._printer._comm.getPrintTime()
				lines_recovered = self._printer._comm._lines_recoverd_total
				if self._printer._comm._currentFile:
					lines_total = self._printer._comm._currentFile.getLinesTotal()
					lines_read = self._printer._comm._currentFile.getLinesRead()
					lines_remaining = self._printer._comm._currentFile.getLinesRemaining()
			payload = dict(progress=self.print_progress_last,
			               time=print_time,
			               file_lines_total=lines_total,
			               file_lines_read=lines_read,
			               file_lines_remaining=lines_remaining,
			               lines_recovered=lines_recovered,
			)
			self._event_bus.fire(MrBeamEvents.PRINT_PROGRESS, payload)

	def on_slicing_progress(self, slicer, source_location, source_path, destination_location, destination_path, progress):
		# TODO: this method should be moved into printer.py or comm_acc2 or so.
		flooredProgress = progress - (progress % 10)
		if (flooredProgress != self.slicing_progress_last):
			self.slicing_progress_last = flooredProgress
			payload = dict(progress=self.slicing_progress_last)
			self._event_bus.fire(MrBeamEvents.SLICING_PROGRESS, payload)

	##~~ Softwareupdate hook

	def get_update_information(self):
		# calling from .software_update_information import get_update_information
		return get_update_information(self)

	def get_update_branch_info(self):
		"""
		Gets you a list of plugins which are currently not configured to be updated from their default branch.
		Why do we need this? Frontend injects these data into SWupdate settings. So we can see if we put
		a component like Mr Beam Plugin to a special branch (for development.)
		:return: dict
		"""
		result = dict()
		configured_checks = None
		try:
			pluginInfo = self._plugin_manager.get_plugin_info("softwareupdate")
			if pluginInfo is not None:
				impl = pluginInfo.implementation
				configured_checks = impl._configured_checks
			else:
				self._logger.error("get_branch_info() Can't get pluginInfo.implementation")
		except Exception as e:
			self._logger.exception("Exception while reading configured_checks from softwareupdate plugin. ")

		for name, config in configured_checks.iteritems():
			if name == 'octoprint':
				continue
			if 'branch' in config and \
					(('branch_default' in config and config['branch'] != config['branch_default'])
					or (not 'branch_default' in config)):
				result[name] = config['branch']
		return result

	# inject a Laser object instead the original Printer from standard.py
	def laser_factory(self, components, *args, **kwargs):
		from octoprint_mrbeam.printing.printer import Laser
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

	def notify_frontend(self, title, text, type=None, sticky=False, delay=None, replay_when_new_client_connects=False):
		"""
		Show a frontend notification to the user. (PNotify)
		# TODO: All these messages will not be translated to any language. To change this we need:
		# TODO: - either just send an error-code to the frontend and the frontend somehow knows what texts to use
	    # TODO: - or use lazy_gettext and evaluate the resulting object here. (lazy_gettext() returns not a string but a function/object)
	    # TODO:   To do sow we need a flask request context. We could sinply keep the request context from the last request to the webpage.
	    # TODO:   This would be hacky but would work most of the time.
		:param title: title of your mesasge
		:param text: the actual text
		:param type: info, success, error, ... (default is info)
		:param sticky: True | False (default is False)
		:param delay: (int) number of seconds the notification shows until it hides (default: 10s)
		:param replay_when_new_client_connects: If True the notification will be sent to all clients when a new client connects.
				If you send the same notification (all params have identical values) it won't be sent again.
		:return:
		"""
		text = text.replace("Mr Beam II", "Mr&nbsp;Beam&nbsp;II").replace("Mr Beam", "Mr&nbsp;Beam")
		notification = dict(
			title= title,
			text= text,
			type=type,
			sticky=sticky,
			delay=delay
		)

		send = True
		if replay_when_new_client_connects:
			my_hash = hash(frozenset(notification.items()))
			existing = next((item for item in self._stored_frontend_notifications if item["h"] == my_hash), None)
			if existing is None:
				notification['h'] = my_hash
				self._stored_frontend_notifications.append(notification)
			else:
				send =False

		if send:
			self._plugin_manager.send_plugin_message("mrbeam", dict(frontend_notification = notification))

	def _replay_stored_frontend_notification(self):
		# all currently connected clients will get this notification again
		for n in self._stored_frontend_notifications:
			self.notify_frontend(title = n['title'], text = n['text'], type= n['type'], sticky = n['sticky'], replay_when_new_client_connects=False)

	def get_mrb_state(self):
		"""
		Returns the data set 'mrb_state' which we add to the periodic status messages
		and almost all events which are sent to the frontend.
		Called (among others) by LaserStateMonitor.get_current_data in printer.py
		:return: mrb_state
		:rtype: dict
		"""
		try:
			return dict(
				laser_temp = self._temperatureManager.get_temperature(),
				fan_connected = self._dustManager.is_fan_connected(),
				fan_state = self._dustManager.get_fan_state(),
				fan_rpm = self._dustManager.get_fan_rpm(),
				fan_dust = self._dustManager.get_dust(),
				lid_fully_open = self._lid_handler.is_lid_open(),
				interlocks_closed = self._ioBeam.is_interlock_closed(),
				interlocks_open_ids = self._ioBeam.open_interlocks(),
				rtl_mode = self._oneButtonHandler.is_ready_to_laser(),
				pause_mode = self._printer.is_paused(),
				cooling_mode = self._temperatureManager.is_cooling(),
				dusting_mode = self._dustManager.is_dust_mode,
				state = self._printer.get_state_string(),

			)
		except:
			if not self.is_boot_grace_period():
				self._logger.exception("Exception while collecting mrb_state data: ")
			return None

	def _getCurrentFile(self):
		currentJob = self._printer.get_current_job()
		if currentJob is not None and "file" in currentJob.keys() and "name" in currentJob["file"] and "origin" in \
				currentJob["file"]:
			return currentJob["file"]["origin"], currentJob["file"]["name"]
		else:
			return None, None

	def getHostname(self):
		"""
		Returns device hostname like 'MrBeam2-F930'.
		If system hostname (/etc/hostname) is differen it'll be set (overwritten!!) to the value from device_info
		:return: String hostname
		"""
		if self._hostname is None:
			hostname_dev_info = self._get_val_from_device_info('hostname')
			hostname_socket = None
			try:
				hostname_socket = socket.gethostname()
			except:
				self._logger.exception("Exception while reading hostname from socket.")
				pass

			# yes, let's go with the actual host name untill changes have applied.
			self._hostname = hostname_socket

			if hostname_dev_info != hostname_socket:
				self._logger.warn("getHostname() Hostname from device_info file does NOT match system hostname. device_info: {dev_info}, system hostname: {sys}. Setting system hostname to {dev_info}"
				                  .format(dev_info=hostname_dev_info, sys=hostname_socket))
				exec_cmd("sudo /root/scripts/change_hostname {}".format(hostname_dev_info))
				exec_cmd("sudo /root/scripts/change_apname {}".format(hostname_dev_info))
				self._logger.warn("getHostname() system hostname got changed to: {}. Requires reboot to take effect!".format(hostname_dev_info))


		return self._hostname

	def getDisplayName(self):
		code = None
		name = "Mr Beam II {}"
		preFix = "MrBeam2-"
		hostName = self.getHostname()
		if hostName.startswith(preFix):
			code = hostName.replace(preFix, "")
			return name.format(code)
		else:
			return name.format(hostName)

	def getSerialNum(self):
		"""
		Gives you the device's Mr Beam serieal number eg "00000000E79B0313-2C"
		The value is soley read from device_info file (/etc/mrbeam)
		and it's cached once read.
		:return: serial number
		:rtype: String
		"""
		if self._serial_num is None:
			self._serial_num = self._get_val_from_device_info('serial')
		return self._serial_num

	def getBranch(self):
		"""
		DEPRECATED
		:return:
		"""
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
		if not self._device_info:
			ok = None
			try:
				db = dict()
				with open(self.DEVIE_INFO_FILE, 'r') as f:
					for line in f:
						line = line.strip()
						token = line.split('=')
						if len(token) >= 2:
							db[token[0]] = token[1]
					ok = True
			except Exception as e:
				ok = False
				self._logger.error("Can't read device_info_file '%s' due to exception: %s", self.DEVIE_INFO_FILE, e)
			if ok:
				self._device_info = db
		return self._device_info.get(key, None)


	def isFirstRun(self):
		return self._settings.global_get(["server", "firstRun"])

	def is_boot_grace_period(self):
		return self._boot_grace_period_counter < self.BOOT_GRACE_PERIOD

	def _start_boot_grace_period_thread(self):
		my_timer = threading.Timer(1.0, self._callback_boot_grace_period_thread)
		my_timer.daemon = True
		my_timer.name = "boot_grace_period_timer"
		my_timer.start()

	def _callback_boot_grace_period_thread(self):
		try:
			self._boot_grace_period_counter += 1
			if self._boot_grace_period_counter < self.BOOT_GRACE_PERIOD:
				self._start_boot_grace_period_thread()
		except:
			self._logger.exception("Exception in _callback_boot_grace_period_thread()")

	def is_prod_env(self, type=None):
		return self.get_env(type).upper() == self.ENV_PROD

	def is_dev_env(self, type=None):
		return self.get_env(type).upper() == self.ENV_DEV

	def get_env(self, type=None):
		result = self._settings.get(["dev", "env"]).upper()
		if type is not None:
			if type == self.ENV_LASER_SAFETY:
				type_env = self._settings.get(["dev", "cloud_env"]) # deprected flag
			else:
				type_env = self._settings.get(["dev", "env_overrides", type])
			if type_env is not None:
				result = type_env
		return result

	def get_beta_label(self):
		chunks = []
		if self._settings.get(['beta_label']):
			chunks.append(self._settings.get(['beta_label']))
		if self.is_beta_channel():
			chunks.append('<a href="https://mr-beam.freshdesk.com/support/solutions/articles/43000507827" target="_blank">BETA</a>')
		if self.is_vorlon_enabled():
			chunks.append("VORLON")
		if self.support_mode:
			chunks.append("SUPPORT")

		return " | ".join(chunks)

	def is_time_ntp_synced(self):
		return self._time_ntp_synced


	def start_time_ntp_timer(self):
		self.__calc_time_ntp_offset(log_out_of_sync=True)


	def __calc_time_ntp_offset(self, log_out_of_sync=False):
		"""
		Checks if we have a NTP time and if the offsett is < 1min.
		- If not, this function is called again. The first times with 10s delay, then 120sec.
		- If yes, this fact is logged with a shift_time wich indicates the time the device was off from ntp utc time
		    Technically it's the difference in time between the time that should have passed theoratically and
		    that actually passed due to invisible ntp corrections.
		:param log_out_of_sync: do not log if time is not synced
		"""
		ntp_offset = None
		max_offset = 60000 #miliseconds
		now = time.time()
		try:
			# ntpq_out, code = exec_cmd_output("ntpq -p", shell=True, log_cmd=False)
			# self._logger.debug("ntpq -p:\n%s", ntpq_out)
			cmd = "ntpq -pn | /usr/bin/awk 'BEGIN { ntp_offset=%s } $1 ~ /^\*/ { ntp_offset=$9 } END { print ntp_offset }'" % max_offset
			output, code = exec_cmd_output(cmd, shell=True, log_cmd=False)
			try:
				ntp_offset = float(output)
			except:
				# possible output: "ntpq: read: Connection refused"
				ntp_offset = None
				pass
			if ntp_offset == max_offset:
				ntp_offset = None
		except:
			self._logger.exception("__calc_time_ntp_offset() Exception while reading ntpq data.")

		local_time_shift = 0.0
		interval_last = self.TIME_NTP_SYNC_CHECK_INTERVAL_FAST if self._time_ntp_check_count <= self.TIME_NTP_SYNC_CHECK_FAST_COUNT else self.TIME_NTP_SYNC_CHECK_INTERVAL_SLOW
		interval_next = self.TIME_NTP_SYNC_CHECK_INTERVAL_FAST if self._time_ntp_check_count < self.TIME_NTP_SYNC_CHECK_FAST_COUNT else self.TIME_NTP_SYNC_CHECK_INTERVAL_SLOW
		if self._time_ntp_check_last_ts > 0.0:
			local_time_shift = now - self._time_ntp_check_last_ts - interval_last # if there was no shift, this should sum up to zero
		self._time_ntp_shift += local_time_shift
		self._time_ntp_synced = ntp_offset is not None
		during_realtime = self.TIME_NTP_SYNC_CHECK_INTERVAL_FAST * min(self._time_ntp_check_count, self.TIME_NTP_SYNC_CHECK_FAST_COUNT) + self.TIME_NTP_SYNC_CHECK_INTERVAL_SLOW * max(0, self._time_ntp_check_count - self.TIME_NTP_SYNC_CHECK_FAST_COUNT)

		msg = "is_time_ntp_synced: {synced}, time_shift: {time_shift:.2f}s, during_realtime: {during_realtime:.2f}s (checks: {checks}, local_time_shift: {local_time_shift:.2f})".format(
			synced = self._time_ntp_synced,
			time_shift = self._time_ntp_shift,
			during_realtime = during_realtime,
			checks = self._time_ntp_check_count,
			local_time_shift = local_time_shift)

		if self._time_ntp_synced or log_out_of_sync:
			self._logger.info(msg)

		self._time_ntp_check_last_ts = now
		self._time_ntp_check_count += 1

		if not self._time_ntp_synced:
			if not self._shutting_down:
				real_wait_time = interval_next - (time.time()-now)
				timer = threading.Timer(real_wait_time, self.__calc_time_ntp_offset)
				timer.daemon = True
				timer.start()

	def is_beta_channel(self):
		return self._settings.get(["dev", "software_tier"]) == SW_UPDATE_TIER_BETA

	def is_vorlon_enabled(self):
		vorlon = self._settings.get(['vorlon'])
		ts = -1
		if vorlon == True:
			# usually we get a timestamp here. if it's a true-Boolean, it was entered manually and we keep it forever.
			return True
		if not vorlon:
			return False
		try:
			ts = float(vorlon)
		except:
			pass
		if ts > 0 and time.time() - ts < float(60 * 60 * 6):
			return True
		else:
			self._settings.set_boolean(['vorlon'], False, force=True)
			return False




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
			_disabled=['cura', 'pluginmanager', 'announcements', 'corewizard', 'octopi_support']   # accepts dict | pfad.yml | callable
		),
		terminalFilters = [
			dict(name="Filter beamOS messages", regex="^([0-9,.: ]+ [A-Z]+ mrbeam)", activated=True),
			dict(name="Filter _COMM_ messages", regex="^([0-9,.: ]+ _COMM_)", activated=False),
			dict(name="Filter _COMM_ except Gcode", regex="^([0-9,.: ]+ _COMM_: (Send: \?|Recv: ok|Recv: <))", activated=False),
		],
		appearance=dict(components=dict(
			order=dict(
				wizard=["plugin_mrbeam_wifi", "plugin_mrbeam_acl", "plugin_mrbeam_lasersafety",
				        "plugin_mrbeam_whatsnew_0", "plugin_mrbeam_whatsnew_1", "plugin_mrbeam_whatsnew_2", "plugin_mrbeam_whatsnew_3", "plugin_mrbeam_whatsnew_4",
				        "plugin_mrbeam_analytics"],
				settings = ['plugin_mrbeam_about', 'plugin_softwareupdate', 'accesscontrol', 'plugin_netconnectd', 'plugin_findmymrbeam', 'plugin_mrbeam_conversion',
				            'plugin_mrbeam_camera', 'plugin_mrbeam_airfilter', 'plugin_mrbeam_analytics', 'plugin_mrbeam_reminders', 'logs', 'plugin_mrbeam_debug']
			),
			disabled=dict(
				wizard=['plugin_softwareupdate'],
				settings=['serial', 'webcam', 'terminalfilters']
			)
		)),
		server = dict(commands=dict(
			serverRestartCommand = "sudo systemctl restart octoprint.service",
			systemRestartCommand = "sudo shutdown -r now",
			systemShutdownCommand = "sudo shutdown -h now"
		))
		# )),
		# system=dict(actions=[
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
		"octoprint.cli.commands": get_cli_commands

	}

