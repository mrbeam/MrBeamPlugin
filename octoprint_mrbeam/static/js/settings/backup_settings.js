/* global OctoPrint, OCTOPRINT_VIEWMODELS, INITIAL_CALIBRATION */
$(function () {
    function BackupSettings(params) {
        let self = this;
        self.email = null;
        self.connectAccount = function () {
            $.ajax({
                url: "/plugin/mrbeam/oauth/google/drive",
                dataType: "json",
                contentType: "application/json; charset=UTF-8",
            })
                .done(function (script, textStatus) {
                    alert(response);
                })
                .fail(function (jqxhr, settings, exception) {
                    alert(response);
                });
        }
    }

    // we don't explicitly declare a name property here
    // our view model will be registered under "myCustomViewModel" (implicit
    // name derived from constructor name) and "yourCustomViewModel" (explicitly
    // provided as additional name)
    OCTOPRINT_VIEWMODELS.push({
        construct: BackupSettings,
        dependencies: ["loginStateViewModel", "settingsViewModel"],
        elements: ["#settings_mrbeam_backup"]
    });
});
