$(function () {
    function HighTemperatureWarningModalViewModel(params) {
        let self = this;
        window.mrbeam.viewModels["HighTemperatureWarningModalViewModel"] = self;

        self.warningTriggeredTime = null;

        self.hardRefreshCheckbox = ko.observable(false);
        self.level = ko.observable(0);
        self.audio = new Audio(
            "/plugin/mrbeam/static/audio/high_temperature_warning.mp3"
        );

        self.onEventHighTemperatureCriticalShow = function (payload) {
            self._showTemperatureWarning();
            self.level(2);
        };

        self.onEventHighTemperatureWarningShow = function (payload) {
            self._showTemperatureWarning();
            self.level(1);
        };

        self.onEventAlarmEnter = function (payload) {
            self._playAlarmSound();
        };

        self.onEventAlarmExit = function (payload) {
            self._stopAlarmSound();
        };

        self.onStartupComplete = function (payload) {
            OctoPrint.simpleApiCommand(
                "mrbeam",
                "high_temperature_warning_status",
                {}
            )
                .done(function (data) {
                    console.log("High Temperature warning status: " + data);
                    if (
                        data.high_temperature_warning ||
                        data.high_temperature_critical
                    ) {
                        self._showTemperatureWarning();
                        if (data.high_temperature_critical) {
                            self.level(2);
                        } else if (data.high_temperature_warning) {
                            self.level(1);
                        }
                    }
                })
                .fail(function (response) {
                    console.log(
                        "Failed to load high temperature warning status!"
                    );
                    console.log(response);
                });
        };

        self.dismissTemperatureWarning = function () {
            OctoPrint.simpleApiCommand(
                "mrbeam",
                "high_temperature_warning_dismiss",
                {}
            )
                .done(function (data) {
                    $("#high_temperature_warning_modal").modal("hide");
                })
                .fail(function (response) {
                    console.log("Failed to dismiss high temperature warning!");
                    console.log(response);
                });
        };

        self._showTemperatureWarning = function () {
            $("#high_temperature_warning_modal").modal("show");
        };

        self._playAlarmSound = function () {
            // Play sound only if the last sound is longer than 5 minutes ago
            if (
                self.warningTriggeredTime + 300000 < Date.now() ||
                self.warningTriggeredTime === null
            ) {
                self.warningTriggeredTime = Date.now();
                self.audio.play();
            }
        };

        self._stopAlarmSound = function () {
            self.audio.pause();
            self.audio.currentTime = 0;
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        HighTemperatureWarningModalViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        [],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#high_temperature_warning_modal"],
    ]);
});
