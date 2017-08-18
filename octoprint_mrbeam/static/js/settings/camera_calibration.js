/*
 * View model for Mr Beam
 *
 * Author: Teja Philipp <teja@mr-beam.org>
 * License: AGPLv3
 */
/* global OctoPrint, OCTOPRINT_VIEWMODELS */

$(function() {
    function CameraCalibrationViewModel(parameters) {
        var self = this;
        self.scaleFactor = 8;
        // todo get ImgUrl from Backend/Have it hardcoded but right
		self.calImgUrl = ko.observable("/plugin/mrbeam/static/img/cam_calib_static.jpg");
		self.calImgWidth = ko.observable(1024);
		self.calImgHeight = ko.observable(768);
		self.calSvgOffX = ko.observable(0);
		self.calSvgOffY = ko.observable(0);
		self.calSvgScale = ko.observable(1);
		self.calSvgViewBox = ko.computed(function(){
			var w = self.calImgWidth() / self.calSvgScale();
			var h = self.calImgHeight() / self.calSvgScale();
			return [self.calSvgOffX(), self.calSvgOffY(), w, h].join(' ');
		});
		self.currentStep = 0;
        self.currentResults = {};

		self.calibrationSteps = [
			{name: 'start', desc: 'click to start', focus: [0,0,1]},
			{name: 'NW', desc: 'North West', focus: [0,0,self.scaleFactor]},
			{name: 'SW', desc: 'North East', focus: [0,self.calImgHeight(),self.scaleFactor]},
			{name: 'SE', desc: 'South East', focus: [self.calImgWidth(),self.calImgHeight(),self.scaleFactor]},
			{name: 'NE', desc: 'South West', focus: [self.calImgWidth(),0,self.scaleFactor]}
		];

		self.userClick = function(vm, ev){
			var cPos = self._getClickPos(ev);
			console.log("got calibration: ", cPos);

			// save current stepResult
			var step = self.calibrationSteps[self.currentStep];
			if(self.currentStep > 0){
			    self.currentResults[step.name] = {'x':cPos.xImg,'y':cPos.yImg};
            }

			//check if finished and send result if true
            self.currentStep = (self.currentStep + 1) % self.calibrationSteps.length;
            if(self.currentStep === 0){
                self._sendData({result:self.currentResults});
                self.currentResults = {}
            }

			// update for next step
			var nextStep = self.calibrationSteps[self.currentStep];
			self.zoomTo(nextStep.focus[0], nextStep.focus[1], nextStep.focus[2]);
			console.log("now click for " + nextStep.desc);
		};

		self._getClickPos = function(ev){

			var bbox = ev.target.parentElement.getBoundingClientRect();
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

		self.zoomTo = function(x,y, scale){
			self.calSvgScale(scale);
			var w = self.calImgWidth() / scale;
			var h = self.calImgHeight() / scale;
			var offX = Math.min(Math.max(x - w/scale, 0), self.calImgWidth() - w);
			var offY = Math.min(Math.max(y - h/scale, 0), self.calImgHeight() - h);
			self.calSvgOffX(offX);
			self.calSvgOffY(offY);
		};

        self.onStartup = function(){
            console.log("CameraCalibrationViewModel.onStartup()");

        };

        self.loadUndistortedPicture = function () {
          console.log("NEW PICTURE REQUESTED...");
          OctoPrint.simpleApiCommand("mrbeam", "take_undistorted_picture")
                .done(function(response) {
                    console.log(response);
                    new PNotify({
                        title: gettext("Success"),
                        text: gettext("New Picture is loaded"),
                        type: "success",
                        hide: true
                    });
                })
                .fail(function(){
                    new PNotify({
                        title: gettext("Error"),
                        text: gettext("could not take picture"),
                        type: "warning",
                        hide: true
                    });
                });
        };




        self._sendData = function(data) {
            OctoPrint.simpleApiCommand("mrbeam", "camera_calibration_markers", data)
                .done(function(response) {
                    new PNotify({
                        title: gettext("BAM! markers are sent."),
                        text: gettext("Cool, eh?"),
                        type: "success",
                        hide: true
                    });
                })
                .fail(function(){
                    new PNotify({
                        title: gettext("Couldn't send image markers."),
                        text: gettext("...and I have no clue why."),
                        type: "warning",
                        hide: true
                    });
                });
        };
    };

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        CameraCalibrationViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["settingsViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        [ "#settings_plugin_mrbeam_camera" ]
    ]);
});
