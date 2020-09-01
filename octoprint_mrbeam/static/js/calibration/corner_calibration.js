/*
 * View model for Mr Beam
 *
 * Author: Teja Philipp <teja@mr-beam.org>
 * License: AGPLv3
 */
/* global OctoPrint, OCTOPRINT_VIEWMODELS, INITIAL_CALIBRATION */

const DEFAULT_IMG_RES = [2048, 1536]
const CROPPED_IMG_RES = [500,390]
const LOADING_IMG_RES = [512, 384]
const STATIC_URL = "/plugin/mrbeam/static/img/calibration/calpic_wait.svg";

$(function () {
    function CornerCalibrationViewModel(parameters) {
        let self = this;
        window.mrbeam.viewModels['cornerCalibrationViewModel'] = self;
        self.calibration = parameters[0];
        self.workingArea = parameters[1];
        self.conversion = parameters[2];
        self.camera = parameters[3];

        self.cornerCalibrationActive = ko.observable(false);
        self.waitingForRefresh = ko.observable(true);
        self.availablePic = ko.observable({
            'raw': false,
            'lens_corrected': false,
            'cropped': false,
        })
        self.currentResults = ko.observable({});

        self.focusX = ko.observable(0);
		self.focusY = ko.observable(0);

        self.markersFoundPosition = ko.observable({});
        self.markersFoundPositionCopy = null;
        self.dbNWImgUrl = ko.observable("");
		self.dbNEImgUrl = ko.observable("");
		self.dbSWImgUrl = ko.observable("");
		self.dbSEImgUrl = ko.observable("");

		self.picType = ko.observable(""); // raw, lens_corrected, cropped
		self.correctedMarkersVisibility = ko.observable('hidden');
		self.croppedMarkersVisibility = ko.observable('hidden');

		self.currentMarker = 0;
		self.calibrationMarkers = [
			{name: 'start', desc: 'click to start', focus: [0, 0, 1]},
			{name: 'NW', desc: self.camera.MARKER_DESCRIPTIONS['NW'], focus: [0, 0, 4]},
			{name: 'SW', desc: self.camera.MARKER_DESCRIPTIONS['SW'], focus: [0, DEFAULT_IMG_RES[1], 4]},
			{name: 'SE', desc: self.camera.MARKER_DESCRIPTIONS['SE'], focus: [DEFAULT_IMG_RES[0], DEFAULT_IMG_RES[1], 4]},
			{name: 'NE', desc: self.camera.MARKER_DESCRIPTIONS['NE'], focus: [DEFAULT_IMG_RES[0], 0, 4]}
		];

		self.crossSize = ko.observable(30);

		self._cornerCalImgUrl = ko.observable("");

		self.calImgWidth = ko.observable(DEFAULT_IMG_RES[0]);
		self.calImgHeight = ko.observable(DEFAULT_IMG_RES[1]);
		self.calSvgOffX = ko.observable(0);
		self.calSvgOffY = ko.observable(0);
		self.calSvgDx = ko.observable(0);
		self.calSvgDy = ko.observable(0);
		self.calSvgScale = ko.observable(1);

		self._availablePicUrl = ko.observable({'default': STATIC_URL, 'raw': null, 'lens_corrected': null, 'cropped': null, })
		self.availablePicUrl = ko.computed(function() {
			var ret = self._availablePicUrl();
			var before = _.clone(ret); // shallow copy
			for (let _t of [['cropped', self.camera.croppedUrl],
							['lens_corrected', self.camera.undistortedUrl],
							['raw', self.camera.rawUrl]]) {
				if (self.availablePic()[_t[0]])
					ret[_t[0]] = (_t[0] === 'cropped')? self.camera.timestampedCroppedImgUrl()
					                                  : self.camera.getTimestampedImageUrl(_t[1]);
			}
			self._availablePicUrl(ret)
			var selectedTab = $('#camera-calibration-tabs .active a').attr('id')
			if (selectedTab === 'lenscal_tab_btn')
				return before
			else
				return ret
		})

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

		self.calImgReady = ko.computed(function () {
			if (Object.keys(self.camera.markersFound()).length !== 4) return false;
			return Object.values(self.camera.markersFound()).reduce((x,y) => x && y);
		})

        self.cornerCalImgUrl = ko.computed(function() {
			if (!self.cornerCalibrationActive()) {
				if (self.availablePic()['cropped']) {
				    self._cornerCalImgUrl(self._getImgUrl('cropped', true))
                } else {
				    self._cornerCalImgUrl(self._getImgUrl('raw', true))
                }
			}
			return self._cornerCalImgUrl()
		});

		self.cornerCalibrationComplete = ko.computed(function(){
			if (Object.keys(self.currentResults()).length !== 4) return false;
			return Object.values(self.currentResults()).reduce((x,y) => x && y);
		});

		self.zMarkersTransform = ko.computed( function () {
			// Like workArea.zObjectImgTransform(), but zooms
			// out the markers instead of the image itself
			let offset = [self.calImgWidth(), self.calImgHeight()].map(x=>x*self.camera.imgHeightScale())
			return 'scale('+1/(1+2*self.camera.imgHeightScale())+') translate('+offset.join(' ')+')';
		});

		self.svgCross = ko.computed(function () {
			let s = self.crossSize()
			return `M0,${s} h${2*s} M${s},0 v${2*s} z`
		});


		self.onStartupComplete = function () {
		    if(window.mrbeam.isWatterottMode()){
				self.loadUndistortedPicture();
			}
		};

		self.onSettingsShown = function(){
            self.abortCornerCalibration()
		};

        // todo user lens calibration: can we simplify/split this?
        self.onDataUpdaterPluginMessage = function (plugin, data) {
			if (plugin !== "mrbeam" || !data)
				return;

			if (!self.calibration.calibrationScreenShown()) {
				return;
            }

			if ('beam_cam_new_image' in data) {
				// update image
				let selectedTab = $('#camera-calibration-tabs li.active:not(li.tabdrop) a').attr('id')
				let _d = data['beam_cam_new_image'];
				if (_d['undistorted_saved'] && !self.cornerCalibrationActive()) {
					if (_d['available']) {
						self.availablePic(_d['available'])
					}

					if (window.mrbeam.isWatterottMode() && (selectedTab === "cornercal_tab_btn" || self.waitingForRefresh())) {
						self.dbNWImgUrl('/downloads/files/local/cam/debug/NW.jpg' + '?ts=' + new Date().getTime());
						self.dbNEImgUrl('/downloads/files/local/cam/debug/NE.jpg' + '?ts=' + new Date().getTime());
						self.dbSWImgUrl('/downloads/files/local/cam/debug/SW.jpg' + '?ts=' + new Date().getTime());
						self.dbSEImgUrl('/downloads/files/local/cam/debug/SE.jpg' + '?ts=' + new Date().getTime());
					}

					// check if all markers are found and image is good for calibration
					if (self.calImgReady() && !self.cornerCalibrationActive()) {
						// console.log("Remembering markers for Calibration", markers);
						let _tmp = data['beam_cam_new_image']['markers_pos'];
						//	i, j -> x, y conversion
						['NW', 'NE', 'SE', 'SW'].forEach(function(m) {_tmp[m] = _tmp[m].reverse();} );
						self.markersFoundPosition(_tmp)
					}
					else if(self.cornerCalibrationActive()){
						console.log("Not all Markers found, are the pink circles obstructed?");
						// As long as all the corners were not found, the camera will continue to take pictures
						// self.loadUndistortedPicture();
					}
					self.waitingForRefresh(false)
				}
			}
		};

        self.startCornerCalibration = function () {
			self.analytics.send_fontend_event('corner_calibration_start', {});
			self.cornerCalibrationActive(true);
			self.picType("raw");
			// self.applySetting('lens_corrected')
			self._cornerCalImgUrl(self._getImgUrl('raw', true))
			self.markersFoundPositionCopy = self.markersFoundPosition()
			self.nextMarker();
		};

        // todo user lens calibration
        self.abortCornerCalibration = function () {
            // Please check: stopCornerCalibration wasn't here
            self.stopCornerCalibration();
            self.calibration.resetView();
        };

		self.stopCornerCalibration = function () {
			self.cornerCalibrationActive(false);
			self.cornerCalImgUrl() // trigger refresh
		}

        self.saveCornerCalibrationData = function () {
            let _corners = self.currentResults()
            let _k;
            for (_k of Object.keys(_corners)) {
                _corners[_k] = [_corners[_k].x, _corners[_k].y]
            }
            let data = {
                result: {
                    newMarkers: self.markersFoundPositionCopy,
                    newCorners: self.currentResults()
                }
            };
            console.log('Sending data:', data);
            self.simpleApiCommand("send_corner_calibration", data, self._saveMarkersSuccess, self._saveMarkersError, "POST");
        };

        self._saveMarkersError = function () {
            self.cornerCalibrationActive(false);
            new PNotify({
                title: gettext("Couldn't send calibration data."),
                text: gettext("Please check your connection to the device."),
                type: "warning",
                hide: true
            });

            self.calibration.resetView();
        };

        self._saveMarkersSuccess = function (response) {
            self.cornerCalibrationActive(false);
            self.analytics.send_fontend_event('corner_calibration_finish', {});
            new PNotify({
                title: gettext("Camera Calibrated."),
                text: gettext("Camera calibration was successful."),
                type: "success",
                hide: true
            });
            self.calibration.resetView();
        };


        self.engraveMarkers = function () {
		    let success_callback = function (data) {
				console.log("generated_markers_svg", data);
                let fileObj = {
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
			};
		    let error_callback = function (jqXHR, textStatus, errorThrown) {
				new PNotify({
                    title: gettext("Error"),
                    text: _.sprintf(gettext("Calibration failed.<br><br>Error:<br/>%(code)s %(status)s - %(errorThrown)s"), {code: jqXHR.status, status: textStatus, errorThrown: errorThrown}),
                    type: "error",
                    hide: false
                })
			};

		    self.simpleApiCommand(
		        "generate_calibration_markers_svg",
                {},
                success_callback,
                error_callback,
                "GET"
            )
		};

        self._getImgUrl = function(type, applyCrossVisibility) {
			if (type !== undefined) {
				self.applySetting(type, applyCrossVisibility)
				if (type == 'default')
					return self.staticURL
				else
					return self.availablePicUrl()[type]
			}
			for (let _t of ['cropped', 'lens_corrected', 'raw', 'default'])
				if (_t === 'default' || self.availablePic()[_t]){
					self.applySetting(_t, applyCrossVisibility)
					if (_t == 'default')
						return self.staticURL
					else
						return self.availablePicUrl()[_t]
				}
			self.applySetting('default')
			return self.staticURL // precaution
		};

        // MARKER NAVIGATION
        self.goToMarker = function(markerNum) {
		    self.currentMarker = markerNum;
		    self._highlightStep(self.calibrationMarkers[markerNum])
        }

        self.previousMarker = function(){
			let i = self.currentMarker - 1;
			if(!self.cornerCalibrationComplete() && i === 0) i = -1;
			if(i < 0) i = self.calibrationMarkers.length - 1;
			self.currentMarker = i;
			let nextStep = self.calibrationMarkers[self.currentMarker];
			self._highlightStep(nextStep);
		};

        self.nextMarker = function(){
			self.currentMarker = (self.currentMarker + 1) % self.calibrationMarkers.length;
			if(!self.cornerCalibrationComplete() && self.currentMarker === 0) self.currentMarker = 1;
			let nextStep = self.calibrationMarkers[self.currentMarker];
			self._highlightStep(nextStep);
		};

        self._highlightStep = function(step){
			$('.cal-row').removeClass('active');
			$('#'+step.name).addClass('active');
			self.focusX(step.focus[0]);
			self.focusY(step.focus[1]);
			self.calSvgScale(step.focus[2])
		}

		self._formatPoint = function(p){
			if(typeof p === 'undefined') return '?,?';
			else return p.x+','+p.y;
		};

		// USER CLICKS
		self.userClick = function (vm, ev) {
			// check if picture is loaded
			if(window.location.href.indexOf('localhost') === -1)
				if(self.cornerCalImgUrl() === STATIC_URL){
					console.log("Please wait until camera image is loaded...");
					return;
				}

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
				// self.nextMarker()
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

		self.applySetting = function(picType, applyCrossVisibility) {
			// TODO with a dictionary
			let settings = [['cropped', CROPPED_IMG_RES, 'hidden', 'visible'],
			                ['lens_corrected', DEFAULT_IMG_RES, 'hidden', 'hidden'],
			                ['raw', DEFAULT_IMG_RES, 'visible', 'hidden'],
			                ['default', LOADING_IMG_RES, 'hidden', 'hidden']]
			for (let _t of settings)
				if (_t[0] === picType) {
					self.calImgWidth(_t[1][0])
					self.calImgHeight(_t[1][1])
					if(applyCrossVisibility){
						self.correctedMarkersVisibility(_t[2])
						self.croppedMarkersVisibility(_t[3])
					}
					return
				}
			new PNotify({
				title: gettext("Error"),
				text: "Something went wrong (applySettings)",
				type: 'error',
				hide: true
			});
		};


		self.loadUndistortedPicture = function (callback) {
			let success_callback = function (data) {
				new PNotify({
					title: gettext("Picture requested"),
					text: data['msg'],
					type: 'info',
					hide: true
				});
				if (typeof callback === 'function')
					callback(data);
				else {
					self.waitingForRefresh(true)
					console.log("Calibration picture requested.");
				}
			};
			let error_callback = function (resp) {
				new PNotify({
					title: gettext("Something went wrong. It's not you, it's us."),
					text: resp.responseText,
					type: 'warning',
					hide: true
				});
				if (typeof callback === 'function')
					callback(resp);
			};
			self.simpleApiCommand(
				"take_undistorted_picture",
				{},
				success_callback,
				error_callback
			)
		};

    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        CornerCalibrationViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["calibrationViewModel", "workingAreaViewModel", "vectorConversionViewModel", "cameraViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#settings_plugin_mrbeam_camera"]
    ]);
});
