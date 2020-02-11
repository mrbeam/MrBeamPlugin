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
		self.rawUrl = '/downloads/files/local/cam/beam-cam-tmp.jpg';
		self.undistortedUrl = '/downloads/files/local/cam/undistorted.jpg';
		self.croppedUrl = '/downloads/files/local/cam/beam-cam.jpg';
		self.camImgPath = self.staticURL;

		self.dbNWImgUrl = ko.observable("");
		self.dbNEImgUrl = ko.observable("");
		self.dbSWImgUrl = ko.observable("");
		self.dbSEImgUrl = ko.observable("");
		self.interlocks_closed = ko.observable(false);
		self.lid_fully_open = ko.observable(false);

		self.workingArea = parameters[1];
		self.conversion = parameters[2];
		self.analytics = parameters[3];

		self.zoomIn = ko.observable(false);
		self.focusX = ko.observable(0);
		self.focusY = ko.observable(0);
		self.picType = ko.observable(""); // raw, lens_correction, cropped
		self.picType.subscribe(function (val) {
			switch (val) {
				case 'cropped':
					self.camImgPath = self.croppedUrl;
					break;
				case 'raw':
					self.camImgPath = self.rawUrl;
					break;
				case 'lens_correction':
					self.camImgPath = self.undistortedUrl;
					break;
				default:
					self.camImgPath = self.staticURL;
			}
			self.calImgUrl(self.camImgPath + "?" + new Date().getTime());
		});
		// todo get ImgUrl from Backend/Have it hardcoded but right
		self.calImgUrl = ko.observable(self.staticURL);

		self.calImgWidth = ko.observable(2048);
		self.calImgHeight = ko.observable(1536);
		self.calSvgOffX = ko.observable(0);
		self.calSvgOffY = ko.observable(0);
		self.calSvgDx = ko.observable(0);
		self.calSvgDy = ko.observable(0);
		self.calSvgScale = ko.observable(4);
		self.calibrationActive = ko.observable(false);
		self.currentResults = ko.observable({});
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

		self.cal_img_ready = ko.computed(function () {
//			console.log("cal_img_ready: ", self.foundNE() , self.foundNW() , self.foundSE() , self.foundSW());
			return self.foundNE() && self.foundNW() && self.foundSE() && self.foundSW();
		});

		self.__format_point = function(p){
			if(typeof p === 'undefined') return '?,?';
			else return p.x+','+p.y;
		};


		self.calSvgViewBox = ko.computed(function () {
			var zoom = self.zoomIn() ? self.calSvgScale() : 1;
			var w = self.calImgWidth() / zoom;
			var h = self.calImgHeight() / zoom;
			var offX = Math.min(Math.max(self.focusX() - w / zoom, 0), self.calImgWidth() - w) + self.calSvgDx();
			var offY = Math.min(Math.max(self.focusY() - h / zoom, 0), self.calImgHeight() - h) + self.calSvgDy();
			self.calSvgOffX(offX);
			self.calSvgOffY(offY);
			return [self.calSvgOffX(), self.calSvgOffY(), w, h].join(' ');
		});
		self.currentMarker = 0;
		self.currentMarkersFound = {};

		self.calibrationMarkers = [
			{name: 'start', desc: 'click to start', focus: [0, 0, false]},
			{name: 'NW', desc: 'North West', focus: [0, 0, true]},
			{name: 'SW', desc: 'North East', focus: [0, self.calImgHeight(), true]},
			{name: 'SE', desc: 'South East', focus: [self.calImgWidth(), self.calImgHeight(), true]},
			{name: 'NE', desc: 'South West', focus: [self.calImgWidth(), 0, true]}
		];

		self.larger = function(){
			var val = Math.min(self.calSvgScale() + 1, 10);
			self.calSvgScale(val);
		}
		self.smaller = function(){
			var val = Math.max(self.calSvgScale() - 1, 1);
			self.calSvgScale(val);
		}
		self.move = function(dx, dy){
			self.calSvgDx(self.calSvgDx()+dx);
			self.calSvgDy(self.calSvgDy()+dy);
		}
		self.resetMove = function(){
			self.calSvgDx(0);
			self.calSvgDy(0);
		}


		self.startCalibration = function () {
			self.analytics.send_fontend_event('calibration_start', {});
			self.currentResults({});
			self.calibrationActive(true);
			self.picType("lens_correction");
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

			// if(self.calibrationComplete() || !self.calibrationActive()) return;

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
				self.picType("");
//				self.calImgUrl(self.staticURL);
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
			self.focusX(step.focus[0]);
			self.focusY(step.focus[1]);
			self.zoomIn(step.focus[2])
		}

		self.onStartupComplete = function () {
//            console.log("CameraCalibrationViewModel.onStartup()");
			if(self.isInitialCalibration()){
				self.loadUndistortedPicture();
			}
		};

		self.loadUndistortedPicture = function (callback) {
			var success_callback = function (data) {
				new PNotify({
					title: gettext("Picture requested"),
					text: data['msg'],
					type: 'info',
					hide: true
				});
				if (typeof callback === 'function')
					callback(data);
				else
					console.log("Calibration picture requested.");
			};
			var error_callback = function (resp) {
				new PNotify({
					title: gettext("Something went wrong. It's not you, it's us."),
					text: resp.responseText,
					type: 'warning',
					hide: true
				});
				if (typeof callback === 'function')
					callback(resp);
			};
			if (self.isInitialCalibration()) {
				// only accessible during initial calibration
				$.ajax({
					type: "GET",
					url: '/plugin/mrbeam/take_undistorted_picture',
					data: {},
					success: success_callback,
					error: error_callback
				});
			} else {
				// requires user to be logged in
				OctoPrint.simpleApiCommand("mrbeam", "take_undistorted_picture", {})
						.done(success_callback)
						.fail(error_callback);
			}
		};


		self.onDataUpdaterPluginMessage = function (plugin, data) {
			if (plugin !== "mrbeam" || !data)
				return;
			if('mrb_state' in data){
//				console.log('machine state', data['mrb_state']);
				self.interlocks_closed(data['mrb_state']['interlocks_closed']);
//				self.fan_connected(data['fan_connected']);
				self.lid_fully_open(data['mrb_state']['lid_fully_open']);
//				self.machine_state(data['state']);
//				self.pause_mode(data['pause_mode']);
//				self.file_lines_total(data['file_lines_total']);
//				self.file_lines_read(data['file_lines_read']);
//				console.log(data);
			}

			if ('beam_cam_new_image' in data) {
				//console.log('New Image [NW,NE,SW,SE]:', data['beam_cam_new_image']);
				// update markers
				var markers = data['beam_cam_new_image']['markers_found'];
				if(!self.calibrationActive()){
					self.foundNW(markers['NW'] && markers['NW'].recognized);
					self.foundNE(markers['NE'] && markers['NE'].recognized);
					self.foundSW(markers['SW'] && markers['SW'].recognized);
					self.foundSE(markers['SE'] && markers['SE'].recognized);
					self.foundNW.notifySubscribers(); // somehow doesn't trigger automatically
				}
				// update image
				if (data['beam_cam_new_image']['undistorted_saved']) {
					self.calImgUrl(self.camImgPath + '?' + new Date().getTime());

					if (self.isInitialCalibration()) {
						self.dbNWImgUrl('/downloads/files/local/cam/beam-cam-tmp2_debug_NW.jpg' + '?' + new Date().getTime());
						self.dbNEImgUrl('/downloads/files/local/cam/beam-cam-tmp2_debug_NE.jpg' + '?' + new Date().getTime());
						self.dbSWImgUrl('/downloads/files/local/cam/beam-cam-tmp2_debug_SW.jpg' + '?' + new Date().getTime());
						self.dbSEImgUrl('/downloads/files/local/cam/beam-cam-tmp2_debug_SE.jpg' + '?' + new Date().getTime());

					}

					// check if all markers are found and image is good for calibration
					if (self.cal_img_ready()) {
						console.log("Remembering markers for Calibration", markers);
						self.currentMarkersFound = markers;
					} else {
						console.log("Not all Markers found, fetching new Picture.")
						self.loadUndistortedPicture();
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
					//clear workingArea from previous designs
					self.workingArea.clear();
					// put it on the working area
					self.workingArea.placeSVG(fileObj, function () {
						// start conversion
						self.conversion.show_conversion_dialog();
					});
				},
				error: function (jqXHR, textStatus, errorThrown) {
					new PNotify({
						title: gettext("Error"),
						text: _.sprintf(gettext("Calibration failed.<br><br>Error:<br/>%(code)s %(status)s - %(errorThrown)s"), {code: jqXHR.status, status: textStatus, errorThrown: errorThrown}),
						type: "error",
						hide: false
					})
				}
			});
		};

		self.engrave_markers_without_gui = function () {
			var intensity = $('#initialcalibration_intensity').val()
			var feedrate = $('#initialcalibration_feedrate').val()
			var url = "/plugin/mrbeam/engrave_calibration_markers/" + intensity + "/" + feedrate
			$.ajax({
				type: "GET",
				url: url,
				data: {},
				success: function (data) {
					console.log("Success", url, data);

				},
				error: function (jqXHR, textStatus, errorThrown) {
					new PNotify({
						title: gettext("Error"),
						text: _.sprintf(gettext("Marker engraving failed: <br>%(errmsg)s<br>Error:<br/>%(code)s %(status)s - %(errorThrown)s"),
								{errmsg: jqXHR.responseText, code: jqXHR.status, status: textStatus, errorThrown: errorThrown}),
						type: "error",
						hide: false
					})
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
			self.analytics.send_fontend_event('calibration_finish', {});
			new PNotify({
				title: gettext("Camera Calibrated."),
				text: gettext("Camera calibration was successful."),
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

		self.abortCalibration = function () {
			self.calibrationActive(false);
			new PNotify({
				title: gettext("Calibration cancelled."),
				text: gettext("Feel free to restart"),
				type: "info",
				hide: true
			});
			self.reset_calibration();
		};

		self.reset_calibration = function () {
			self.picType("");
			self.focusX(0);
			self.focusY(0);
			self.zoomIn(false)
			self.currentMarker = 0;
			self.currentMarkersFound = {};
			self.currentResults({});
			self.foundNW(false);
			self.foundSW(false);
			self.foundSE(false);
			self.foundNE(false);
			if (self.isInitialCalibration()) {
				self.loadUndistortedPicture();
			} else {
				self.goto('#calibration_step_1');
			}
			$('.calibration_click_indicator').attr({cx: -100, cy: -100});
		};

		self.continue_to_calibration = function () {
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
			if (el) {
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
		["settingsViewModel", "workingAreaViewModel", "vectorConversionViewModel", "analyticsViewModel"],

		// e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
		["#settings_plugin_mrbeam_camera"]
	]);
});
