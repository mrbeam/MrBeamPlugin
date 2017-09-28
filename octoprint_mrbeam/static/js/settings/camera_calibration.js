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

		self.staticURL = "/plugin/mrbeam/static/img/cam_calibration/calpic_wait.svg";

		self.workingArea = parameters[1];
		self.conversion = parameters[2];
		self.scaleFactor = 6;
		// todo get ImgUrl from Backend/Have it hardcoded but right
		self.calImgUrl = ko.observable(self.staticURL);
		self.calImgWidth = ko.observable(2048);
		self.calImgHeight = ko.observable(1536);
		self.calSvgOffX = ko.observable(0);
		self.calSvgOffY = ko.observable(0);
		self.calSvgScale = ko.observable(1);
		self.calibrationActive = ko.observable(false);
		self.currentResults = ko.observable({});
		self.cal_img_ready = ko.computed(function(){ return self.calImgUrl() !== self.staticURL; });
		self.calibrationComplete = ko.computed(function(){
			var markers = ['NW', 'NE', 'SW', 'SE'];
			for (var i = 0; i < markers.length; i++) {
				var k = markers[i];
				var m = self.currentResults()[k];
				if(typeof m === 'undefined' || isNaN(m.x) || isNaN(m.y)){
					return false;
				}
			}
			return true;
		});
		self.foundNW = ko.observable(false);
		self.foundSW = ko.observable(false);
		self.foundSE = ko.observable(false);
		self.foundNE = ko.observable(false);


		self.__format_point = function(p){
			if(typeof p === 'undefined') return '?,?';
			else return p.x+','+p.y;
		};


		self.calSvgViewBox = ko.computed(function () {
			var w = self.calImgWidth() / self.calSvgScale();
			var h = self.calImgHeight() / self.calSvgScale();
			return [self.calSvgOffX(), self.calSvgOffY(), w, h].join(' ');
		});
		self.currentMarker = 0;
		self.currentMarkersFound = {};

		self.calibrationMarkers = [
			{name: 'start', desc: 'click to start', focus: [0, 0, 1]},
			{name: 'NW', desc: 'North West', focus: [0, 0, self.scaleFactor]},
			{name: 'SW', desc: 'North East', focus: [0, self.calImgHeight(), self.scaleFactor]},
			{name: 'SE', desc: 'South East', focus: [self.calImgWidth(), self.calImgHeight(), self.scaleFactor]},
			{name: 'NE', desc: 'South West', focus: [self.calImgWidth(), 0, self.scaleFactor]}
		];

		self.startCalibration = function () {
			self.currentResults({});
			self.calibrationActive(true);
			self.nextMarker();
		};

		self.nextMarker = function(){
			self.currentMarker = (self.currentMarker + 1) % self.calibrationMarkers.length;
			if(!self.calibrationComplete() && self.currentMarker === 0) self.currentMarker = 1;
			var nextStep = self.calibrationMarkers[self.currentMarker];
			self._highlightStep(nextStep);
		};
		self.previousMarker = function(){
			var i = self.currentMarker - 1;
			if(!self.calibrationComplete() && i === 0) i = -1;
			if(i < 0) i = self.calibrationMarkers.length - 1;
			self.currentMarker = i;
			var nextStep = self.calibrationMarkers[self.currentMarker];
			self._highlightStep(nextStep);
		};

		self.userClick = function (vm, ev) {
			// check if picture is loaded
			if(window.location.href.indexOf('localhost') === -1)
				if(self.calImgUrl() === self.staticURL){
					console.log("Please wait until camera image is loaded...");
					return;
				}

			if(self.calibrationComplete() || !self.calibrationActive()) return;

			// save current stepResult
			var step = self.calibrationMarkers[self.currentMarker];
			if (self.currentMarker > 0) {
				var cPos = self._getClickPos(ev);
				var x = Math.round(cPos.xImg);
				var y = Math.round(cPos.yImg);
				var tmp = self.currentResults();
				tmp[step.name] = {'x': x, 'y': y};
				self.currentResults(tmp);
				$('#click_'+step.name).attr({cx:x, cy:y});
			}

			if (self.currentMarker === 0) {
				self.calImgUrl(self.staticURL);
				$('#calibration_box').removeClass('up').removeClass('down');
			}
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

		self._highlightStep = function(step){
			$('.cal-row').removeClass('active');
			$('#'+step.name).addClass('active');
			self._zoomTo(step.focus[0], step.focus[1], step.focus[2]);
		}

		self._zoomTo = function (x, y, scale) {
			self.calSvgScale(scale);
			var w = self.calImgWidth() / scale;
			var h = self.calImgHeight() / scale;
			var offX = Math.min(Math.max(x - w / scale, 0), self.calImgWidth() - w);
			var offY = Math.min(Math.max(y - h / scale, 0), self.calImgHeight() - h);
			self.calSvgOffX(offX);
			self.calSvgOffY(offY);
		};

		self.onStartupComplete = function () {
//            console.log("CameraCalibrationViewModel.onStartup()");
			if(self.isInitialCalibration()){
				self.loadUndistortedPicture();
			}
		};

		self.loadUndistortedPicture = function (callback) {
			var success_callback = function(resp){
				if(typeof callback === 'function') callback(resp);
				else console.log("Calibration picture requested.");
			};
			var error_callback = function (resp) {
				var notifyType;
				var notifyTitle;
				if (resp.status === 200) {  // should never be 200 when failing ?? TODO
					notifyType = 'success';
					notifyTitle = 'Success';
				} else {
					notifyType = 'warning';
					notifyTitle = 'Error';
				}
				new PNotify({
					title: notifyTitle,
					text: resp.responseText,
					type: notifyType,
					hide: true
				});
				if(typeof callback === 'function') callback(resp);
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
				var markers = data['beam_cam_new_image']['markers_found'];
				if(!self.cal_img_ready()){
					['NW', 'SW', 'SE', 'NE'].forEach(function(d){
						self.foundNW(markers[d] && markers[d].recognized);
					});
				}
				if (data['beam_cam_new_image']['undistorted_saved']) {
					console.log("Update imgURL");
					self.calImgUrl('/downloads/files/local/cam/undistorted.jpg' + '?' + new Date().getTime());
					self.currentMarkersFound = markers;
					if (self.currentMarkersFound === {}) {
						console.log("ERROR NO MARKERS FOUND IN PICTURE, PLEASE TAKE PIC AGAIN")
						new PNotify({
							title: gettext("Error"),
							text: gettext("No Markers found/no Data about Markers. Please take picture again. Canceling calibration."),
							type: "warning",
							hide: true
						});
						self.calibrationActive(false);
					} else {
						console.log("Markers Found here:", self.currentMarkersFound);
					}
				}
			}
		};


		self.engrave_markers = function () {
			var url = '/plugin/mrbeam/generate_calibration_markers_svg';
			$.ajax({
				type: "GET",
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
					self.workingArea.placeSVG(fileObj, function(){
						// start conversion
						self.conversion.show_conversion_dialog();
					});
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
					newCorners: self.currentResults()
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
			new PNotify({
				title: gettext("Calibration finished."),
				text: gettext("Cool, eh?"),
				type: "success",
				hide: true
			});
			self.reset_calibration();
		};

		self.saveMarkersError = function () {
			self.calibrationActive(false);
			new PNotify({
				title: gettext("Couldn't send calibration data."),
				text: gettext("...and I have no clue why. Sorry."),
				type: "warning",
				hide: true
			});
			self.reset_calibration();
		};

		self.reset_calibration = function(){
			self.calImgUrl(self.staticURL);
			self._zoomTo(0,0,1);
			self.currentMarker = 0;
			if(self.isInitialCalibration()){
				self.loadUndistortedPicture();
			} else {
				self.goto('#calibration_step_1');
			}
			$('.calibration_click_indicator').attr({cx:-100, cy:-100});
		};

		self.continue_to_calibration = function(){
			self.loadUndistortedPicture(self.next);
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

		self.goto = function (target_id) {
			var el = $(target_id);
			if(el){
				$('.calibration_step.active').removeClass('active');
				$(target_id).addClass('active');
			} else {
				console.error('no element with id' + target_id);
			}
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
