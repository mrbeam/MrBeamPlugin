# coding=utf-8
from __future__ import absolute_import

__author__ = "Gina Häußge <osd@foosel.net>"
__license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'
__copyright__ = "Copyright (C) 2014 The OctoPrint Project - Released under terms of the AGPLv3 License"


import os
import copy
import re
import collections

from octoprint.util import dict_merge, dict_clean, dict_contains_keys
from octoprint.settings import settings
from octoprint_mrbeam.mrb_logger import mrb_logger

# singleton
_instance = None
def laserCutterProfileManager():
	global _instance
	if _instance is None:
		_instance = LaserCutterProfileManager()
	return _instance


defaults = dict(
	# general settings
	svgDPI=90,
	pierce_time=0,

	# vector settings
	speed=300,
	intensity=500,
	fill_areas=False,
	engrave=False,
	set_passes=1,
	cut_outlines=True,
	cross_fill=False,
	fill_angle=0,
	fill_spacing=0.25,

	# pixel settings
	beam_diameter=0.25,
	intensity_white=0,
	intensity_black=500,
	feedrate_white=1500,
	feedrate_black=250,
	img_contrast=1.0,
	img_sharpening=1.0,
	img_dithering=False,
	multicolor=""
)

class SaveError(Exception):
	pass

class CouldNotOverwriteError(SaveError):
	pass

class InvalidProfileError(Exception):
	pass

