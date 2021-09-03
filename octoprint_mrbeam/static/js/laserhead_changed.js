$(function () {
    function LaserheadChangedViewModel(params) {
        let self = this;
        window.mrbeam.viewModels["LaserheadChangedViewModel"] = self;

        self.settings = params[0];
        self.loginState = params[1];

        self.onUserLoggedIn = function () {
            if (
                self.loginState.currentUser?.()?.active
            ) {
                let laserheadChanged = self.settings.settings.plugins.mrbeam.laserheadChanged();
                if (laserheadChanged) {
                    $("#laserhead_changed").modal("show");
                }
            }
        };

        self.laserheadChangedDetected = function (){
            let data = {
                laserheadChanged: false,
            };
            OctoPrint.simpleApiCommand("mrbeam", "laserhead_changed", data)
                .done(function (response) {
                    self.settings.requestData();
                    console.log(
                        "simpleApiCall response for saving laserhead change detection: ",
                        response
                    );
                })
                .fail(function () {
                    self.settings.requestData();
                    console.error("Unable to save laserhead change detection state: ", data);
                    new PNotify({
                        title: gettext("Error while saving laserhead change detection!"),
                        text: _.sprintf(
                            gettext(
                                "Unable to save laserhead change detection at the moment.%(br)sCheck connection to Mr Beam and try again."
                            ),
                            { br: "<br/>" }
                        ),
                        type: "error",
                        hide: true,
                    });
                });
        }
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        LaserheadChangedViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["settingsViewModel", "loginStateViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#laserhead_changed"],
    ]);
});
