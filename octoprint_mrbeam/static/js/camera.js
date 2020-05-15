MARKERS = ['NW', 'NE', 'SE', 'SW'];


$(function(){

	function CameraViewModel(params) {
        var self = this;
        self.settings = params[0];
        self.cameraCalibration = params[1];

        self.TAB_NAME_WORKING_AREA = '#workingarea';
        self.FALLBACK_IMAGE_URL = '/plugin/mrbeam/static/img/beam-cam-static.jpg';

        self.needsCalibration = false;

        self.rawUrl = '/downloads/files/local/cam/debug/raw.jpg'; // TODO get from settings
        self.undistortedUrl = '/downloads/files/local/cam/debug/undistorted.jpg'; // TODO get from settings
        self.croppedUrl = '/downloads/files/local/cam/beam-cam.jpg';
        self.timestampedImgUrl = ko.observable("");
        self.webCamImageElem = undefined;
        self.isCamCalibrated = false;
        self.firstImageLoaded = false;

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
            });

            // trigger initial loading of the image
            self.loadImage();
        };

        // Image resolution notification //
        self.imgResolution = ko.observable('Low');
        self.imgResolutionNoticeDisplay = ko.computed(function () {
            if (self.imgResolution() === 'Low') return 'inherit';
            else return 'none';
        });

        self.markerMissedClass = ko.computed(function() {
            var ret = '';
            MARKERS.forEach(function(m){
                if (!(self.markersFound()[m] === undefined) && !self.markersFound()[m])
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
                } else if (data['beam_cam_new_image']['error'] === "NO_CALIBRATION: Marker Calibration Needed" && !self.needsCalibration) {
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
                self.loadImage();
            }

			// If camera is not active (lid closed), all marker(NW|NE|SW|SE) classes should be removed.
			if('interlocks_closed' in data && data.interlocks_closed === true){
				self.cameraMarkerElem.attr('class', '');
			}
        };

        self.loadImage = function () {
            var myImageUrl = self.getTimestampedImageUrl(self.croppedUrl);
            var img = $('<img>');
            img.load(function () {
                self.timestampedImgUrl(myImageUrl);
                if (window.mrbeam.browser.is_safari) {
                    // load() event seems not to fire in Safari.
                    // So as a quick hack, let's set firstImageLoaded to true already here
                    self.firstImageLoaded = true;
                }
                if (this.width > 1500 && this.height > 1000) self.imgResolution('High');
                else self.imgResolution('Low');
                // TODO respond to backend to tell we have loaded the picture
                OctoPrint.simpleApiCommand("mrbeam", "on_camera_picture_transfer", {})
            });
            if (!self.firstImageLoaded) {
                img.error(function () {
                    self.timestampedImgUrl(self.FALLBACK_IMAGE_URL);
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
    }



    // view model class, parameters for constructor, container to bind to
    ADDITIONAL_VIEWMODELS.push([CameraViewModel,
		["settingsViewModel"],
		[] // nothing to bind.
	]);

});