class LaserCutterProfileManager(object):

	SETTINGS_PATH_PROFILE_DEFAULT_ID = ['lasercutterProfiles', 'default']
	SETTINGS_PATH_PROFILE_DEFAULT_PROFILE = ['lasercutterProfiles', 'defaultProfile']
	# SETTINGS_PATH_PROFILE_CURRENT_ID = ['lasercutterProfiles', 'current']

	# old default dictionary for Mr Beam I
	# default = dict(
	# 	id = "_mrbeam_junior",
	# 	name = "Mr Beam",
	# 	model = "Junior",
	# 	volume=dict(
	# 		width = 217,
	# 		depth = 298,
	# 		height = 0,
	# 		origin_offset_x = 1.1,
	# 		origin_offset_y = 1.1,
	# 	),
	# 	zAxis = False,
	# 	focus = False,
	# 	glasses = True,
	# 	axes=dict(
	# 		x = dict(speed=5000, inverted=False),
	# 		y = dict(speed=5000, inverted=False),
	# 		z = dict(speed=1000, inverted=False)
	# 	),
	# 	start_method = None,
	# 	grbl = dict(
	# 		resetOnConnect = False,
	# 	),
	# )

	# we tried to switch to more up-to-date default profiles...
	# but then more than just one profile had the same name as the default one
	#    and that confused the whole system.... :-(
	default = dict(
		id = 'my_default',
		name = 'Dummy Laser',
		model = 'X',
		axes = dict(
			x = dict(
				inverted = False,
				speed = 5000,
				overshoot = 1,
				homing_direction_positive = True
			),
			y = dict(
				inverted = False,
				speed = 5000,
				overshoot=0,
				homing_direction_positive=True
			),
			z = dict(
				inverted = False,
				speed = 1000,
				overshoot=0,
				homing_direction_positive=True
			),
		),
		focus = True,  # false if we need to show focus tab
		glasses = False,
		start_method = 'onebutton',
		grbl = dict(
			resetOnConnect = True,
			homing_debounce = 1
		),
		laser=dict(
			max_temperature=55.0,
			hysteresis_temperature=48.0,
			cooling_duration=25, # if set to positive values: enables time based cooling resuming rather that per hysteresis_temperature
			intensity_factor=13  # to get from 100% intesity to GCODE-intensity of 1300
		),
		dust=dict(
			extraction_limit=0.70,
			auto_mode_time=60
		),
		volume = dict(
			# Grbl values $130 (x max travel) and $131 (y max travel) need to be set to:
			# x | $130:  width + working_area_shift_x + origin_offset_x
			# y | $131:  width + working_area_shift_y + origin_offset_y
			# While origin_offset_x = origin_offset_x = $27 (homing pull-off) + 0.1 !!
			depth = 390.0,
			height = 0.0,
			origin_offset_x = 1.1,
			origin_offset_y = 1.1,
			width = 500.0,
			working_area_shift_x = 0.0,
			working_area_shift_y = 0.0
		),
		zAxis = False,
		legacy = dict(
			# 2C series only
			# https: // github.com / mrbeam / MrBeamPlugin / issues / 211
			job_done_home_position_x = None
		)
	)

	def __init__(self):
		self._current = None
		self.settings = settings()
		self._folder = self.settings.getBaseFolder("printerProfiles")+"/lasercutterprofiles"
		if not os.path.exists(self._folder):
			os.makedirs(self._folder)
		self._logger = mrb_logger("octoprint.plugins.mrbeam.profile")

	def select(self, identifier):
		"""
		Selects a profile non-persistently
		:param identifier:
		:return:
		"""
		if identifier is None or not self.exists(identifier):
			self._current = self.get_default()
			return False
		else:
			self._current = self.get(identifier)
			return True

	def deselect(self):
		self._current = None

	def get_all(self):
		return self._load_all()

	def get(self, identifier):
		try:
			if identifier == "_default":
				return self._load_default()
			elif self.exists(identifier):
				return self._load_from_path(self._get_profile_path(identifier))
			else:
				return None
		except InvalidProfileError:
			return None

	def remove(self, identifier):
		if identifier == "_default":
			return False
		return self._remove_from_path(self._get_profile_path(identifier))

	def save(self, profile, allow_overwrite=False, make_default=False):
		"""
		Saves given profile to file.
		:param profile:
		:param allow_overwrite:
		:param make_default:
		:return:
		"""
		if "id" in profile and profile['id'] != '':
			identifier = profile["id"]
		elif "name" in profile:
			identifier = profile["name"]
		else:
			raise InvalidProfileError("profile must contain either id or name")

		identifier = self._sanitize(identifier)
		profile["id"] = identifier
		profile = dict_clean(profile, self.__class__.default)

		if identifier == "_default":
			default_profile = dict_merge(self._load_default(), profile)
			if not self._ensure_valid_profile(default_profile):
				raise InvalidProfileError()

			self.settings.set(self.SETTINGS_PATH_PROFILE_DEFAULT_PROFILE, default_profile, defaults=dict(lasercutterprofiles=dict(defaultProfile=self.__class__.default)))
			self.settings.save()
		else:
			self._save_to_path(self._get_profile_path(identifier), profile, allow_overwrite=allow_overwrite)

			if make_default:
				self.set_default(identifier)

		# Not sure if we want to sync to OP's PrinterprofileManager
		# _mrbeam_plugin_implementation._printer_profile_manager.save(profile, allow_overwrite, make_default)

		return self.get(identifier)

	def get_default(self):
		default = self.settings.get(self.SETTINGS_PATH_PROFILE_DEFAULT_ID)
		if default is not None and self.exists(default):
			profile = self.get(default)
			if profile is not None:
				return profile

		return self._load_default()

	def set_default(self, identifier):
		all_identifiers = self._load_all_identifiers().keys()
		if identifier is not None and not identifier in all_identifiers:
			return

		self.settings.set(self.SETTINGS_PATH_PROFILE_DEFAULT_ID, identifier, force=True)
		self.settings.save()

	def get_current_or_default(self):
		if self._current is not None:
			return self._current
		else:
			return self.get_default()

	def get_current(self):
		return self._current

	def exists(self, identifier):
		if identifier is None:
			return False
		elif identifier == "_mrbeam_junior" or identifier == "_mrbeam_senior"                                                                                                                               :
			return True
		else:
			path = self._get_profile_path(identifier)
			return os.path.exists(path) and os.path.isfile(path)

	def _load_all(self):
		all_identifiers = self._load_all_identifiers()
		results = dict()
		for identifier, path in all_identifiers.items():
			try:
				profile = self._load_from_path(path)
			except InvalidProfileError:
				continue

			if profile is None:
				continue

			results[identifier] = dict_merge(self._load_default("_mrbeam_junior"), profile)

		results["_mrbeam_junior"] = self._load_default("_mrbeam_junior")
		results["_mrbeam_senior"] = self._load_default("_mrbeam_senior")
		return results

	def _load_all_identifiers(self):
		results = dict()
		for entry in os.listdir(self._folder):
			if entry.startswith(".") or not entry.endswith(".profile") or entry == "_default.profile":
				continue

			path = os.path.join(self._folder, entry)
			if not os.path.isfile(path):
				continue

			identifier = entry[:-len(".profile")]
			results[identifier] = path
		return results

	def _load_from_path(self, path):
		if not os.path.exists(path) or not os.path.isfile(path):
			return None

		import yaml
		with open(path) as f:
			profile = yaml.safe_load(f)
		profile = self._ensure_valid_profile(profile)
		if not profile:
			self._logger.warn("Invalid profile: %s" % path)
			raise InvalidProfileError()
		profile = self._underlay_profile_with_default(profile)
		return profile

	def _save_to_path(self, path, profile, allow_overwrite=False):
		validated_profile = self._ensure_valid_profile(profile)
		if not validated_profile:
			raise InvalidProfileError()

		if os.path.exists(path) and not allow_overwrite:
			raise SaveError("Profile %s already exists and not allowed to overwrite" % profile["id"])

		import yaml
		with open(path, "wb") as f:
			try:
				yaml.safe_dump(profile, f, default_flow_style=False, indent="  ", allow_unicode=True)
			except Exception as e:
				raise SaveError("Cannot save profile %s: %s" % (profile["id"], e.message))

	def _remove_from_path(self, path):
		try:
			os.remove(path)
			return True
		except:
			return False

	def _load_default(self, defaultModel = None):
		default = copy.deepcopy(self.__class__.default)
		if(defaultModel is not None and defaultModel == "_mrbeam_senior"):
			default['volume']['width'] *= 2
			default['volume']['depth'] *= 2
			default['model'] = "Senior"
			default['id'] = "_mrbeam_senior"

		profile = self._ensure_valid_profile(default)
		if not profile:
			self._logger.warn("Invalid default profile after applying overrides")
			raise InvalidProfileError()
		return profile

	def _get_profile_path(self, identifier):
		return os.path.join(self._folder, "%s.profile" % identifier)

	def _sanitize(self, name):
		if name is None:
			return None

		if "/" in name or "\\" in name:
			raise ValueError("name must not contain / or \\")

		import string
		valid_chars = "-_.() {ascii}{digits}".format(ascii=string.ascii_letters, digits=string.digits)
		sanitized_name = ''.join(c for c in name if c in valid_chars)
		sanitized_name = sanitized_name.replace(" ", "_")
		return sanitized_name

	def _ensure_valid_profile(self, profile):
		# # ensure all keys are present
		# if not dict_contains_keys(self.default, profile):
		# 	return False

		# conversion helper
		def convert_value(profile, path, converter):
			value = profile
			for part in path[:-1]:
				if not isinstance(value, dict) or not part in value:
					raise RuntimeError("%s is not contained in profile" % ".".join(path))
				value = value[part]

			if not isinstance(value, dict) or not path[-1] in value:
				raise RuntimeError("%s is not contained in profile" % ".".join(path))

			value[path[-1]] = converter(value[path[-1]])


		# convert ints
		for path in (("axes", "x", "speed"), ("axes", "y", "speed"), ("axes", "z", "speed")):
			try:
				convert_value(profile, path, int)
			except:
				return False

		# convert floats
		for path in (("volume", "width"), ("volume", "depth"), ("volume", "height")):
			try:
				convert_value(profile, path, float)
			except:
				return False

		# convert booleans
		for path in (("axes", "x", "inverted"), ("axes", "y", "inverted"), ("axes", "z", "inverted")):
			try:
				convert_value(profile, path, bool)
			except:
				return False

		return profile

	def _underlay_profile_with_default(self, profile):
		return update(self._load_default(), profile)

