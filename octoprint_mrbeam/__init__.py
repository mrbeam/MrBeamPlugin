# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
from octoprint.util import dict_merge
from octoprint.server import NO_CONTENT

from .profile import LaserCutterProfileManager, InvalidProfileError, CouldNotOverwriteError, Profile
# from .state.ledstrips import LEDstrips

import copy
import time
import os
import logging
import socket
import threading
import json
from octoprint.server.util.flask import restricted_access, get_json_command_from_request
from octoprint.filemanager import ContentTypeDetector, ContentTypeMapping
from flask import Blueprint, request, jsonify, make_response, url_for




class MrBeamPlugin(octoprint.plugin.SettingsPlugin,
                   octoprint.plugin.AssetPlugin,
				   octoprint.plugin.UiPlugin,
                   octoprint.plugin.TemplatePlugin,
				   octoprint.plugin.BlueprintPlugin,
				   octoprint.plugin.SimpleApiPlugin,
				   octoprint.plugin.EventHandlerPlugin,
				   octoprint.plugin.ProgressPlugin,
				   octoprint.plugin.SlicerPlugin):

	def __init__(self):
		self.laserCutterProfileManager = None
		self._slicing_commands = dict()
		self._slicing_commands_mutex = threading.Lock()
		self._cancelled_jobs = []
		self._cancelled_jobs_mutex = threading.Lock()
		# self.stateHandler = LEDstrips()
		self._MULTICOLOR_PARAMS_PATH = "/tmp/multicolor_parameters.json" #TODO add proper path there

	def initialize(self):
		self.laserCutterProfileManager = LaserCutterProfileManager(self._settings)
		self._log = logging.getLogger("octoprint.plugins.mrbeam")

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
			showlasersafety = False,
			glasses = False,
			camera_offset_x = 0,
			camera_offset_y = 0,
			camera_scale = 1,
			camera_rotation = 0
		)

	def on_settings_load(self):
		return dict(
			current_profile_id = self._settings.get(["current_profile_id"]),
			defaultIntensity = self._settings.get(['defaultIntensity']),
			defaultFeedrate = self._settings.get(['defaultFeedrate']),
			svgDPI = self._settings.get(['svgDPI']),
			svgtogcode_debug_logging = self._settings.get(['svgtogcode_debug_logging']),
			showlasersafety = self._settings.get(['showlasersafety']),
			glasses = self._settings.get(['glasses']),
			camera_offset_x = self._settings.get(['camera_offset_x']),
			camera_offset_y = self._settings.get(['camera_offset_y']),
			camera_scale = self._settings.get(['camera_scale']),
			camera_rotation = self._settings.get(['camera_rotation']),
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
			js=["js/lasercutterprofiles.js","js/mother_viewmodel.js", "js/mrbeam.js","js/color_classifier.js","js/working_area.js", "js/camera.js",
			"js/lib/snap.svg-min.js", "js/render_fills.js", "js/matrix_oven.js", "js/drag_scale_rotate.js",
			"js/convert.js", "js/gcode_parser.js", "js/lib/photobooth_min.js", "js/laserSafetyNotes.js", "js/svg_cleaner.js"],
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

		selectedProfile = self.laserCutterProfileManager.get_current_or_default()
		enable_focus = selectedProfile["focus"]
		safety_glasses = selectedProfile["glasses"]
		# render_kwargs["templates"]["settings"]["entries"]["serial"][1]["template"] = "settings/serialconnection.jinja2"

		render_kwargs.update(dict(
							 webcamStream = self._settings.global_get(["webcam", "stream"]),
							 enableFocus = enable_focus,
							 safetyGlasses = safety_glasses,
							 enableTemperatureGraph = False,
							 enableAccessControl = enable_accesscontrol,
							 accessControlActive = accesscontrol_active,
							 enableSdSupport = False,
							 gcodeMobileThreshold = 0,
							 gcodeThreshold = 0,
							 wizard = False,
							 now = now,
							 ))
		return make_response(render_template("mrbeam_ui_index.jinja2", **render_kwargs))

	##~~ TemplatePlugin mixin

	def get_template_configs(self):
		return [
			dict(type = 'settings', name = "Machine Profiles", template='settings/lasercutterprofiles_settings.jinja2', suffix="_lasercutterprofiles", custom_bindings = False),
			dict(type = 'settings', name = "SVG Conversion", template='settings/svgtogcode_settings.jinja2', suffix="_conversion", custom_bindings = False),
			dict(type = 'settings', name = "Camera Calibration", template='settings/camera_settings.jinja2', suffix="_camera", custom_bindings = True),
			dict(type = 'settings', name = "Serial Connection", template='settings/serialconnection_settings.jinja2', suffix='_serialconnection', custom_bindings= False, replaces='serial')
		]

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
		#except Exception as e:
		#	return make_response("Could not save profile: %s" % e.message, 500)
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
		#except Exception as e:
		#	return make_response("Could not save profile: %s" % e.message, 500)
		else:
			return jsonify(dict(profile=self._convert_profile(saved_profile)))

	@octoprint.plugin.BlueprintPlugin.route("/convert", methods=["POST"])
	@restricted_access
	def gcodeConvertCommand(self):
		target = "local";

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
				return make_response("Cannot convert while lasering due to performance reasons".format(**locals()),
									 409)

			import os
			if "gcode" in data.keys() and data["gcode"]:
				gcode_name = data["gcode"]
				del data["gcode"]
			else:
				name, _ = os.path.splitext(filename)
				gcode_name = name + ".gco"

			# append number if file exists
			name, ext = os.path.splitext(gcode_name)
			i = 1;
			while (self._file_manager.file_exists(target, gcode_name)):
				gcode_name = name + '.' + str(i) + ext
				i += 1

			# prohibit overwriting the file that is currently being printed
			currentOrigin, currentFilename = self._getCurrentFile()
			if currentFilename == gcode_name and currentOrigin == target and (
						self._printer.is_printing() or self._printer.is_paused()):
				make_response("Trying to slice into file that is currently being printed: %s" % gcode_name, 409)

#			if "profile" in data.keys() and data["profile"]:
#				profile = data["profile"]
#				del data["profile"]
#			else:
#				profile = None
			##
#			if "printerProfile" in data.keys() and data["printerProfile"]:
#				printerProfile = data["printerProfile"]
#				del data["printerProfile"]
#			else:
#				printerProfile = None
#
#			if "position" in data.keys() and data["position"] and isinstance(data["position"], dict) and "x" in \
#					data[
#						"position"] and "y" in data["position"]:
#				position = data["position"]
#				del data["position"]
#			else:
#				position = None

			select_after_slicing = False
#			if "select" in data.keys() and data["select"] in valid_boolean_trues:
#				if not printer.is_operational():
#					return make_response("Printer is not operational, cannot directly select for printing", 409)
#				select_after_slicing = True

			print_after_slicing = False
#			if "print" in data.keys() and data["print"] in valid_boolean_trues:
#				if not printer.is_operational():
#					return make_response("Printer is not operational, cannot directly start printing", 409)
#				select_after_slicing = print_after_slicing = True

			#get profile information out of data json
			override_keys = [k for k in data if k.startswith("profile.") and data[k] is not None]
			overrides = dict()
			for key in override_keys:
				overrides[key[len("profile."):]] = data[key]
			overrides['multicolor'] = data['multicolor']

			with open(self._MULTICOLOR_PARAMS_PATH, 'w') as outfile:
				json.dump(data, outfile)
				self._log.info('Wrote job parameters to %s', self._MULTICOLOR_PARAMS_PATH)

			#get color information out of data json
#			override_color_keys = [k for k in data if k.startswith("colors.") and data[k] is not None]
#			color_overrides = dict()
#			for key in override_color_keys:
#				colorKey = key[len("colors."):len("colors.#000000")]
#				if colorKey == 'undefin': break
#				color_overrides[colorKey] = {'intensity' : data['colors.'+colorKey+'.intensity'],
#											 'speed': data['colors.'+colorKey+'.speed'],
#											 'cut': data['colors.'+colorKey+'.cut']}
#				print ('color_overrides', color_overrides)
			#color_overrides = data['multicolor']
			self._printer.set_colors(currentFilename, data['multicolor'])
	
			self._log.debug('### BEFORE CALLBACK %s', str(data['multicolor']))

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

			#files = {}
			location = "test"#url_for(".readGcodeFile", target=target, filename=gcode_name, _external=True)
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


	##~~ SimpleApiPlugin mixin

	def get_api_commands(self):
		return dict(
			position=["x", "y"],
			feedrate=["value"],
			intensity=["value"],
			passes=["value"]
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

		self._log.info("### Slicing %s to %s using profile stored at %s, %s" % (model_path, machinecode_path, profile_path, self._MULTICOLOR_PARAMS_PATH))

		#profile = Profile(self._load_profile(profile_path))
		#params = profile.convert_to_engine2()

		# READ PARAMS FROM JSON
		params = dict()
		with open(self._MULTICOLOR_PARAMS_PATH) as data_file:    
			params = json.load(data_file)
			#self._log.debug("Read multicolor params %s" % params)

		dest_dir, dest_file = os.path.split(machinecode_path)
		params['directory'] = dest_dir
		params['file'] = dest_file
		params['noheaders'] = "true"  # TODO... booleanify

		params['fill_areas'] = False  # disabled as highly experimental
		if (self._settings.get(["debug_logging"])):
			log_path = homedir + "/.octoprint/logs/svgtogcode.log"
			params['log_filename'] = log_path
		else:
			params['log_filename'] = ''

		params['log_filename'] = '/tmp/test.log'
		self._log.info("params ###")
		self._log.info(params)
		
		## direct call
		from .gcodegenerator.converter import Converter
		enginex = Converter(params, model_path)
		enginex.convert(on_progress, on_progress_args, on_progress_kwargs)
			
		#self._log.info("### converter init %s" % enginex)
		#from .gcodegenerator.mrbeam import Laserengraver
		#from .gcodegenerator.mrbeam_multicolor import Laserengraver
		#engine = Laserengraver(params, model_path)
			#engine.set_laser_params(params['multicolor'])
		#engine.affect(on_progress, on_progress_args, on_progress_kwargs)
		try:

			self._log.info("### Conversion finished")
			return True, None  # TODO add analysis about out of working area, ignored elements, invisible elements, text elements
		except octoprint.slicing.SlicingCancelled as e:
			self._log.info("### _cancel 1")
			raise e
#		except Exception as e:
#			self._log.info("### _exception")
#			print e.__doc__
#			print e.message
#			self._log.exception("Conversion error ({0}): {1}".format(e.__doc__, e.message))
#			return False, "Unknown error, please consult the log file"

		finally:
			with self._cancelled_jobs_mutex:
				if machinecode_path in self._cancelled_jobs:
					self._cancelled_jobs.remove(machinecode_path)
			with self._slicing_commands_mutex:
				if machinecode_path in self._slicing_commands:
					del self._slicing_commands[machinecode_path]

			self._log.info("-" * 40)

	def cancel_slicing(self, machinecode_path):
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
		#self._log.debug("on_event %s: %s", event, payload)
		# self.stateHandler.on_state_change(event)
		pass

	##~~ Progress Plugin API

	def on_print_progress(self, storage, path, progress):
		state = "progress:"+str(progress)
		# self.stateHandler.on_state_change(state)

	def on_slicing_progress(self, slicer, source_location, source_path, destination_location, destination_path, progress):
		state = "slicing:"+str(progress)
		# self.stateHandler.on_state_change(state)

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

	def get_update_information(self):
		return dict(
			updateplugindemo=dict(
				displayName=self._plugin_name,
				displayVersion=self._plugin_version,

				type="github_release",
				current=self._plugin_version,
				user="mrbeam",
				repo="MrBeamPlugin",

				pip="https://github.com/mrbeam/MrBeamPlugin/archive/{target_version}.zip"
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


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Mr Beam Laser Cutter"


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
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.server.http.bodysize": __plugin_implementation__.bodysize_hook
		#"octoprint.server.http.routes": __plugin_implementation__.serve_url
	}

