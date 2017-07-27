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

		self.calImgUrl = ko.observable("/plugin/mrbeam/static/img/beam-cam-static.jpg");
		self.calImgWidth = ko.observable(500);
		self.calImgHeight = ko.observable(400);
		self.calSvgOffX = ko.observable(0);
		self.calSvgOffY = ko.observable(0);
		self.calSvgScale = ko.observable(1);
		self.calSvgViewBox = ko.computed(function(){
			var w = self.calImgWidth() / self.calSvgScale();
			var h = self.calImgHeight() / self.calSvgScale();
			return [self.calSvgOffX(), self.calSvgOffY(), w, h].join(' ');
		});
		self.currentStep = 0;

		self.calibrationSteps = [
			{name: 'start', desc: 'click to start', focus: [0,0,1]},
			{name: 'NW', desc: 'North West', focus: [0,0,5]},
			{name: 'NE', desc: 'North East', focus: [0,self.calImgWidth(),5]},
			{name: 'SE', desc: 'South East', focus: [self.calImgHeight(),self.calImgWidth(),5]},
			{name: 'SW', desc: 'South West', focus: [self.calImgHeight(),0,5]}
		];

		self.userClick = function(vm, ev){
			var cPos = self._getClickPos(ev);
			console.log("got calibration: ", cPos);
			self.currentStep = (self.currentStep + 1) % self.calibrationSteps.length;
			var n = self.calibrationSteps[self.currentStep];
			self.zoomTo(n.focus[0], n.focus[1], n.focus[2]);
			console.log("now click for " + n.desc);
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
			var offX = Math.min(Math.max(x - w/2, 0), self.calImgWidth() - w);
			var offY = Math.min(Math.max(y - h/2, 0), self.calImgHeight() - h);
			self.calSvgOffX(offX);
			self.calSvgOffY(offY);
		};
		
        self.onStartup = function(){
            console.log("TEJAMARKERS CameraCalibrationViewModel.onStartup()");
            // ok, maybe don't sent this onStartup()
            self._sendData({some:"data", goes:"here"});
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
