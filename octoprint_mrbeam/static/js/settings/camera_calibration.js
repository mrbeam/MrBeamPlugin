/*
 * View model for Mr Beam
 *
 * Author: Teja Philipp <teja@mr-beam.org>
 * License: AGPLv3
 */
/* global OctoPrint, OCTOPRINT_VIEWMODELS, INITIAL_CALIBRATION */

MARKERS = ['NW', 'NE', 'SE', 'SW'];
MIN_BOARDS_FOR_CALIBRATION = 9;
MAX_BOARD_SCORE = 5;
DEFAULT_IMG_RES = [2048, 1536]
CROPPED_IMG_RES = [500,390]

$(function () {
	function CameraCalibrationViewModel(parameters) {
		var self = this;
		window.mrbeam.viewModels['cameraCalibrationViewModel'] = self;
		self.settings = parameters[0];
		self.workingArea = parameters[1];
		self.conversion = parameters[2];
		self.analytics = parameters[3];
		self.loginState = parameters[4];
		self.camera = self.workingArea.camera;

		self.all_bound = ko.observable(false);
		self.calibrationScreenShown = ko.observable(false);
		self.waitingForRefresh = ko.observable(true)

		self.staticURL = "/plugin/mrbeam/static/img/cam_calibration/calpic_wait.svg";

		self.dbNWImgUrl = ko.observable("");
		self.dbNEImgUrl = ko.observable("");
		self.dbSWImgUrl = ko.observable("");
		self.dbSEImgUrl = ko.observable("");
		self.interlocks_closed = ko.observable(false);
		self.lid_fully_open = ko.observable(false);

		self.focusX = ko.observable(0);
		self.focusY = ko.observable(0);
		self.qa_pic_raw = ko.computed(function(){
			return self.camera.getTimestampedImageUrl(self.camera.rawUrl);
		});
		self.qa_pic_undistorted = ko.computed(function(){
			return self.camera.getTimestampedImageUrl(self.camera.undistortedUrl);
		});
		self.qa_pic_cropped = ko.computed(function(){
			return self.camera.getTimestampedImageUrl(self.camera.croppedUrl);
		});
		self.picType = ko.observable(""); // raw, lens_corrected, cropped
		self.correctedMarkersVisibility = ko.observable('hidden')
		self.croppedMarkersVisibility = ko.observable('hidden');
		self.calImgWidth = ko.observable(DEFAULT_IMG_RES[0]);
		self.calImgHeight = ko.observable(DEFAULT_IMG_RES[1]);
		self.availablePic = ko.observable({'raw': false, 'lens_corrected': false, 'cropped': false, })
		self._availablePicUrl = ko.observable({'default': self.staticURL, 'raw': null, 'lens_corrected': null, 'cropped': null, })
		self.availablePicUrl = ko.computed(function() {
			var ret = self._availablePicUrl();
			var before = _.clone(ret); // shallow copy
			for (let _t of [['cropped', self.camera.croppedUrl],
							['lens_corrected', self.camera.undistortedUrl],
							['raw', self.camera.rawUrl]]) {
				if (self.availablePic()[_t[0]])
					ret[_t[0]] = self.camera.getTimestampedImageUrl(_t[1]);
			}
			self._availablePicUrl(ret)
			var selectedTab = $('#camera-calibration-tabs .active a').attr('id')
			if (selectedTab === 'lenscal_tab_btn')
				return before
			else
				return ret
		})

		self.calSvgOffX = ko.observable(0);
		self.calSvgOffY = ko.observable(0);
		self.calSvgDx = ko.observable(0);
		self.calSvgDy = ko.observable(0);
		self.calSvgScale = ko.observable(1);
		self.cornerCalibrationActive = ko.observable(false);
		self.lensCalibrationActive = ko.observable(false);
		self.currentResults = ko.observable({});

		self.calImgUrl = ko.computed(function() {
			var settings = [['cropped', CROPPED_IMG_RES, 'hidden', 'visible'],
			                ['lens_corrected', DEFAULT_IMG_RES, 'visible', 'hidden'],
				            ['raw', DEFAULT_IMG_RES, 'hidden', 'hidden']]
			var applySetting = function(setting) {
				_t = setting
				self.calImgWidth(_t[1][0])
				self.calImgHeight(_t[1][1])
				self.correctedMarkersVisibility(_t[2])
				self.croppedMarkersVisibility(_t[3])
				return self.availablePicUrl()[_t[0]]
			}
			if (self.cornerCalibrationActive() && self.availablePic()['lens_corrected'])
				return applySetting(settings[1])

			for (let _t of settings) {
				if (self.availablePic()[_t[0]])
					return applySetting(_t)
			}
			self.calImgWidth(512);
			self.calImgHeight(384);
			self.correctedMarkersVisibility('hidden')
			self.croppedMarkersVisibility('hidden');
			return self.staticURL

		});
		self.cornerCalibrationComplete = ko.computed(function(){
			if (Object.keys(self.currentResults()).length !== 4) return false;
			return Object.values(self.currentResults()).reduce((x,y) => x && y);
		});
		self.cal_img_ready = ko.computed(function () {
			if (Object.keys(self.camera.markersFound()).length !== 4) return false;
			return Object.values(self.camera.markersFound()).reduce((x,y) => x && y);
		});

		self.rawPicSelection = ko.observableArray([])
		// calibrationState is constantly refreshed by the backend
		// as an immutable array that contains the whole state of the calibration
		self.calibrationState = ko.observable({})

		self.lensCalibrationNpzFileTs = ko.observable(null);
		self.lensCalibrationNpzFileVerboseDate = ko.computed(function(){
			const ts = self.lensCalibrationNpzFileTs();
			if(ts !== null){
				const d = new Date(ts);
				const verbose = d.toLocaleString('de-DE', { timeZone: 'Europe/Berlin' })
				return `Using .npz created at ${verbose}`;
			} else {
				return 'No .npz file available';
			}
		});
        self.lensCalibrationRunning = ko.observable(false);
		self.lensCalibrationComplete = ko.computed(function(){
			return ('lensCalibration' in self.calibrationState()) ? self.calibrationState().lensCalibration === "success" : false;
		});
		self.boardsFound = ko.computed(function() {
			return self.rawPicSelection().filter(elm => elm.state === "success").length
		})

		self.hasMinBoardsFound = ko.computed(function() {
			return self.boardsFound() >= MIN_BOARDS_FOR_CALIBRATION
		})
		
		self.boardsFoundString = ko.computed(function(){
			return `${self.boardsFound()}/${MIN_BOARDS_FOR_CALIBRATION}`;
		});
	
		self.lensCalibrationCoverageQuality = ko.observable(0);
		self.lensCalibrationCoverageQualityStr = ko.computed(function(){
			const totalScore = self.lensCalibrationCoverageQuality();
			const maxScore = Math.max(MIN_BOARDS_FOR_CALIBRATION, self.boardsFound()) * MAX_BOARD_SCORE;
			const percent = (totalScore / maxScore * 100);
			const text = `Quality: ${percent.toFixed(0)}% (min 90%)`;
			
			// data-bind is complicated with inline svg -> direct manipulation.
			document.getElementById('lensCalibrationCoverageText').innerHTML = text;
			return text;
		});
		self.markersFoundPosition = ko.observable({});
		self.markersFoundPositionCopy = null;

		self.onAllBound = function(){
			self.all_bound(true);
		};

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
			{name: 'SW', desc: 'North East', focus: [0, DEFAULT_IMG_RES[1], 4]},
			{name: 'SE', desc: 'South East', focus: [DEFAULT_IMG_RES[0], DEFAULT_IMG_RES[1], 4]},
			{name: 'NE', desc: 'South West', focus: [DEFAULT_IMG_RES[0], 0, 4]}
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
			self.markersFoundPositionCopy = self.markersFoundPosition()
			self.nextMarker();
		};

		self.stopCornerCalibration = function () {
			self.cornerCalibrationActive(false);
		}

		self.startLensCalibration = function () {
			self.analytics.send_fontend_event('lens_calibration_start', {});
			// self.picType("raw");
			self.simpleApiCommand("calibration_lens_start",
								  {},
								  self.refreshPics,
								  self.getRawPicError,
								  "GET");
			self.lensCalibrationActive(true);
		};
		
		self.lensCalibrationToggleQA = function (){
			$('#lensCalibrationPhases').toggleClass('qa_active');
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
				self.nextMarker()
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
					self.waitingForRefresh(true)
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
				var selectedTab = $('#camera-calibration-tabs .active a').attr('id')
				var _d = data['beam_cam_new_image'];
				if (_d['undistorted_saved'] && !self.cornerCalibrationActive()) {
					if (_d['available']) {
						self.availablePic(_d['available'])
					}

					if (self.isInitialCalibration() && (selectedTab === "cornercal_tab_btn" || self.waitingForRefresh())) {
						self.dbNWImgUrl('/downloads/files/local/cam/debug/NW.jpg' + '?ts=' + new Date().getTime());
						self.dbNEImgUrl('/downloads/files/local/cam/debug/NE.jpg' + '?ts=' + new Date().getTime());
						self.dbSWImgUrl('/downloads/files/local/cam/debug/SW.jpg' + '?ts=' + new Date().getTime());
						self.dbSEImgUrl('/downloads/files/local/cam/debug/SE.jpg' + '?ts=' + new Date().getTime());
					}

					// check if all markers are found and image is good for calibration
					if (self.cal_img_ready() && !self.cornerCalibrationActive()) {
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

			if ('chessboardCalibrationState' in data) {
				var _d = data['chessboardCalibrationState']
								
				self.calibrationState(_d);
				var arr = []
				// { '/home/pi/.octoprint/uploads/cam/debug/tmp_raw_img_4.jpg': {
				//      state: "processing", 
				//      tm_proc: 1590151819.735044, 
				//      tm_added: 1590151819.674166, 
				//      board_bbox: [[767.5795288085938, 128.93748474121094],
				//                   [1302.0089111328125, 578.4738159179688]], // [xmin, ymin], [xmax, ymax]
				//      board_center: [1039.291259765625, 355.92547607421875], // cx, cy
				//      found_pattern: null,
				//      index: 2,
				//      board_size: [5, 6]
				//    }, ...
				// }

                if ('lensCalibrationNpzFileTs' in _d) {
                    self.lensCalibrationNpzFileTs(_d.lensCalibrationNpzFileTs > 0 ? _d.lensCalibrationNpzFileTs*1000 : null)
                }

				let found_bboxes = [];
				let total_score = 0;
				for (const [path, value] of Object.entries(_d.pictures)) {
					value.path = path;
					value.url = path.replace("home/pi/.octoprint/uploads", "downloads/files/local");
					value.processing_duration = value.tm_end !== null ? (value.tm_end - value.tm_proc).toFixed(1) + ' sec' : '?';
					arr.push(value);
					if(value.board_bbox){
						// TODO individual score should be attributed when all boxes are in the list
						value.score = self._calc_pic_score(value.board_bbox, found_bboxes);
						total_score += value.score;
						found_bboxes.push(value.board_bbox);
					}
				}
				self.updateHeatmap(_d.pictures);
				self.lensCalibrationCoverageQuality(total_score);
			
				for (var i = arr.length; i < 9; i++) {
					arr.push({
						index: i,
						path: null, 
						url: '',
						state: 'missing'
					});
				}
				
				// required to refresh the heatmap
				$('#heatmap_container').html($('#heatmap_container').html());

				arr.sort(function(l,r){
				    return l.index < r.index ? -1 : 1;
                });

//				console.log(arr);
				self.rawPicSelection(arr);
				self.lensCalibrationRunning(_d.lensCalibration === "processing");
			}
		};
		
		self._calc_pic_score = function(bbox, found_bboxes){
			if(!bbox) return 0;
			const [x1, y1] = bbox[0];
			const [x2, y2] = bbox[1];
			let max_overlap = 0;
			const area = (x2-x1) * (y2-y1);
			for (var i = 0; i < found_bboxes.length; i++) {
				var existing_bbox = found_bboxes[i];
				max_overlap = Math.max(max_overlap, self._get_bbox_intersecting_area(bbox, existing_bbox));
			}
			const score = ((1 - (max_overlap / area)) * MAX_BOARD_SCORE);
			return score;
		};
		
		self._get_bbox_intersecting_area = function(bb1, bb2){
			// precondition: bb = [[xmin, ymin], [xmax, ymax]] with always _min < _max
			const [x11, y11] = bb1[0];
			const [x21, y21] = bb1[1];
			const [x12, y12] = bb2[0];
			const [x22, y22] = bb2[1];
			if(x21 < x12 || x11 > x22 ) return 0; // bboxes don't overlap on the x axis
			if(y21 < y12 || y11 > y22 ) return 0; // bboxes don't overlap on the y axis
			const dx =  Math.min(x21, x22) - Math.max(x11, x12);
			const dy =  Math.min(y21, y22) - Math.max(y11, y12);
			return dx*dy;
		}
	
		self.updateHeatmap = function(picturesState){
			let boxes = []
			for (const [path, value] of Object.entries(picturesState)) {
				if (value.board_bbox) {
					let fileName = path.split('/').reverse()[0]
					const [x1, y1] = value.board_bbox[0];
					const [x2, y2] = value.board_bbox[1];
					boxes.push(`<rect id="heatmap_board${fileName}" x="${x1}" y="${y1}" width="${(x2-x1)}" height="${(y2-y1)}" />`);
				}
			}
			let heatmapGroup = $('#segment_group');
			heatmapGroup.empty()
			heatmapGroup.append(boxes)
		}
		
		self.reset_heatmap = function(){
			$('#segment_group rect').remove();
		}
		
		self.heatmap_highlight = function(data){
			let fileName = data.path.split('/').reverse()[0];
			let id = 'heatmap_board'+fileName;
			// $("#"+id).addClass('highlight'); // no idea why this doesn't work anymore
			document.getElementById(id).classList.add('highlight')
		}
		
		self.heatmap_dehighlight = function(data){
			$('#segment_group rect').removeClass('highlight');
		}

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


		self.delRawPic = function() {
			$('#heatmap_board'+this.index).remove(); // remove heatmap
			self.simpleApiCommand("calibration_del_pic",
								  {name: this['path']},
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

		self.rawPicSuccess = function(response) {}
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

		self.cameraBusy = ko.computed(function() {
			return self.rawPicSelection().some(elm => elm.state === "camera_processing")
		});

		self.resetLensCalibration = function() {
			self.lensCalibrationActive(false);
			self.lensCalibrationRunning(false);
			self.reset_heatmap();
		};

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

		self.stopLensCalibration = function() {
			self.simpleApiCommand(
				"camera_stop_lens_calibration",
				{},
				function(){
					new PNotify({
						title: gettext("Lens Calibration stopped"),
						// text: "",
						type: "info",
						hide: true});
					self.resetLensCalibration();
				},
				function(){
					new PNotify({
						title: gettext("Couldn't stop the lens calibration."),
						text: gettext("...and I have no clue why. Sorry."),
						type: "warning",
						hide: true})},
				"POST");

		}

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
					newMarkers: self.markersFoundPositionCopy,
					newCorners: self.currentResults()
				}
			};
			console.log('Sending data:', data);
			self.simpleApiCommand("send_corner_calibration", data, self.saveMarkersSuccess, self.saveMarkersError, "POST");
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
			}
			self.resetView();
		};

		self.resetView = function () {
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
		["settingsViewModel", "workingAreaViewModel", "vectorConversionViewModel", "analyticsViewModel", "loginStateViewModel"],

		// e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
		["#settings_plugin_mrbeam_camera"]
	]);
});
