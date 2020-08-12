const MARKERS = ['NW', 'NE', 'SE', 'SW'];


$(function(){

	function CameraViewModel(params) {
        var self = this;
        window.mrbeam.viewModels['cameraViewModel'] = self;

        self.settings = params[0];
        self.state = params[1];

        self.TAB_NAME_WORKING_AREA = '#workingarea';
        self.FALLBACK_IMAGE_URL = '/plugin/mrbeam/static/img/beam-cam-static.jpg';
        self.MARKER_DESCRIPTIONS = {
            'NW': gettext('Top left'),
            'SW': gettext('Bottom left'),
            'NE': gettext('Top right'),
            'SE': gettext('Bottom right')
        }

        self.needsCalibration = false;

        self.rawUrl = '/downloads/files/local/cam/debug/raw.jpg'; // TODO get from settings
        self.undistortedUrl = '/downloads/files/local/cam/debug/undistorted.jpg'; // TODO get from settings
        self.croppedUrl = '/downloads/files/local/cam/beam-cam.jpg';
        self.timestampedCroppedImgUrl = ko.observable("");
        self.webCamImageElem = undefined;
        self.isCamCalibrated = false;
        self.firstImageLoaded = false;
        self.countImagesLoaded = ko.observable(0);

        self.markersFound = ko.observable(new Map(MARKERS.map(elm => [elm, undefined])));

        self.maxObjectHeight = 38; // in mm
        self.defaultMargin = self.maxObjectHeight / 582;
        self.objectZ = ko.observable(0); // in mm
        self.cornerMargin = ko.observable(self.defaultMargin / 2);
        self.imgHeightScale = ko.computed(function () {
            return self.cornerMargin() * (1 - self.objectZ() / self.maxObjectHeight);
        });
        // event listener callbacks //

        self.onAllBound = function () {
            self.webCamImageElem = $("#beamcam_image_svg");
			self.cameraMarkerElem = $("#camera_markers");
            // self.webCamImageElem.removeAttr('onerror');
            self.croppedUrl = self.settings.settings.plugins.mrbeam.cam.frontendUrl();

            if (window.mrbeam.browser.is_safari) {
                // svg filters don't really work in safari: https://github.com/mrbeam/MrBeamPlugin/issues/586
                self.webCamImageElem.attr('filter', '');
            }

            // loading_overlay disappears only if this is set to true
            // not working in Safari
            self.webCamImageElem.load(function(){
                self.firstImageLoaded = true;
                self.countImagesLoaded(self.countImagesLoaded()+1);
            });

            // trigger initial loading of the image
            self.loadImage(self.croppedUrl);
        };

        // Image resolution notification //
        self.imgResolution = ko.observable('Low');
        self.imgResolutionNoticeDisplay = ko.computed(function () {
            if (self.imgResolution() === 'Low') return 'inherit';
            else return 'none';
        });

        self.markerState = ko.computed(function() {
            // Returns the number of markers found
            if (MARKERS.reduce((prev, key) => prev || self.markersFound()[key] === undefined, false))
                return undefined
            return MARKERS.reduce((prev_val, key) => prev_val + self.markersFound()[key], 0)
        })

        self.markerStateColor = ko.computed(function() {
            if (self.markerState() === undefined)
                return undefined
            else if (self.markerState() >= 4)
                return 'green'
            else if (2 <= self.markerState() < 4)
                return 'yellow'
            else if (self.markerState() < 2)
                return 'red'
            else
                return undefined
        })

        self.firstRealimageLoaded = ko.computed(function() {
            return self.countImagesLoaded() >= 2;
        })

        self.cameraActive = ko.computed(function() {
            return self.firstRealimageLoaded() && self.state.isOperational() && !self.state.isPrinting() && !self.state.isLocked();
        })

        self.markerMissedClass = ko.computed(function() {
            var ret = '';
            MARKERS.forEach(function(m){
                if ((self.markersFound()[m] !== undefined) && !self.markersFound()[m])
                    ret = ret + ' marker' + m;
            });
            return ret;
        })

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin !== "mrbeam" || !data) return;
            if ('beam_cam_new_image' in data) {
                const mf = data['beam_cam_new_image']['markers_found'];
                _markersFound = {};
                MARKERS.forEach(function(m) {
                    if(mf.includes(m)) {
                        _markersFound[m] = true;
                    } else {
                        _markersFound[m] = false;
                    }
                });
                self.markersFound(_markersFound);

                if (data['beam_cam_new_image']['error'] === undefined) {
                    self.needsCalibration = false;
                } else if (data['beam_cam_new_image']['error'] === "Camera_calibration_is_needed" && !self.needsCalibration) {
                    self.needsCalibration = true;
                    new PNotify({
                        title: gettext("Calibration needed"),
                        text: gettext("Please calibrate the camera under Settings -> Camera Calibration"),
                        type: "warning",
                        tag: "calibration_needed",
                        hide: false
                    });
                }
                if ('workspace_corner_ratio' in data['beam_cam_new_image']) {
                    // workspace_corner_ratio should be a float
                    // describing the fraction of the img where
                    // the z=0 view starts.
                    self.cornerMargin(data['beam_cam_new_image']['workspace_corner_ratio']);
                } else {
                    self.cornerMargin(0)
                }
                self.loadImage(self.croppedUrl);
            }

			// If camera is not active (lid closed), all marker(NW|NE|SW|SE) classes should be removed.
			if('interlocks_closed' in data && data.interlocks_closed === true){
				self.cameraMarkerElem.attr('class', '');
			}
        };

        self.loadImage = function (url) {
            var myImageUrl = self.getTimestampedImageUrl(url);
            var img = $('<img>');
            img.load(function () {
                self.timestampedCroppedImgUrl(myImageUrl);
                if (window.mrbeam.browser.is_safari) {
                    // load() event seems not to fire in Safari.
                    // So as a quick hack, let's set firstImageLoaded to true already here
                    self.firstImageLoaded = true;
                    self.countImagesLoaded(self.countImagesLoaded()+1);
                }
                if (this.width > 1500 && this.height > 1000) self.imgResolution('High');
                else self.imgResolution('Low');

                // respond to backend to tell we have loaded the picture
                if (INITIAL_CALIBRATION) {
                    $.ajax({type: "GET", url: '/plugin/mrbeam/on_camera_picture_transfer'});
                } else {
                    OctoPrint.simpleApiCommand("mrbeam", "on_camera_picture_transfer", {})
                }
            });
            if (!self.firstImageLoaded) {
                img.error(function () {
                    self.timestampedCroppedImgUrl(self.FALLBACK_IMAGE_URL);
                });
            }
            img.attr({src: myImageUrl});
        };

        self.getTimestampedImageUrl = function (url) {
            var result = undefined;
            if (url) {
                result = url;
            } else if (self.croppedUrl) {
                result = self.croppedUrl;
            }
            if (result) {
                if (result.match(/(\?|&)ts=/))
                    result = result.replace(/(\?|&)ts=[0-9]+/, "$1ts=" + new Date().getTime())
                else {
                    result += (result.lastIndexOf("?") > -1) ? '&ts=' : '?ts='
                    result += new Date().getTime();
                }
            }
            return result;
        };

        self.send_camera_image_to_analytics = function(){
            OctoPrint.simpleApiCommand("mrbeam", "send_camera_image_to_analytics", {})
        };
    }



    // view model class, parameters for constructor, container to bind to
    ADDITIONAL_VIEWMODELS.push([CameraViewModel,
		["settingsViewModel", "printerStateViewModel"],
		[] // nothing to bind.
	]);

});
