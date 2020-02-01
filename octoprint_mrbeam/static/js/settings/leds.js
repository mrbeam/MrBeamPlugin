/*
 * View model for Mr Beam
 *
 * Author: Teja Philipp <teja@mr-beam.org>
 * License: AGPLv3
 */
/* global OctoPrint, OCTOPRINT_VIEWMODELS */

$(function () {
	function LedsViewModel(parameters) {
		var self = this;
		self.settings = parameters[0];

		self.edge_brightness = ko.observable(255);
		self.edge_brightness.extend({ rateLimit: { timeout: 500, method: "notifyWhenChangesStop" } });
		self.edge_brightness.subscribe(function(val){
			let br = parseInt(val);
			OctoPrint.simpleApiCommand("mrbeam", "leds", {brightness: br});
			self.settings.settings.plugins.mrbeam.leds.brightness(val);
			self.settings.saveData(undefined, function(newSettings){
				console.log("Saved LEDs edge brightness", newSettings.plugins.mrbeam.leds.brightness);
			});
		});
		
		self.leds_fps = ko.observable(28);
		self.leds_fps.extend({ rateLimit: { timeout: 500, method: "notifyWhenChangesStop" } });
		self.leds_fps.subscribe(function(val){
			let fps = parseInt(val);
			OctoPrint.simpleApiCommand("mrbeam", "leds", {fps: fps});
			self.settings.settings.plugins.mrbeam.leds.fps(val);
			self.settings.saveData(undefined, function(newSettings){
				console.log("Saved LEDs fps", newSettings.plugins.mrbeam.leds.fps);
			});
		});

		// set config values once settings have been loaded.
		self.onAllBound = function(data){
			let br = self.settings.settings.plugins.mrbeam.leds.brightness();
			self.edge_brightness(br);
			console.warn("init LED brightness (edges)", br);
			let fps = self.settings.settings.plugins.mrbeam.leds.fps();
			self.leds_fps(fps);
			console.log("init LED fps (edges)", fps);
		}

	}

	// view model class, parameters for constructor, container to bind to
	OCTOPRINT_VIEWMODELS.push([
		LedsViewModel,

		// e.g. loginStateViewModel, settingsViewModel, ...
		["settingsViewModel"],

		// e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
		["#settings_plugin_mrbeam_leds"]
	]);
});
