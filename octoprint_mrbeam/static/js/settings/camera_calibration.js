/*
 * View model for Mr Beam
 *
 * Author: Teja Philipp <teja@mr-beam.org>
 * License: AGPLv3
 */
/* global OctoPrint, OCTOPRINT_VIEWMODELS */

MARKERS = ['NW', 'NE', 'SE', 'SW'];

$(function () {
	function CameraCalibrationViewModel(parameters) {
		var self = this;
		window.mrbeam.viewModels['cameraCalibrationViewModel'] = self;
		self.calibrationScreenShown = ko.observable(false)

		self.staticURL = "/plugin/mrbeam/static/img/cam_calibration/calpic_wait.svg";

		self.dbNWImgUrl = ko.observable("");
		self.dbNEImgUrl = ko.observable("");
		self.dbSWImgUrl = ko.observable("");
		self.dbSEImgUrl = ko.observable("");
		self.interlocks_closed = ko.observable(false);
		self.lid_fully_open = ko.observable(false);

		self.workingArea = parameters[1];
		self.conversion = parameters[2];
		self.analytics = parameters[3];
		self.camera = self.workingArea.camera;

		self.focusX = ko.observable(0);
		self.focusY = ko.observable(0);
		self.picType = ko.observable(""); // raw, lens_corrected, cropped
		self.correctedMarkersVisibility = ko.observable('hidden')
		self.croppedMarkersVisibility = ko.observable('hidden');
		self.calImgWidth = ko.observable(2048);
		self.calImgHeight = ko.observable(1536);
		self.picType.subscribe(function (val) {
			switch (val) {
				case 'cropped':
					var croppedUrl = self.camera.timestampedImgUrl()
					if (!croppedUrl)
						croppedUrl = self.camera.getTimestampedImageUrl(self.camera.croppedUrl)
					self.calImgUrl(croppedUrl);
					self.calImgWidth(500);
					self.calImgHeight(390);
					self.correctedMarkersVisibility('hidden');
					self.croppedMarkersVisibility('visible');
					break;
				case 'raw':
					self.calImgUrl(self.camera.getTimestampedImageUrl(self.camera.rawUrl));
					self.calImgWidth(2048);
					self.calImgHeight(1536);
					self.correctedMarkersVisibility('hidden')
					self.croppedMarkersVisibility('hidden');
					break;
				case 'lens_corrected':
					self.calImgUrl(self.camera.getTimestampedImageUrl(self.camera.undistortedUrl));
					self.calImgWidth(2048);
					self.calImgHeight(1536);
					self.correctedMarkersVisibility('visible')
					self.croppedMarkersVisibility('hidden');
					break;
				default:
					self.calImgWidth(512);
					self.calImgHeight(384);
					self.correctedMarkersVisibility('hidden')
					self.croppedMarkersVisibility('hidden');
					self.calImgUrl(self.staticURL);
			}
		});
		self.availablePic = ko.observable({'raw': false, 'lens_corrected': false, 'cropped': false, })
		self.calImgUrl = ko.observable(self.staticURL);

		self.calSvgOffX = ko.observable(0);
		self.calSvgOffY = ko.observable(0);
		self.calSvgDx = ko.observable(0);
		self.calSvgDy = ko.observable(0);
		self.calSvgScale = ko.observable(1);
		self.cornerCalibrationActive = ko.observable(false);
		self.lensCalibrationActive = ko.observable(false);
		self.currentResults = ko.observable({});
		self.cornerCalibrationComplete = ko.computed(function(){
			if (Object.keys(self.currentResults()).length !== 4) return false;
			return Object.values(self.currentResults()).reduce((x,y) => x && y);
		});
		self.cal_img_ready = ko.computed(function () {
			if (Object.keys(self.camera.markersFound()).length !== 4) return false;
			return Object.values(self.camera.markersFound()).reduce((x,y) => x && y);
		});

		self.rawPics = ko.observable([])
		self.rawPicSelection = ko.observableArray([])
		// calibrationState is constantly refreshed by the backend
		// as an immutable array that contains the whole state of the calibration
		self.calibrationState = ko.observable({})

		self.lensCalibrationRunning = ko.observable(false);
		self.markersFoundPosition = ko.observable({});

		self.__format_point = function(p){
			if(typeof p === 'undefined') return '?,?';
			else return p.x+','+p.y;
		};

		self.calSvgViewBox = ko.computed(function () {
			var zoom = self.calSvgScale();
			var w = self.calImgWidth() / zoom;
			var h = self.calImgHeight() / zoom;
			var offX = Math.min(Math.max(self.focusX() - w / zoom, 0), self.calImgWidth() - w) + self.calSvgDx();
			var offY = Math.min(Math.max(self.focusY() - h / zoom, 0), self.calImgHeight() - h) + self.calSvgDy();
			self.calSvgOffX(offX);
			self.calSvgOffY(offY);
			return [self.calSvgOffX(), self.calSvgOffY(), w, h].join(' ');
		});
		self.currentMarker = 0;

		self.zMarkersTransform = ko.computed( function () {
			// Like workArea.zObjectImgTransform(), but zooms
			// out the markers instead of the image itself
			if (self.picType() === 'cropped') {
				var offset = [self.calImgWidth(), self.calImgHeight()].map(x=>x*self.camera.imgHeightScale())
				return 'scale('+1/(1+2*self.camera.imgHeightScale())+') translate('+offset.join(' ')+')';
			}
			else return 'scale(1)';
		});


		self.calibrationMarkers = [
			{name: 'start', desc: 'click to start', focus: [0, 0, 1]},
			{name: 'NW', desc: 'North West', focus: [0, 0, 4]},
			{name: 'SW', desc: 'North East', focus: [0, self.calImgHeight(), 4]},
			{name: 'SE', desc: 'South East', focus: [self.calImgWidth(), self.calImgHeight(), 4]},
			{name: 'NE', desc: 'South West', focus: [self.calImgWidth(), 0, 4]}
		];
		self.crossSize = ko.observable(30);
		self.svgCross = ko.computed(function () {
			var s = self.crossSize()
			return `M0,${s} h${2*s} M${s},0 v${2*s} z`
		})

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


		self.startCornerCalibration = function () {
			self.analytics.send_fontend_event('corner_calibration_start', {});
			// self.currentResults({});
			self.cornerCalibrationActive(true);
			self.picType("lens_corrected");
			self.nextMarker();
		};

		self.startLensCalibration = function () {
			self.analytics.send_fontend_event('lens_calibration_start', {});
			self.picType("raw");
			self.lensCalibrationActive(true);
			self.refreshPics()
		};

		self.nextMarker = function(){
			self.currentMarker = (self.currentMarker + 1) % self.calibrationMarkers.length;
			if(!self.cornerCalibrationComplete() && self.currentMarker === 0) self.currentMarker = 1;
			var nextStep = self.calibrationMarkers[self.currentMarker];
			self._highlightStep(nextStep);
		};
		self.previousMarker = function(){
			var i = self.currentMarker - 1;
			if(!self.cornerCalibrationComplete() && i === 0) i = -1;
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

			// if(self.cornerCalibrationComplete() || !self.cornerCalibrationActive()) return;

			// save current stepResult
			var step = self.calibrationMarkers[self.currentMarker];
			if (self.currentMarker > 0) {
				var cPos = self._getClickPos(ev);
				var x = Math.round(cPos.xImg);
				var y = Math.round(cPos.yImg);
				var tmp = self.currentResults();
				tmp[step.name] = {'x': x, 'y': y};
				self.currentResults(tmp);
				$('#click_'+step.name).attr({'x':x-self.crossSize(), 'y':y-self.crossSize()});
			}

			if (self.currentMarker === 0) {
				// TODO do some zooming instead?
				// self.picType("");
				// self.calImgUrl(self.staticURL);
				// $('#calibration_box').removeClass('up').removeClass('down');
			}
		};

		self._getClickPos = function (ev) {

			var bbox = ev.target.parentElement.parentElement.getBoundingClientRect();
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
			self.calSvgScale(step.focus[2])
		}

		self.onStartupComplete = function () {
			if(self.isInitialCalibration()){
				self.loadUndistortedPicture();
				self.refreshPics();
				self.calibrationScreenShown(true)
			}
		};

		self.onSettingsShown = function(){
		    self.goto('#calibration_step_1');
        }

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
			if (!self.calibrationScreenShown()) return;
			if('mrb_state' in data){
				self.interlocks_closed(data['mrb_state']['interlocks_closed']);
				self.lid_fully_open(data['mrb_state']['lid_fully_open']);
			}

			if ('beam_cam_new_image' in data) {
				// update image
				var _d = data['beam_cam_new_image'];
				if (_d['undistorted_saved'] && ! self.cornerCalibrationActive()) {
					if (_d['available']) {
						self.availablePic(_d['available'])
						if (! ['raw', 'lens_corrected', 'cropped'].includes(self.picType())) {
							for (_type of ['lens_corrected', 'raw']) {
								if (self.availablePic()[_type]) {
									self.picType(_type);
									break;
								}
							}
						} else
							self.calImgUrl(self.camera.getTimestampedImageUrl(self.calImgUrl()));
					}

					if (self.isInitialCalibration()) {
						self.dbNWImgUrl('/downloads/files/local/cam/debug/NW.jpg' + '?ts=' + new Date().getTime());
						self.dbNEImgUrl('/downloads/files/local/cam/debug/NE.jpg' + '?ts=' + new Date().getTime());
						self.dbSWImgUrl('/downloads/files/local/cam/debug/SW.jpg' + '?ts=' + new Date().getTime());
						self.dbSEImgUrl('/downloads/files/local/cam/debug/SE.jpg' + '?ts=' + new Date().getTime());
					}

					// check if all markers are found and image is good for calibration
					if (self.cal_img_ready()) {
						// console.log("Remembering markers for Calibration", markers);
						_tmp = data['beam_cam_new_image']['markers_pos'];
						//	i, j -> x, y conversion
						['NW', 'NE', 'SE', 'SW'].forEach(function(m) {_tmp[m] = _tmp[m].reverse();} );
						self.markersFoundPosition(_tmp)
					}
					else if(self.cornerCalibrationActive()){
						console.log("Not all Markers found, are the pink circles obstructed?");
						// As long as all the corners were not found, the camera will continue to take pictures
						// self.loadUndistortedPicture();
					}
				}
			}

			if ('chessboardCalibrationState' in data) {
				var _d = data['chessboardCalibrationState']
				self.calibrationState(_d);
				var arr = []
				for (const [key, value] of Object.entries(_d.pictures)) {
					arr.push({name: key, state: value.state})
				}
				self.rawPicSelection(arr)
				self.lensCalibrationRunning(_d.lensCalibration == "processing");
			}

		};

		self.saveRawPic = function() {
				$.ajax({
					type: "GET",
					url: '/plugin/mrbeam/calibration_save_raw_pic',
					data: {},
					success: self.rawPicSuccess,
					error: self.saveRawPicError
				});
			// self.simpleApiCommand( "calibration_save_raw_pic",
			// 					   {},
			// 					   self.saveRawPicSuccess,
			// 					   self.saveRawPicError);
		}

		self.showRawPic = function() {
			var path = this['name'];
			var dl_path = path.replace("home/pi/.octoprint/uploads",
									   "downloads/files/local")
			self.picType("reserved");
			self.calImgUrl(dl_path)
		}

		self.delRawPic = function() {
			self.simpleApiCommand("calibration_del_pic",
								  {name: this['name']},
								  self.refreshPics,
								  self.delRawPicError,
								  "POST");
		}

		self.refreshPics = function() {
				$.ajax({
					type: "GET",
					url: '/plugin/mrbeam/calibration_get_raw_pic',
					data: {},
					success: self.rawPicSuccess,
					error: self.getRawPicError
				});
		}

		self.rawPicSuccess = function(response) {} // {self.rawPics(response.split(':'))}
		self.saveRawPicError = function() {self.rawPicError(gettext("Failed to save the latest image."))}
		self.delRawPicError  = function() {self.rawPicError(gettext("Failed to delete the latest image."))}
		self.getRawPicError  = function() {self.rawPicError(gettext("Failed to refresh the list of images."))}

		self.rawPicError= function(err) {
			new PNotify({
				title: err,
				text: gettext("...and I have no clue why. Sorry."),
				type: "warning",
				hide: true
			});
		}

		self.rawPicSelectOptions = ko.computed(function() {
			self.rawPicSelection.removeAll()
			if (self.rawPics().length == 1 && self.rawPics()[0] === "") return;
            for (let i = 0; i < self.rawPics().length; i++) {
                self.rawPicSelection.push({
                    id: self.rawPics()[i],
                    name: "Picture " + i
                });
			}
		})

		self.cameraBusy = ko.computed(function() {
			return self.rawPicSelection().some(elm => elm.state === "camera_processing")
		});

		self.runLensCalibration = function() {
			self.lensCalibrationRunning(true);
			self.simpleApiCommand(
				"camera_run_lens_calibration",
				{},
				function(){
					new PNotify({
						title: gettext("Calibration started"),
						text: gettext("Please relax, this will take a little while.\nWe will let you know when we are done."),
						type: "info",
						hide: false})},
				function(){
					new PNotify({
						title: gettext("Couldn't start the lens calibration."),
						text: gettext("...and I have no clue why. Sorry."),
						type: "warning",
						hide: true})},
				"POST");
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


		self.saveCornerCalibrationData = function () {
			var data = {
				result: {
					newMarkers: self.markersFoundPosition(),
					newCorners: self.currentResults()
				}
			};
			console.log('Sending data:', data);
			self.simpleApiCommand("camera_calibration_markers", data, self.saveMarkersSuccess, self.saveMarkersError);
		};

		self.saveMarkersSuccess = function (response) {
			self.cornerCalibrationActive(false);
			self.analytics.send_fontend_event('cornerCalibration_finish', {});
			new PNotify({
				title: gettext("Camera Calibrated."),
				text: gettext("Camera calibration was successful."),
				type: "success",
				hide: true
			});
			if(self.isInitialCalibration()) self.resetView();
			else self.goto('#calibration_step_1');
		};

		self.saveMarkersError = function () {
			self.cornerCalibrationActive(false);
			new PNotify({
				title: gettext("Couldn't send calibration data."),
				text: gettext("...and I have no clue why. Sorry."),
				type: "warning",
				hide: true
			});
			if(self.isInitialCalibration()) self.resetView();
			else self.reset_cornerCalibration();
		};

		self.abortCalibration = function () {
			if (self.cornerCalibrationActive()) {
				self.cornerCalibrationActive(false);
				self.rawPics([])
			}
			if (self.lensCalibrationActive(false)) {
					self.lensCalibrationActive(false);
				new PNotify({
					title: gettext("Calibration cancelled."),
					text: gettext("Feel free to restart"),
					type: "info",
					hide: true
				});
				self.reset_corner_calibration();
			}
		};

		self.resetView = function () {
			self.picType("lens_corrected");
			self.focusX(0);
			self.focusY(0);
			self.calSvgScale(1);
			self.currentMarker = 0;
		};

		self.reset_corner_calibration = function () {
			self.resetView();
			self.markersFoundPosition({});
			self.currentResults({});
			if (!self.isInitialCalibration())
				self.goto('#calibration_step_1');
			$('.calibration_click_indicator').attr({'x': -100, 'y': -100});
		};

		self.continue_to_calibration = function () {
			self.loadUndistortedPicture(self.next);
			self.calibrationScreenShown(true)
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

		self.simpleApiCommand = function(command, data, successCallback, errorCallback, type) {
			if (self.isInitialCalibration()) {
				$.ajax({
					url: "/plugin/mrbeam/" + command,
					type: type, // POST, GET
					headers: {
						"Accept": "application/json; charset=utf-8",
						"Content-Type": "application/json; charset=utf-8"
					},
					data: JSON.stringify(data),
					dataType: "json",
					success: successCallback,
					error: errorCallback
				});
			}
			else {
				OctoPrint.simpleApiCommand("mrbeam", command, data)
						.done(successCallback)
						.fail(errorCallback);
			}
		}

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
