$(function () {
    function SafecutterModalViewModel(params) {
        let self = this;

        window.mrbeam.viewModels["SafecutterModalViewModel"] = self;

        self.close = function () {
            $("#safecutter_modal").modal("hide");
        };

        self.onEventSafecutterResponse = function (payload) {
            console.log(payload);
            if ([1, 2, 4, 8, 16].includes(payload["value"])) {
                let imageElement = $("#safecutter_image");
                switch (payload["value"]) {
                    case 1:
                        imageElement.attr(
                            "src",
                            "/plugin/mrbeam/static/img/CO.png"
                        );
                        break;
                    case 2:
                        imageElement.attr(
                            "src",
                            "/plugin/mrbeam/static/img/pvc.png"
                        );
                        break;
                    case 4:
                        imageElement.attr(
                            "src",
                            "/plugin/mrbeam/static/img/formaldehyde.png"
                        );
                        break;
                    case 8:
                        imageElement.attr(
                            "src",
                            "/plugin/mrbeam/static/img/dust.png"
                        );
                        break;
                    case 16:
                        imageElement.attr(
                            "src",
                            "/plugin/mrbeam/static/img/ozone.png"
                        );
                        break;
                }
                $("#safecutter_modal").modal("show");
                $("#safecutter_modal").parent().css("z-index", 9000);
                // $("#ready_to_laser_dialog").modal("hide");
            }
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        SafecutterModalViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        [],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#safecutter_modal"],
    ]);
});
