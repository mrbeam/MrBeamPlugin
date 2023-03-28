$(function () {
    function TemperatureWarningModalViewModel(params) {
        let self = this;
        window.mrbeam.viewModels["TemperatureWarningModalViewModel"] = self;

        self.hardRefreshCheckbox = ko.observable(false);

        self.onEventHighTemperatureWarning = function (payload) {
            self._showTemperatureWarning();
        };

        self.onStartupComplete = function (payload) {
            if (MRBEAM_HIGH_TMP_WARNING) {
                self._showTemperatureWarning();
            }
        };

        self.dismissTemperatureWarning = function () {
            OctoPrint.simpleApiCommand(
                "mrbeam",
                "dismiss_temperature_warning",
                {}
            )
                .done(function (data) {
                    $("#temperature_warning_modal").modal("hide");
                })
                .fail(function (response) {
                    console.log("Failed to dismiss temperature warning!");
                    console.log(response);
                });
        };

        self._showTemperatureWarning = function () {
            $("#temperature_warning_modal").modal("show");
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
