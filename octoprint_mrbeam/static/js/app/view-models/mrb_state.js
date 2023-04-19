$(function () {
    function MrbStateViewModel(parameters) {
        var self = this;
        window.mrbeam.viewModels["mrbStateModel"] = self;

        self.isCooling = ko.observable(undefined);

        self.onEventReadyToLaserStart = function (payload) {
            self._getMrbState(payload);
        };

        self.onEventReadyToLaserCanceled = function (payload) {
            self._getMrbState(payload);
        };

        self.onEventPrintStarted = function (payload) {
            self._getMrbState(payload);
        };

        self.onEventPrintPaused = function (payload) {
            self._getMrbState(payload);
        };

        self.onEventPrintResumed = function (payload) {
            self._getMrbState(payload);
        };

        self.onEventPrintCancelled = function (payload) {
            self._getMrbState(payload);
        };

        self.fromCurrentData = function (data) {
            self._getMrbState(data);
        };

        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin !== MRBEAM.PLUGIN_IDENTIFIER) {
                return;
            }
            if (MRBEAM.STATE_KEY in data) {
                self._getMrbState(data, "onDataUpdaterPluginMessage");
            }
        };

        self._getMrbState = function (payload) {
            if (
                !payload ||
                !(MRBEAM.STATE_KEY in payload) ||
                !payload[MRBEAM.STATE_KEY]
            ) {
                return;
            }
            let mrb_state = payload[MRBEAM.STATE_KEY];
            if (mrb_state) {
                // TODO: All the handling of mrb_state data should be moved into a dedicated view model
                window.mrbeam.mrb_state = mrb_state;
                window.STATUS = mrb_state;
                if ("cooling_mode" in mrb_state) {
                    self.isCooling(mrb_state["cooling_mode"]);
                }
            }
        };
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: MrbStateViewModel,
        elements: [""],
    });
});
