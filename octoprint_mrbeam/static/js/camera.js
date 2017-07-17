$(function(){

	function CameraViewModel(params) {
        var self = this;
        self.settings = params[0];
        self.profile = params[2];

        self.INTERVAL_DURATION = 2000;
        self.TAB_NAME_WORKING_AREA = '#workingarea';

        self.camEnabled = undefined;
        self.doImageLoading = undefined;

        self.imageUrl = undefined;
        self.webCamImageElem = undefined;

        self.currentTab = '';
        self.lidClosed = undefined;

        // event listener callbacks //

        self.onAllBound = function () {
            self.webCamImageElem = $("#beamcam_image_svg");
            self.webCamImageElem.removeAttr('onerror');
            self.camEnabled = self.settings.settings.plugins.mrbeam.cam.enabled();
            self.imageUrl = self.settings.settings.plugins.mrbeam.cam.frontendUrl();

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
            if (plugin !== "mrbeam" || !data) return;
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
                    self.webCamImageElem.attr('xlink:href', myImageUrl);
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
            return currentTab === self.TAB_NAME_WORKING_AREA;
        };

        self.getCurrentTab = function(){
            return $('#mrbeam-main-tabs li.active a').attr('href');
        }
    };



    // view model class, parameters for constructor, container to bind to
    ADDITIONAL_VIEWMODELS.push([CameraViewModel,
		["settingsViewModel", "laserCutterProfilesViewModel"],
		[] // nothing to bind.
	]);

});