def update(d, u):
	for k, v in u.iteritems():
		if isinstance(v, collections.Mapping):
			r = update(d.get(k, {}), v)
			d[k] = r
		else:
			d[k] = u[k]
	return d



class Profile(object):
	regex_extruder_offset = re.compile("extruder_offset_([xy])(\d)")
	regex_filament_diameter = re.compile("filament_diameter(\d?)")
	regex_print_temperature = re.compile("print_temperature(\d?)")
	regex_strip_comments = re.compile(";.*$", flags=re.MULTILINE)

	@classmethod
	def from_svgtogcode_ini(cls, path):
		import os
		if not os.path.exists(path) or not os.path.isfile(path):
			return None

		import ConfigParser
		config = ConfigParser.ConfigParser()
		try:
			config.read(path)
		except:
			return None

		arrayified_options = ["print_temperature", "filament_diameter", "start.gcode", "end.gcode"]
		translated_options = dict(
			inset0_speed="outer_shell_speed",
			insetx_speed="inner_shell_speed",
			layer0_width_factor="first_layer_width_factor",
			simple_mode="follow_surface",
		)
		translated_options["start.gcode"] = "start_gcode"
		translated_options["end.gcode"] = "end_gcode"
		value_conversions = dict(
			platform_adhesion={
				"None": PlatformAdhesionTypes.NONE,
				"Brim": PlatformAdhesionTypes.BRIM,
				"Raft": PlatformAdhesionTypes.RAFT
			},
			support={
				"None": SupportLocationTypes.NONE,
				"Touching buildplate": SupportLocationTypes.TOUCHING_BUILDPLATE,
				"Everywhere": SupportLocationTypes.EVERYWHERE
			},
			support_type={
				"Lines": SupportTypes.LINES,
				"Grid": SupportTypes.GRID
			},
			support_dual_extrusion={
				"Both": SupportDualTypes.BOTH,
				"First extruder": SupportDualTypes.FIRST,
				"Second extruder": SupportDualTypes.SECOND
			}
		)

		result = dict()
		for section in config.sections():
			if not section in ("profile", "alterations"):
				continue

			for option in config.options(section):
				ignored = False
				key = option

				# try to fetch the value in the correct type
				try:
					value = config.getboolean(section, option)
				except:
					# no boolean, try int
					try:
						value = config.getint(section, option)
					except:
						# no int, try float
						try:
							value = config.getfloat(section, option)
						except:
							# no float, use str
							value = config.get(section, option)
				index = None

				for opt in arrayified_options:
					if key.startswith(opt):
						if key == opt:
							index = 0
						else:
							try:
								# try to convert the target index, e.g. print_temperature2 => print_temperature[1]
								index = int(key[len(opt):]) - 1
							except ValueError:
								# ignore entries for which that fails
								ignored = True
						key = opt
						break
				if ignored:
					continue

				if key in translated_options:
					# if the key has to be translated to a new value, do that now
					key = translated_options[key]

				if key in value_conversions and value in value_conversions[key]:
					value = value_conversions[key][value]

				if index is not None:
					# if we have an array to fill, make sure the target array exists and has the right size
					if not key in result:
						result[key] = []
					if len(result[key]) <= index:
						for n in xrange(index - len(result[key]) + 1):
							result[key].append(None)
					result[key][index] = value
				else:
					# just set the value if there's no array to fill
					result[key] = value

		# merge it with our default settings, the imported profile settings taking precedence
		return cls.merge_profile(result)

	@classmethod
	def merge_profile(cls, profile, overrides=None):
		import copy

		result = copy.deepcopy(defaults)
		for k in result.keys():
			profile_value = None
			override_value = None

			if k in profile:
				profile_value = profile[k]
			if overrides and k in overrides:
				override_value = overrides[k]

			if profile_value is None and override_value is None:
				# neither override nor profile, no need to handle this key further
				continue

			# just change the result value to the override_value if available, otherwise to the profile_value if
			# that is given, else just leave as is
			if override_value is not None:
				result[k] = override_value
			elif profile_value is not None:
				result[k] = profile_value
		return result

	def __init__(self, profile):
		self.profile = profile

	def get(self, key):
		if key in self.profile:
			return self.profile[key]
		elif key in defaults:
			return defaults[key]
		else:
			return None

	def get_int(self, key, default=None):
		value = self.get(key)
		if value is None:
			return default

		try:
			return int(value)
		except ValueError:
			return default

	def get_float(self, key, default=None):
		value = self.get(key)
		if value is None:
			return default

		if isinstance(value, (str, unicode, basestring)):
			value = value.replace(",", ".").strip()

		try:
			return float(value)
		except ValueError:
			return default

	def get_boolean(self, key, default=None):
		value = self.get(key)
		if value is None:
			return default

		if isinstance(value, bool):
			return value
		elif isinstance(value, (str, unicode, basestring)):
			return value.lower() == "true" or value.lower() == "yes" or value.lower() == "on" or value == "1"
		elif isinstance(value, (int, float)):
			return value > 0
		else:
			return value == True

	def get_microns(self, key, default=None):
		value = self.get_float(key, default=None)
		if value is None:
			return default
		return int(value * 1000)

	def convert_to_engine(self):

		settings = {
			"--engraving-laser-speed": self.get_int("speed"),
			"--laser-intensity": self.get_int("intensity"),
			"--beam-diameter": self.get_float("beam_diameter"),
			"--img-intensity-white": self.get_int("intensity_white"),
			"--img-intensity-black": self.get_int("intensity_black"),
			"--img-speed-white": self.get_int("feedrate_white"),
			"--img-speed-black": self.get_int("feedrate_black"),
			"--pierce-time": self.get_float("pierce_time"),
			"--contrast": self.get_float("img_contrast"),
			"--sharpening": self.get_float("img_sharpening"),
			"--img-dithering": self.get_boolean("img_dithering")
		}

		return settings

	def convert_to_engine2(self):
		# engrave is mirrored fill area, needs to be removed in next iteration
		settings = {
			"engraving_laser_speed": self.get_int("speed"),
			"laser_intensity": self.get_int("intensity"),
			"beam_diameter": self.get_float("beam_diameter"),
			"intensity_white": self.get_int("intensity_white"),
			"intensity_black": self.get_int("intensity_black"),
			"speed_white": self.get_int("feedrate_white"),
			"speed_black": self.get_int("feedrate_black"),
			"pierce_time": self.get_float("pierce_time"),
			"contrast": self.get_float("img_contrast"),
			"sharpening": self.get_float("img_sharpening"),
			"dithering": self.get_boolean("img_dithering"),
			"fill_areas": self.get_boolean("fill_areas"),
			"engrave": self.get_boolean("fill_areas"),
			"set_passes": self.get_int("set_passes"),
			"cut_outlines": self.get_boolean("cut_outlines"),
			"cross_fill": self.get_boolean("cross_fill"),
			"fill_angle": self.get_float("fill_angle"),
			"fill_spacing": self.get_float("fill_spacing"),
			"svgDPI": self.get_float("svgDPI")
		}

		return settings
