$(function () {
    function MrbStateViewModel(parameters) {
        /**
         * The view model for the MrBeam plugin.
         * @type {MrbStateViewModel}
         */
        let self = this;
        window.mrbeam.viewModels["mrbStateModel"] = self;

        self.isCooling = ko.observable(undefined);
        self.airfilter_model = ko.observable(undefined);
        self.airfilter_serial = ko.observable(undefined);

        self.onEventReadyToLaserStart = function (payload) {
            /**
             * Event handler for the event ReadyToLaserStart.
             */
            self._getMrbState(payload);
        };

        self.onEventReadyToLaserCanceled = function (payload) {
            /**
             * Event handler for the event ReadyToLaserCanceled.
             */
            self._getMrbState(payload);
        };

        self.onEventPrintStarted = function (payload) {
            /**
             * Event handler for the event PrintStarted.
             */
            self._getMrbState(payload);
        };

        self.onEventPrintPaused = function (payload) {
            /**
             * Event handler for the event PrintPaused.
             */
            self._getMrbState(payload);
        };

        self.onEventPrintResumed = function (payload) {
            /**
             * Event handler for the event PrintResumed.
             */
            self._getMrbState(payload);
        };

        self.onEventPrintCancelled = function (payload) {
            /**
             * Event handler for the event PrintCancelled.
             */
            self._getMrbState(payload);
        };

        self.fromCurrentData = function (data) {
            /**
             * Will be called when the current data has been updated.
             */
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
            /**
             * Gets the mrb_state from the payload and sets it to the window.mrbeam.mrb_state variable.
             */
            if (
                !payload ||
                !(MRBEAM.STATE_KEY in payload) ||
                !payload[MRBEAM.STATE_KEY]
            ) {
                return;
            }
            let mrb_state = payload[MRBEAM.STATE_KEY];
            if (mrb_state) {
                if ("cooling_mode" in mrb_state) {
                    self.isCooling(mrb_state["cooling_mode"]);
                }
                if ("airfilter_model" in mrb_state) {
                    self.airfilter_model(mrb_state["airfilter_model"]);
                }
                if ("airfilter_serial" in mrb_state) {
                    self.airfilter_serial(mrb_state["airfilter_serial"]);
                }
            }
        };
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: MrbStateViewModel,
        elements: [""],
    });
});
