# coding=utf-8
from __future__ import absolute_import

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.

import octoprint.plugin

class MrBeamPlugin(octoprint.plugin.SettingsPlugin,
                   octoprint.plugin.AssetPlugin,
				   octoprint.plugin.UiPlugin,
                   octoprint.plugin.TemplatePlugin):

	##~~ AssetPlugin mixin

	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/mother_viewmodel.js", "js/mrbeam.js", "js/working_area.js", 
			"js/lib/snap.svg-min.js", "js/render_fills.js", "js/matrix_oven.js", "js/drag_scale_rotate.js", 
			"js/convert.js", "js/gcode_parser.js", "js/lib/photobooth_min.js", "js/laserSafetyNotes.js"],
			css=["css/mrbeam.css", "css/svgtogcode.css"],
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

	def laser_factory(self, components):
		from .printer import Laser
		return Laser(components['file_manager'], components['analysis_queue'], components['printer_profile_manager'])




# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Mr Beam Plugin"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = MrBeamPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.printer.factory": __plugin_implementation__.laser_factory
	}

