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

		self.staticURL = "/plugin/mrbeam/static/img/cam_calibration/calpic_wait.svg";
		self.croppedUrl = '/downloads/files/local/cam/beam-cam.jpg';
		self.camImgPath = self.staticURL;
		self.edge_brightness = ko.observable(self.settings.settings.plugins.mrbeam.leds.brightness);
		self.edge_brightness.extend({ rateLimit: { timeout: 500, method: "notifyWhenChangesStop" } });
		self.edge_brightness.subscribe(function(val){
			let br = parseInt(val);
			OctoPrint.simpleApiCommand("mrbeam", "leds_brightness", {brightness: br});
		});

//		// brightness realtime adjust
//		window.mrbeam.leds_brightness = function(val){
//			let br = parseInt(val);
//			OctoPrint.simpleApiCommand("mrbeam", "leds_brightness", {brightness: br});
//
//		}

		self.onDataUpdaterPluginMessage = function (plugin, data) {
			if (plugin !== "mrbeam" || !data)
				return;
//			if('mrb_state' in data){
//				self.interlocks_closed(data['mrb_state']['interlocks_closed']);
//				self.lid_fully_open(data['mrb_state']['lid_fully_open']);
//			}

		};





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
