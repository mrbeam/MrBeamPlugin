/*
 * View model for Mr_Beam
 *
 * Author: Teja
 * License: AGPLv3
 */
$(function() {
    function LaserJobDoneViewmodel(parameters) {
        var self = this;
        window.mrbeam.viewModels['laserJobDoneViewmodel'] = self;
        self.readyToLaser = parameters[0];
        self.analytics = parameters[1];

        self._switchDuration = 3000;

        self.jobDoneDialog = {
            shown: null,
            closed: null,
            dur: null
        };

        self.is_job_done = ko.observable(false);
        self.is_dust_mode = ko.observable(false);
        self.job_duration = ko.observable(0);
        self.job_duration_formatted = ko.computed(function(){
            if (self.job_duration() < 0) {
                return '--:--:--'
            }
            var sec_num = parseInt(self.job_duration(), 10); // don't forget the second param
            var hours   = Math.floor(sec_num / 3600);
            var minutes = Math.floor((sec_num - (hours * 3600)) / 60);
            var seconds = sec_num - (hours * 3600) - (minutes * 60);

            if (hours   < 10) {hours   = "0"+hours;}
            if (minutes < 10) {minutes = "0"+minutes;}
            if (seconds < 10) {seconds = "0"+seconds;}
            return hours+':'+minutes+':'+seconds;
		});

        self.onStartupComplete = function(){
            self.dialogElement = $('#laser_job_done_dialog');
            self.dialogElement.on('hidden', function (e) {
                self.is_job_done(false);
            });
        };

        self.onEventPrintStarted = function(payload) {
            self.is_job_done(false);
            self.job_duration(0);
            self._fromData(payload);
        };

        self.onEventPrintDone = function (payload) {
            self.is_job_done(true);
            if (payload && 'time' in payload && $.isNumeric(payload['time'])) {
                self.job_duration(payload['time']);
            }
            self._fromData(payload);
            self.dialogElement.modal("show");
            self.jobDoneDialog.shown = payload['ts'] || new Date().getTime();
        };

        self.onEventDustingModeStart = function(payload) {
            self._fromData(payload);
        };

        self.onEventLaserJobDone = function(payload) {
            self._fromData(payload);
            self.dialogElement.modal("show");
            self.switchTimer();
        };

        self.fromCurrentData = function(payload) {
            self._fromData(payload);
        };

        self._fromData = function(payload, event) {
        if (!payload || !'mrb_state' in payload || !payload['mrb_state']) {
                return;
            }
            var mrb_state = payload['mrb_state'];
            if (mrb_state) {
                self.is_dust_mode(mrb_state['dusting_mode']);
            }
        };

        self.switchTimer = function(duration){
            setTimeout(self._switchNow, duration || self._switchDuration);
        };

        self._switchNow = function(){
            $('#laser_job_done_image_check').removeClass('show');
            $('#laser_job_done_image_text').addClass('show');
        };

        self._switchBack = function(){
            $('#laser_job_done_image_check').addClass('show');
            $('#laser_job_done_image_text').removeClass('show');
        };

        self.cancel_btn = function(){
            self.is_job_done(false);
            self.dialogElement.modal("hide");
            self._switchBack();
            self.jobDoneDialog.closed = new Date().getTime();
            self.jobDoneDialog.dur = Math.floor(self.jobDoneDialog.closed/1000 - self.jobDoneDialog.shown/1000);
            self.analytics.send_fontend_event('job_done_dialog', self.jobDoneDialog)
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        LaserJobDoneViewmodel,
        // e.g. loginStateViewModel, settingsViewModel, ...
        [ "readyToLaserViewModel", "analyticsViewModel"],
        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        [ '#laser_job_done_dialog']
    ]);
});
