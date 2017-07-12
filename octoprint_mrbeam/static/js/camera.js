$(function(){

	function CameraViewModel(params) {
        var self = this;
        self.settings = params[0];
        self.workingArea = params[1];
        self.profile = params[2];

        self.INTERVAL_DURATION = 2000;
        self.TAB_NAME_WORKING_AREA = '#workingarea';

        self.camEnabled = undefined;
        self.doImageLoading = undefined;

        self.imageUrl = undefined;
        self.webCamImageElem = undefined;

        self.currentTab = '';
        self.lidClosed = undefined;

        self.camera_offset_x = ko.observable(0);
        self.camera_offset_y = ko.observable(0);
        self.camera_scale = ko.observable(1.0);
        self.camera_rotation = ko.observable(0.0);

        self.camTransform = ko.computed(function () {
            return "scale(" + self.camera_scale() + ") rotate(" + self.camera_rotation() + "deg) translate(" + self.camera_offset_x() + "px, " + self.camera_offset_y() + "px)"
        });

        // event listener callbacks //

        self.onAllBound = function () {
            self.webCamImageElem = $("#beamcam_image");
            self.webCamSettingsImageElem = $("#webcam_image_settings"); // dev settings module
            self.webCamSettingsImageElem.attr('src', self.webCamImageElem.attr('src'));
            self.webCamImageElem.removeAttr('onerror');
            self.camEnabled = self.settings.settings.plugins.mrbeam.cam.enabled();
            self.imageUrl = self.settings.settings.plugins.mrbeam.cam.frontendUrl();
            self.initCameraCalibration();

            // At this point we already got a lid_state through the socket connection.
            // But back then this viewmodel wasn't bound so that doCamState (or more precisely self.workingAreaIsCurrentTab) failed.
            // another doCamState() here solves this problem.
            self.doCamState(undefined, 'onAllBound');
        };

        self.onBrowserTabVisibilityChange = function (state) {
            var fakeTab = state ? self.TAB_NAME_WORKING_AREA : '#notab';
            self.doCamState(fakeTab, 'onBrowserTabVisibilityChange');
        };

        self.onTabChange = function (current, previous) {
            self.doCamState(current, 'onTabChange');
        };

         // this is listening for data coming through the socket connection
        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin != "mrbeam" || !data) return;
            if ('lid_closed' in data) {
                self.lidClosed = data.lid_closed;
                self.doCamState(undefined, 'onDataUpdaterPluginMessage');
            }
            if ('beam_cam_new_image' in data) {
                if (self.doImageLoading) {
                    console.log('Beam Cam: new image. LOADING ', data['beam_cam_new_image']);
                    self.loadImage();
                } else {
                    console.log('Beam Cam: new image. IGNORING ', data['beam_cam_new_image']);
                }
            }
        };


        // action methods //

        self.doCamState = function(currentTab, trigger){
            // console.log("doCamState() trigger:"+trigger+
            //     ", self.camEnabled:"+self.camEnabled+
            //     ", self.lidClosed:"+self.lidClosed+
            //     ", self.workingAreaIsCurrentTab("+currentTab+"):"+self.workingAreaIsCurrentTab(currentTab) +
            //     ", self.intervalId:" + self.intervalId);

            if (self.camEnabled && !self.lidClosed && self.workingAreaIsCurrentTab(currentTab)) {
                self.loadImage();
                self.startImageLoadingInterval();
            } else {
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
            self.doImageLoading = true;
            console.log("BeamCam updating");
        };

        self.stopImageLoadingInterval = function () {
            self.doImageLoading = false;
            console.log("BeamCam paused");
        };

        self.loadImage = function () {
            var myImageUrl = self.getTimestampedImageUrl();
            $('<img>')
                .load(function () {
                    self.webCamImageElem.attr('src', myImageUrl);
                    self.webCamSettingsImageElem.attr('src', myImageUrl);
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

        self.workingAreaIsCurrentTab = function(currentTab){
            currentTab = (currentTab) ? currentTab : self.getCurrentTab();
            return currentTab == self.TAB_NAME_WORKING_AREA;
        }

        self.getCurrentTab = function(){
            return $('#mrbeam-main-tabs li.active a').attr('href');
        }
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
