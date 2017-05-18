$(function(){

	function CameraViewModel(params) {
        var self = this;
        self.settings = params[0];
        self.workingArea = params[1];
        self.profile = params[2];

        self.interval_duration = 2000;

        self.myInterval = undefined;
        self.imageUrl = undefined;
        self.webCamImageElem = undefined;

        self.imageLoadingDuration = -1;

        self.camera_offset_x = ko.observable(0);
        self.camera_offset_y = ko.observable(0);
        self.camera_scale = ko.observable(1.0);
        self.camera_rotation = ko.observable(0.0);

        self.camTransform = ko.computed(function () {
            return "scale(" + self.camera_scale() + ") rotate(" + self.camera_rotation() + "deg) translate(" + self.camera_offset_x() + "px, " + self.camera_offset_y() + "px)"
        });

        self.onAllBound = function () {
            self.webCamImageElem = $("#webcam_image");
            self.imageUrl = self.settings.settings.plugins.mrbeam.cam.frontendUrl();

            self.initCameraCalibration();
            self.onTabChange('#workingarea', '#notab');
        };

        self.onBrowserTabVisibilityChange = function (state) {
            var currentTab = $('#mrbeam-main-tabs li.active a').attr('href');
            if (typeof currentTab !== undefined && currentTab === "#workingarea") {
                if (state === true) {
                    self.onTabChange('#workingarea', '#notab');
                }
                if (state === false) {
                    self.onTabChange('#notab', '#workingarea');
                }
            }
        };

        self.onTabChange = function (current, previous) {
            if (current === "#workingarea") {
                self.loadImage();
                self.startImageLoadingInterval();
            } else if (previous === "#workingarea") {
                self.stopImageLoadingInterval();
            }
        };

        self.initCameraCalibration = function () {
            var s = self.settings.settings.plugins.mrbeam;
            s.camera_offset_x.subscribe(function (newValue) {
                self.camera_offset_x(newValue);
            });
            s.camera_offset_y.subscribe(function (newValue) {
                self.camera_offset_y(newValue);
            });
            s.camera_scale.subscribe(function (newValue) {
                self.camera_scale(newValue);
            });
            s.camera_rotation.subscribe(function (newValue) {
                self.camera_rotation(newValue);
            });

            s.camera_offset_x.notifySubscribers(s.camera_offset_x());
            s.camera_offset_y.notifySubscribers(s.camera_offset_y());
            s.camera_scale.notifySubscribers(s.camera_scale());
            s.camera_rotation.notifySubscribers(s.camera_rotation());

        };

        self.startImageLoadingInterval = function () {
            var myIntervalDuration = Math.max(self.interval_duration, self.imageLoadingDuration);
            self.myInterval = setInterval(self.loadImage, myIntervalDuration);
            console.log("BeamCam updating, interval: " + Math.round(myIntervalDuration) + "ms");
        };

        self.stopImageLoadingInterval = function () {
            window.clearInterval(self.myInterval);
            self.myInterval = undefined;
            console.log("BeamCam update paused");
        };

        self.loadImage = function () {
            var myImageUrl = self.getTimestampedImageUrl();
            var myTime = new Date().getTime();
            $('<img>')
                .load(function () {
                    self.webCamImageElem.attr('src', myImageUrl);
                    var myDuration = new Date().getTime() - myTime;
                    self.addToImageLoadingDuration(myDuration);
                })
                .attr({src: myImageUrl});
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

        self.addToImageLoadingDuration = function(nuDuration) {
            if (nuDuration > 0) {
                if (self.imageLoadingDuration > 0) {
                    self.imageLoadingDuration = (self.imageLoadingDuration + nuDuration) / 2 ;
                } else {
                    self.imageLoadingDuration = nuDuration;
                }
            }
        };
    };



    // view model class, parameters for constructor, container to bind to
    ADDITIONAL_VIEWMODELS.push([CameraViewModel,
		["settingsViewModel", "workingAreaViewModel", "laserCutterProfilesViewModel"],
		[
			document.getElementById("webcam_wrapper"),
			document.getElementById("settings_camera_calibration")
		]
	]);

});
