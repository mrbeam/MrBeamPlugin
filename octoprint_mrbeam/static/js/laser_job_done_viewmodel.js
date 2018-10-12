/*
 * View model for Mr_Beam
 *
 * Author: Teja
 * License: AGPLv3
 */
$(function() {
    function LaserJobDoneViewmodel(parameters) {
        var self = this;
        self.is_job_done = ko.observable(false);
        self.is_dust_mode = ko.observable(false);
        self.job_duration = ko.observable(0);
        self.job_duration_formatted = ko.computed(function(){
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
        }

        self.onEventPrintDone = function (payload) {
            self.is_job_done(true);
            if (payload && 'time' in payload && $.isNumeric(payload['time'])) {
                self.job_duration(payload['time']);
            }
            self._fromData(payload);
            self.dialogElement.modal("show");
        };

        self.onEventDustingModeStart = function(payload) {
            self._fromData(payload);
        };

        self.onEventLaserJobDone = function(payload) {
            self._fromData(payload);
            self.dialogElement.modal("show");
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
        }

        self.cancel_btn = function(){
            self.is_job_done(false);
            self.dialogElement.modal("hide");
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        LaserJobDoneViewmodel,
        // e.g. loginStateViewModel, settingsViewModel, ...
        [ /* "loginStateViewModel", "settingsViewModel" */ ],
        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        [ '#laser_job_done_dialog' ]
    ]);
});
