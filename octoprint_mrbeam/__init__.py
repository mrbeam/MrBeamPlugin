# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
from octoprint.util import dict_merge
from octoprint.server import NO_CONTENT

from .profile import LaserCutterProfileManager, InvalidProfileError, CouldNotOverwriteError

import copy
from octoprint.server.util.flask import restricted_access
from octoprint.filemanager import ContentTypeDetector, ContentTypeMapping
from flask import Blueprint, request, jsonify, make_response, url_for


class MrBeamPlugin(octoprint.plugin.SettingsPlugin,
                   octoprint.plugin.AssetPlugin,
				   octoprint.plugin.UiPlugin,
                   octoprint.plugin.TemplatePlugin,
				   octoprint.plugin.BlueprintPlugin):

	def __init(self):
		self.laserCutterProfileManager = None

	def initialize(self):
		self.laserCutterProfileManager = LaserCutterProfileManager(self._settings)

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
			current_profile_id = "_mrbeam_junior",
			defaultIntensity = 500,
			defaultFeedrate = 300,
			svgDPI = 90,
			svgtogcode_debug_logging = False,
		)

	def on_settings_load(self):
		return dict(
			current_profile_id = self._settings.get(["current_profile_id"]),
			defaultIntensity = self._settings.get(['defaultIntensity']),
			defaultFeedrate = self._settings.get(['defaultFeedrate']),
			svgDPI = self._settings.get(['svgDPI']),
			svgtogcode_debug_logging = self._settings.get(['svgtogcode_debug_logging']),
		)

	def on_settings_save(self, data):
		if "workingAreaWidth" in data and data["workingAreaWidth"]:
			self._settings.set(["workingAreaWidth"], data["workingAreaWidth"])
		if "zAxis" in data:
			self._settings.set_boolean(["zAxis"], data["zAxis"])
		selectedProfile = laserCutterProfileManager.get_current_or_default()
		self._settings.set(["current_profile_id"], selectedProfile['id'])



	##~~ AssetPlugin mixin

	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/mother_viewmodel.js", "js/mrbeam.js", "js/working_area.js", 
			"js/lib/snap.svg-min.js", "js/render_fills.js", "js/matrix_oven.js", "js/drag_scale_rotate.js", 
			"js/convert.js", "js/gcode_parser.js", "js/lib/photobooth_min.js", "js/laserSafetyNotes.js", 
			"js/lasercutterprofiles.js"],
			css=["css/mrbeam.css", "css/svgtogcode.css", "css/ui_mods.css"],
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
		
		enable_accesscontrol = self._user_manager.enabled
		accesscontrol_active = enable_accesscontrol and self._user_manager.hasBeenCustomized()

		# render_kwargs["templates"]["settings"]["entries"]["serial"][1]["template"] = "settings/serialconnection.jinja2"

		render_kwargs.update(dict(
							 webcamStream=self._settings.global_get(["webcam", "stream"]),
							 enableTemperatureGraph=False,
							 enableAccessControl=enable_accesscontrol,
							 accessControlActive=accesscontrol_active,					  
							 enableSdSupport=False,
							 gcodeMobileThreshold=0,
							 gcodeThreshold=0,
							 wizard=False,
							 now=now,
							 ))
		return make_response(render_template("mrbeam_ui_index.jinja2", **render_kwargs))

	##~~ TemplatePlugin mixin

	def get_template_configs(self):
		return [
			dict(type = 'settings', name = "Machine Profiles", template='settings/lasercutterprofiles_settings.jinja2', suffix="_lasercutterprofiles", custom_bindings = False),
			dict(type = 'settings', name = "SVG Conversion", template='settings/svgtogcode_settings.jinja2', suffix="_conversion", custom_bindings = False),
			dict(type = 'settings', name = "Serial Connection", template='settings/serialconnection_settings.jinja2', suffix='_serialconnection', custom_bindings= False, replaces='serial')
		]

	##~~ BlueprintPlugin API

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
		#except Exception as e:
		#	return make_response("Could not save profile: %s" % e.message, 500)
		else:
			return jsonify(dict(profile=_convert_profile(saved_profile)))

	@octoprint.plugin.BlueprintPlugin.route("/profiles/<string:identifier>", methods=["GET"])
	def laserCutterProfilesGet(self, identifier):
		profile = self.laserCutterProfileManager.get(identifier)
		if profile is None:
			return make_response("Unknown profile: %s" % identifier, 404)
		else:
			return jsonify(_convert_profile(profile))


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
		#except Exception as e:
		#	return make_response("Could not save profile: %s" % e.message, 500)
		else:
			return jsonify(dict(profile=_convert_profile(saved_profile)))
											 
	##~~ Softwareupdate hook
	
	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
		# for details.
		return dict(
			mrbeam=dict(
				displayName="Mrbeam Plugin",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="hungerpirat",
				repo="Mr_Beam",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/hungerpirat/Mr_Beam/archive/{target_version}.zip"
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
		
#	def serve_url(self, server_routes, *args, **kwargs):
#		from octoprint.server.util.tornado import LargeResponseHandler, path_validation_factory
#		from octoprint.util import is_hidden_path
#		return [(r"/serve/(.*)", LargeResponseHandler, 
#			dict(path=self._settings.global_get_basefolder("uploads"),
#            as_attachment=False,
#            path_validation=path_validation_factory(lambda path: not is_hidden_path(path), status_code=404)))
#		]

# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Mr Beam Plugin"


def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = MrBeamPlugin()

	global __plugin_settings_overlay__ 
	__plugin_settings_overlay__ = dict(
		plugins = dict(
			_disabled=['cura', 'pluginmanager', 'announcements']), # eats dict | pfad.yml | callable
			terminalFilters=[
				{ "name": "Suppress position requests" , "regex": "(Send: \?)" },
				{ "name": "Suppress confirmations" , "regex": "(Recv: ok)" },
				{ "name": "Suppress status messages" , "regex": "(Recv: <)" },
			],
	)

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.printer.factory": __plugin_implementation__.laser_factory,
		"octoprint.filemanager.extension_tree": __plugin_implementation__.laser_filemanager,
		#"octoprint.server.http.routes": __plugin_implementation__.serve_url
	}

