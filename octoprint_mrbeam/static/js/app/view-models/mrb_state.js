$(function () {
    function MrbStateViewModel(parameters) {
        const self = this;
        window.mrbeam.viewModels["mrbStateModel"] = self;

        self.isCooling = ko.observable(undefined);
        self.isAirfilterConnected = ko.observable(undefined);
        self.isAirfilterExternalPowered = ko.observable(undefined);
        self.isRTLMode = ko.observable(undefined);
        self.isPaused = ko.observable(undefined);
        self.isInterlocksClosed = ko.observable(undefined);
        self.isLidFullyOpen = ko.observable(undefined);

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
                window.mrbeam.mrb_state = mrb_state;
                window.STATUS = mrb_state;
                if ("cooling_mode" in mrb_state) {
                    self.isCooling(mrb_state["cooling_mode"]);
                }
                if ("airfilter_model" in mrb_state) {
                    self.airfilter_model(mrb_state["airfilter_model"]);
                }
                if ("airfilter_serial" in mrb_state) {
                    self.airfilter_serial(mrb_state["airfilter_serial"]);
                }

                if ("pause_mode" in mrb_state) {
                    self.isPaused(mrb_state["pause_mode"]);
                }
                if ("interlocks_closed" in mrb_state) {
                    self.isInterlocksClosed(mrb_state["interlocks_closed"]);
                }
                if ("lid_fully_open" in mrb_state) {
                    self.isLidFullyOpen(mrb_state["lid_fully_open"]);
                }
                if ("fan_connected" in mrb_state) {
                    if (mrb_state["fan_connected"] !== null) {
                        self.isAirfilterConnected(mrb_state["fan_connected"]);
                    } else {
                        self.isAirfilterConnected(false);
                    }
                }
                if ("fan_external_power" in mrb_state) {
                    self.isAirfilterExternalPowered(
                        mrb_state["fan_external_power"] === true ||
                            mrb_state["fan_external_power"] === null
                    );
                }
                if ("rtl_mode" in mrb_state) {
                    self.isRTLMode(mrb_state["rtl_mode"]);
                }
            }
        };
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: MrbStateViewModel,
        dependencies: [],
        elements: [],
    });
});
