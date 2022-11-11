$(function () {
    function HardRefreshOverlayViewModel(params) {
        let self = this;
        window.mrbeam.viewModels["HardRefreshOverlayViewModel"] = self;

        self.settings = params[0];
        self.loginState = params[1];

        self.onUserLoggedIn = function () {
            if (
                self.loginState.currentUser?.()?.active
            ) {
                let x = document.cookie.split('; ').find((row) => row.startsWith('f.u.extra='))?.split('=')[1]; // get cookie
                if (x && x === 'true') {
                    $("#hard_refresh_overlay").modal("show");
                }
            }

        };
        //can be used with newer octoprint version
        self.onEventplugin_softwareupdate_update_succeeded = function () {
            document.cookie = "f.u.extra=true" // add cookie
        }
        // needs to be used for oprint 1.3.6
        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin === "softwareupdate") {
                if ("type" in data && (data["type"] === "success" || data["type"] === "restarting" || data["type"] === "restart_manually")) {
                    document.cookie = "f.u.extra=true"; // add cookie
                }
            }
        }
        self.setUserHardRefreshed = function () {
            document.cookie = "f.u.extra=false; max-age=0" // delete cookie
        }
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        HardRefreshOverlayViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["settingsViewModel", "loginStateViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#hard_refresh_overlay"],
    ]);
});
