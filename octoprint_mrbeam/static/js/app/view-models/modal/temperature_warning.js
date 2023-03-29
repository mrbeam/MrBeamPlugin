$(function () {
    function TemperatureWarningModalViewModel(params) {
        let self = this;
        window.mrbeam.viewModels["TemperatureWarningModalViewModel"] = self;

        self.hardRefreshCheckbox = ko.observable(false);
        self.audio = new Audio(
            "/plugin/mrbeam/static/audio/high_temperature_warning.mp3"
        );

        self.onEventHighTemperatureWarning = function (payload) {
            self._showTemperatureWarning();
        };

        self.onStartupComplete = function (payload) {
            OctoPrint.simpleApiCommand(
                "mrbeam",
                "temperature_warning_status",
                {}
            )
                .done(function (data) {
                    console.log("Temperature warning status: " + data);
                    if (data.high_temperature_warning) {
                        self._showTemperatureWarning();
                    }
                })
                .fail(function (response) {
                    console.log("Failed to load temperature warning status!");
                    console.log(response);
                });
        };

        self.dismissTemperatureWarning = function () {
            OctoPrint.simpleApiCommand(
                "mrbeam",
                "dismiss_temperature_warning",
                {}
            )
                .done(function (data) {
                    $("#temperature_warning_modal").modal("hide");
                    self.audio.pause();
                    self.audio.currentTime = 0; // reset audio to start
                })
                .fail(function (response) {
                    console.log("Failed to dismiss temperature warning!");
                    console.log(response);
                });
        };

        self._showTemperatureWarning = function () {
            $("#temperature_warning_modal").modal("show");

            self.audio.play();
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        TemperatureWarningModalViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        [],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#temperature_warning_modal"],
    ]);
});
