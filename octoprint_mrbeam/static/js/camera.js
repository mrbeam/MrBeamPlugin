MAX_OBJECT_HEIGHT = 38; // in mm
DEFAULT_MARGIN = MAX_OBJECT_HEIGHT / 582;


$(function(){

	function CameraViewModel(params) {
        var self = this;
        self.settings = params[0];
        self.cameraCalibration = params[1];

        self.TAB_NAME_WORKING_AREA = '#workingarea';
        self.FALLBACK_IMAGE_URL = '/plugin/mrbeam/static/img/beam-cam-static.jpg';

        self.needsCalibration = false;

        self.imageUrl = undefined;
        self.webCamImageElem = undefined;
        self.isCamCalibrated = false;
        self.firstImageLoaded = false;

        self.objectZ = ko.observable(0); // in mm
        self.cornerMargin = ko.observable(DEFAULT_MARGIN / 2);
        self.imgHeightScale = ko.computed(function () {
            return self.cornerMargin() * (1 - self.objectZ() / MAX_OBJECT_HEIGHT);
        });
        // event listener callbacks //

        self.onAllBound = function () {
            self.webCamImageElem = $("#beamcam_image_svg");
			self.cameraMarkerElem = $("#camera_markers");
            // self.webCamImageElem.removeAttr('onerror');
            self.imageUrl = self.settings.settings.plugins.mrbeam.cam.frontendUrl();

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
        self.imgResolutionColor = ko.computed(function () {
            if (self.imgResolution() === 'Low') {
                $("#imgQualityNotice").attr('style', "display: inherit");
                return 'orange';
            }
            else {
                $("#imgQualityNotice").attr('style', "display: none");
                return 'green';
            }
        });
        self.imgResolutionNoticeVisibility = ko.observable(true)


        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin !== "mrbeam" || !data) return;
            if ('beam_cam_new_image' in data) {
                const mf = data['beam_cam_new_image']['markers_found'];
                ['NW', 'NE', 'SE', 'SW'].forEach(function(m) {
                    if(mf.includes(m)) {
                        self.cameraMarkerElem.removeClass('marker' + m);
                    } else {
                        self.cameraMarkerElem.addClass('marker' + m);
                    }
                });

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
            var myImageUrl = self.getTimestampedImageUrl();
            var img = $('<img>');
            img.load(function () {
                self.webCamImageElem.attr('xlink:href', myImageUrl);
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
                    self.webCamImageElem.attr("xlink:href", self.FALLBACK_IMAGE_URL);
                });
            }
            img.attr({src: myImageUrl});
        };

        self.getTimestampedImageUrl = function () {
            var result = undefined;
            if (self.imageUrl) {
                result = self.imageUrl;
                result += (result.lastIndexOf("?") > -1) ? '&' : '?';
                result += new Date().getTime();
            }
            return result;
        };
    };



    // view model class, parameters for constructor, container to bind to
    ADDITIONAL_VIEWMODELS.push([CameraViewModel,
		["settingsViewModel"],
		[] // nothing to bind.
	]);

});
