$(function(){

	function CameraViewModel(params) {
        var self = this;
        self.settings = params[0];
        self.cameraCalibration = params[1];

        self.TAB_NAME_WORKING_AREA = '#workingarea';
        self.FALLBACK_IMAGE_URL = '/plugin/mrbeam/static/img/beam-cam-static.jpg';

        self.camEnabled = undefined;
        self.needsCalibration = false;

        self.imageUrl = undefined;
        self.webCamImageElem = undefined;
        self.isCamCalibrated = false;
        self.firstImageLoaded = false;

        // event listener callbacks //

        self.onAllBound = function () {
            self.webCamImageElem = $("#beamcam_image_svg");
			self.cameraMarkerElem = $("#camera_markers");
//			if(snap){
			self.previewImageFilter = $('#preview_precision feGaussianBlur');
//			}
            // self.webCamImageElem.removeAttr('onerror');
            self.camEnabled = self.settings.settings.plugins.mrbeam.cam.enabled();
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


        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin !== "mrbeam" || !data) return;
            if ('beam_cam_new_image' in data) {
                const mf = data['beam_cam_new_image']['markers_found'];
                if(mf['NW'] !== undefined){
                    const pixels = '['+mf['NW']['pixels']+','+mf['NE']['pixels']+','+mf['SW']['pixels']+','+mf['SE']['pixels']+']';
                    const circles = '['+mf['NW']['r']+','+mf['NE']['r']+','+mf['SW']['r']+','+mf['SE']['r']+']';
                    // console.log('New Image [NW,NE,SW,SE]: Pix '+pixels+' Rad '+circles,data['beam_cam_new_image']);
                }
				if(!data['beam_cam_new_image']['successful_correction']){
					['NW', 'NE', 'SE', 'SW'].forEach(function(m) {
						if(mf[m] !== undefined){ 
							if(mf[m].recognized === true){ self.cameraMarkerElem.removeClass('marker'+m); }
							else { self.cameraMarkerElem.addClass('marker'+m);}
						}
					});
					self.previewImageFilter.attr({'stdDeviation': 2});
				} else {
					self.previewImageFilter.attr({'stdDeviation':0});
				}
				
								
                if(data['beam_cam_new_image']['error'] === undefined){
                    self.needsCalibration = false;
                }else if(data['beam_cam_new_image']['error'] === "NO_CALIBRATION: Marker Calibration Needed" && !self.needsCalibration){
                    self.needsCalibration = true;
                    new PNotify({
                        title: gettext("Calibration needed"),
                        text: gettext("Please calibrate the camera under Settings -> Camera Calibration"),
                        type: "warning",
                        tag: "calibration_needed",
                        hide: false
                    });
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
