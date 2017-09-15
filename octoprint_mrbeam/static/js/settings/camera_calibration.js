/*
 * View model for Mr Beam
 *
 * Author: Teja Philipp <teja@mr-beam.org>
 * License: AGPLv3
 */
/* global OctoPrint, OCTOPRINT_VIEWMODELS */

$(function () {
	function CameraCalibrationViewModel(parameters) {
		var self = this;

		self.staticURL = "/plugin/mrbeam/static/img/cam_calib_static.jpg";

		self.workingArea = parameters[1];
		self.conversion = parameters[2];
		self.scaleFactor = 6;
		// todo get ImgUrl from Backend/Have it hardcoded but right
		self.calImgUrl = ko.observable(self.staticURL);
		self.calImgWidth = ko.observable(1024);
		self.calImgHeight = ko.observable(768);
		self.calSvgOffX = ko.observable(0);
		self.calSvgOffY = ko.observable(0);
		self.calSvgScale = ko.observable(1);
		self.calibrationActive = ko.observable(false);
		self.calibrationComplete = ko.observable(false);
		self.markerNW = ko.observable(['?', '?']);
		self.markerSW = ko.observable(['?', '?']);
		self.markerSE = ko.observable(['?', '?']);
		self.markerNE = ko.observable(['?', '?']);


		self.calSvgViewBox = ko.computed(function () {
			var w = self.calImgWidth() / self.calSvgScale();
			var h = self.calImgHeight() / self.calSvgScale();
			return [self.calSvgOffX(), self.calSvgOffY(), w, h].join(' ');
		});
		self.currentMarker = 0;
		self.currentResults = {};
		self.currentMarkersFound = {};

		self.calibrationSteps = [
			{name: 'start', desc: 'click to start', focus: [0, 0, 1]},
			{name: 'NW', desc: 'North West', focus: [0, 0, self.scaleFactor]},
			{name: 'SW', desc: 'North East', focus: [0, self.calImgHeight(), self.scaleFactor]},
			{name: 'SE', desc: 'South East', focus: [self.calImgWidth(), self.calImgHeight(), self.scaleFactor]},
			{name: 'NE', desc: 'South West', focus: [self.calImgWidth(), 0, self.scaleFactor]}
		];

		self.startCalibration = function () {
			self.currentResults = {};
			self.loadUndistortedPicture(function(){
				
				self.calibrationActive(true);
				self.calibrationComplete(false);
			});
		};

		self.userClick = function (vm, ev) {
			// check if picture is loaded
            if(self.calImgUrl() === self.staticURL){
                console.log("Please Take new Picture or wait till its loaded...");
                return;
            }

			var cPos = self._getClickPos(ev);

			// save current stepResult
			var step = self.calibrationSteps[self.currentMarker];
			if (self.currentMarker > 0) {
				var x = Math.round(cPos.xImg);
				var y = Math.round(cPos.yImg);
				self.currentResults[step.name] = {'x': x, 'y': y};
				switch (step.name) {
					case 'NW':
						self.markerNW([x, y])
						break;
					case 'SW':
						self.markerSW([x, y])
						break;
					case 'SE':
						self.markerSE([x, y])
						break;
					case 'NE':
						self.markerNE([x, y])
						break;
				}
			}

			//check if finished and send result if true
			self.currentMarker = (self.currentMarker + 1) % self.calibrationSteps.length;
			if (self.currentMarker === 0) {
				self.calibrationComplete(true);
				self.calImgUrl(self.staticURL);
				$('#calibration_box').removeClass('up').removeClass('down');
			}

			// update for next step
			var nextStep = self.calibrationSteps[self.currentMarker];
			self.zoomTo(nextStep.focus[0], nextStep.focus[1], nextStep.focus[2]);
		};

		self._getClickPos = function (ev) {

			var bbox = ev.target.parentElement.getBoundingClientRect();
			var clickpos = {
				xScreenPx: ev.clientX - bbox.left,
				yScreenPx: ev.clientY - bbox.top
			};
			clickpos.xRel = clickpos.xScreenPx / bbox.width;
			clickpos.yRel = clickpos.yScreenPx / bbox.height;
			clickpos.xImg = self.calSvgOffX() + clickpos.xRel * (self.calImgWidth() / self.calSvgScale());
			clickpos.yImg = self.calSvgOffY() + clickpos.yRel * (self.calImgHeight() / self.calSvgScale());

			return clickpos;
		};

		self.zoomTo = function (x, y, scale) {
			self.calSvgScale(scale);
			var w = self.calImgWidth() / scale;
			var h = self.calImgHeight() / scale;
			var offX = Math.min(Math.max(x - w / scale, 0), self.calImgWidth() - w);
			var offY = Math.min(Math.max(y - h / scale, 0), self.calImgHeight() - h);
			self.calSvgOffX(offX);
			self.calSvgOffY(offY);
		};

		self.onStartup = function () {
//            console.log("CameraCalibrationViewModel.onStartup()");
		};

		self.loadUndistortedPicture = function (callback) {
			console.log("New picture requested.");
			var success_callback = function(resp){ 
					if(callback) callback(resp);
					else console.log("Undistorted picture loaded");
			};
			var error_callback = function (response) {
				var notifyType;
				var notifyTitle;
				if (response.status === 200) {  // should never be 200 when failing ?? TODO
					notifyType = 'success';
					notifyTitle = 'Success';
				} else {
					notifyType = 'warning';
					notifyTitle = 'Error';
				}
				console.log(notifyTitle, response.responseText);
				new PNotify({
					title: notifyTitle,
					text: response.responseText,
					type: notifyType,
					hide: true
				});
			};
			if (self.isInitialCalibration()) {
				$.ajax({
					type: "GET",
					url: '/plugin/mrbeam/take_undistorted_picture',
					data: {},
					success: success_callback,
					error: error_callback
				});
			} else {
				OctoPrint.simpleApiCommand("mrbeam", "take_undistorted_picture", {})
					.done(success_callback)
					.fail(error_callback);
			}
		};

		self.onDataUpdaterPluginMessage = function (plugin, data) {
			if (plugin !== "mrbeam" || !data)
				return;
			if ('beam_cam_new_image' in data) {
				if (data['beam_cam_new_image']['undistorted_saved']) {
					console.log("Update imgURL");
					self.calImgUrl('/downloads/files/local/cam/undistorted.jpg' + '?' + new Date().getTime());
					self.currentMarkersFound = data['beam_cam_new_image']['markers_found'];
					if (self.currentMarkersFound === {}) {
						console.log("ERROR NO MARKERS FOUND IN PICTURE, PLEASE TAKE PIC AGAIN")
						new PNotify({
							title: gettext("Error"),
							text: gettext("No Markers found/no Data about Markers. Please take picture again. Canceling calibration."),
							type: "warning",
							hide: true
						});
						self.calibrationActive(false);
						self.calibrationComplete(false);
					} else {
						console.log("Markers Found here:", self.currentMarkersFound);
					}
				}
			}
		};


		self.engrave_markers = function () {
			var url = '/plugin/mrbeam/generate_calibration_markers_svg';
			$.ajax({
				type: "POST",
				url: url,
				data: {},
				success: function (data) {
					console.log("generated_markers_svg", data);
					var fileObj = {
						"date": Math.floor(Date.now() / 1000),
						"hash": "_generic_",
						"name": "CalibrationMarkers.svg",
						"origin": "local",
						"path": "CalibrationMarkers.svg",
						"refs": {
							"download": "/downloads/files/local/CalibrationMarkers.svg",
							"resource": "/api/files/local/CalibrationMarkers.svg"
						},
						"size": 594,
						"type": "model",
						"typePath": [
							"model",
							"svg"
						]
					};
					// put it on the working area
					self.workingArea.placeSVG(fileObj);
					// start conversion
					self.conversion.show_conversion_dialog();
				},
				error: function (jqXHR, textStatus, errorThrown) {
					alert("Error, status = " + textStatus + ", " +
							"error thrown: " + errorThrown
							);
				}
			});
		};


		self.isInitialCalibration = function () {
			return (typeof INITIAL_CALIBRATION !== 'undefined' && INITIAL_CALIBRATION === true);
		};


		self.saveCalibrationData = function () {
			var data = {
				result: {
					newMarkers: self.currentMarkersFound,
					newCorners: self.currentResults
				}
			};
			console.log('Sending data:', data);
			if (self.isInitialCalibration()) {
				$.ajax({
					url: "/plugin/mrbeam/send_calibration_markers",
					type: "POST",
					headers: {
						"Accept": "application/json; charset=utf-8",
						"Content-Type": "application/json; charset=utf-8"
					},
					data: JSON.stringify(data),
					dataType: "json", 
					success: self.saveMarkersSuccess,
					error: self.saveMarkersError
				});
			} else {
				OctoPrint.simpleApiCommand("mrbeam", "camera_calibration_markers", data)
					.done(self.saveMarkersSuccess)
					.fail(self.saveMarkersError);
			}
		};
		
		self.saveMarkersSuccess = function (response) {
			self.calibrationActive(false);
			self.calibrationComplete(false);
			new PNotify({
				title: gettext("BAM! markers are sent."),
				text: gettext("Cool, eh?"),
				type: "success",
				hide: true
			});
		};

		self.saveMarkersError = function () {
			self.calibrationActive(false);
			self.calibrationComplete(false);
			new PNotify({
				title: gettext("Couldn't send image markers."),
				text: gettext("...and I have no clue why."),
				type: "warning",
				hide: true
			});
		};

		self.outOfWay = function(vm,ev){
			if(!self.calibrationComplete()){
				var y = ev.screenY;
				var h = screen.height;
				var box = $('#calibration_box');
				if(y < h/2){
					box.removeClass('up');
					box.addClass('down');
				} else {
					box.removeClass('down');
					box.addClass('up');
				}
			}
		};

		self.next = function () {
			var current = $('.calibration_step.active');
			current.removeClass('active');
			var next = current.next('.calibration_step');
			if (next.length === 0) {
				next = $('#calibration_step_1');
			}
			next.addClass('active');
		};

	}

	// view model class, parameters for constructor, container to bind to
	OCTOPRINT_VIEWMODELS.push([
		CameraCalibrationViewModel,

		// e.g. loginStateViewModel, settingsViewModel, ...
		["settingsViewModel", "workingAreaViewModel", "vectorConversionViewModel"],

		// e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
		["#settings_plugin_mrbeam_camera"]
	]);
});
