/**
 * Created by andy on 03/03/2017.
 */
$(function() {
    function ReadyToLaserViewModel(params) {
        var self = this;
        self.loginState = params[0];
        self.state = params[1];
        self.laserCutterProfiles = params[2];

        self.oneButton = false;

        self.dialogElement = undefined;
        self.dialogShouldBeOpen = false;
        self.dialogIsInTransition = false;
        self.dialogTimeoutId = -1;
        self.gcodeFile = undefined;

        self.interlocks_closed = ko.observable(true);
        self.is_cooling_mode = ko.observable(false);
        self.is_fan_connected = ko.observable(true);
        self.is_rtl_mode = ko.observable(false);

        self.is_pause_mode = ko.observable(false);

        self.estimated_duration = ko.observable(null)

        self.DEBUG = false;



        self.onStartupComplete = function () {
            self.dialogElement = $('#ready_to_laser_dialog');

            /**
             * OneButton
             * The proper way to do this would be to have a callback that gets called by laserCutterProfiles once data are loaded.
             * However, at some point we must register these. And it's safer to assume there is a OneButton...
              */
            self.oneButton = (self.laserCutterProfiles.currentProfileData().start_method != undefined &&
                                self.laserCutterProfiles.currentProfileData().start_method() == "onebutton");
            if (!self.laserCutterProfiles.hasDataLoaded) {
                self.oneButton = true;
                console.warn("OneButton setting not loaded. Assuming OneButton=true for safety reasons. Try reloading the page if you don't have a OneButton.");
            }

            if (self.oneButton) {
                console.log("OneButton activated.");

                /**
                 * Use 'show', 'shown'.. etx instead of 'show.bs.modal' in BS2!!! Otherwise these callbacks are unreliable!
                 * This code has been written with the assumption of these callbacks being unreliable...
                 * https://github.com/jschr/bootstrap-modal/issues/228
                 * Now that I found how to use em correctly, this code seems a bit overly complicated...
                 */
                self.dialogElement.on('show', function (e) {
                    if (self.dialogShouldBeOpen != true) {
                        if (typeof e !== "undefined") {
                            self._debugDaShit("on(show.bs.modal) skip");
                            e.preventDefault()
                        } else {
                            self._debugDaShit("on(show) cant prevent default event");
                        }
                    } else {
                        self._debugDaShit("on(show) dialogIsInTransition <= true");
                        self.dialogIsInTransition = true;
                    }
                });

                self.dialogElement.on('hide', function () {
                    self._setReadyToLaserCancel(true);
                    if (self.dialogShouldBeOpen != false) {
                        if (typeof e !== "undefined") {
                            self._debugDaShit("on(hide) skip");
                            e.preventDefault()
                        } else {
                            self._debugDaShit("on(hide) cant prevent default event");
                        }
                    } else {
                        self._debugDaShit("on(hide) dialogIsInTransition <= true");
                        self.dialogIsInTransition = true;
                    }
                });

                self.dialogElement.on('shown', function () {
                    if (self.dialogShouldBeOpen == true) {
                        self._debugDaShit("on(shown) dialogIsInTransition <= false");
                        self.dialogIsInTransition = false;
                    } else {
                        self._debugDaShit("on(shown) set timeout (dialogShouldBeOpen not true)");
                        self._setTimeoutForDialog();
                    }
                });

                self.dialogElement.on('hidden', function () {
                    if (self.dialogShouldBeOpen == false) {
                        self._debugDaShit("on(hidden) dialogIsInTransition <= false");
                        self.dialogIsInTransition = false;
                    } else {
                        self._debugDaShit("on(hidden) set timeout (dialogShouldBeOpen not false)");
                        self._setTimeoutForDialog();
                    }
                });

                if (MRBEAM_ENV_LOCAL == "DEV") {
                    $('.dev_start_button').on('click', function () {
                        console.log("dev_start_button pressed...")
                        self._sendReadyToLaserRequest(true, true);
                    })
                };

                self.onEventReadyToLaserStart = function (payload) {
                    self._fromData(payload, 'onEventReadyToLaserStart');
                };

                self.onEventReadyToLaserCanceled = function (payload) {
                    self._fromData(payload, 'onEventReadyToLaserCanceled');
                }

                self.onEventPrintStarted = function (payload) {
                    self._fromData(payload, 'onEventPrintStarted');
                }

                self.onEventPrintPaused = function (payload) {
                    self._fromData(payload, 'onEventPrintPaused');
                };

                self.onEventPrintResumed = function (payload) {
                    self._fromData(payload), 'onEventPrintResumed';
                };

                self.onEventPrintCancelled = function (payload) {
                    self._setReadyToLaserCancel(false);
                    self._fromData(payload, 'onEventPrintCancelled');
                };

                self.onEventJobTimeEstimated = function (payload) {

                    self._fromData(payload, 'onEventJobTimeEstimated');
                    self.formatJobTimeEstimation(payload['estimation'])

                };

                self.fromCurrentData = function(data) {
                    self._fromData(data);
                };
            } // end if oneButton
        }; // end onStartupComplete

        /**
         * this is called from the outside once the slicing is done
         * @param gcodeFile
         */
        self.setGcodeFile = function(gcodeFile){
            self.gcodeFile = gcodeFile;
        };

        self.formatJobTimeEstimation = function (seconds){
            seconds = Number(seconds);
            let hours = Math.floor(seconds / 3600);
            let minutes = Math.floor(seconds % 3600 / 60);
            let duration;

            if (hours === 0) {
                if (minutes == 1) {
                    duration = "" + minutes + " " + gettext(" minute")
                } else {
                    duration = "" + minutes + " " + gettext(" minutes")
                }
            } else if (hours === 1) {
                if (minutes < 10) {
                    minutes = "0" + minutes
                }
                duration = hours + ":" + minutes + " " + gettext(" hour")
            } else {
                if (minutes < 10) {
                    minutes = "0" + minutes
                }
                duration = hours + ":" + minutes + " " + gettext(" hours")
            }

            self.estimated_duration("  ~ " + duration)
        };

        // bound to both cancel buttons
        self.cancel_btn = function(){
            self._debugDaShit("cancel_btn() ");
            if (self.is_rtl_mode()){
                self._setReadyToLaserCancel(true);
            } else {
                self.state.cancel();
            }
        };

        self._fromData = function(payload, event) {
            if (!payload || !'mrb_state' in payload || !payload['mrb_state']) {
                return;
            }
            var mrb_state = payload['mrb_state'];
            if (mrb_state) {
                window.mrbeam.mrb_state = mrb_state;
                window.STATUS = mrb_state;

                if ('pause_mode' in mrb_state) {
                    self.is_pause_mode(mrb_state['pause_mode']);
                }
                if ('interlocks_closed' in mrb_state) {
                    self.interlocks_closed(mrb_state['interlocks_closed']);
                }
                if ('cooling_mode' in mrb_state) {
                    self.is_cooling_mode(mrb_state['cooling_mode']);
                }
                if ('fan_connected' in mrb_state) {
                    if (mrb_state['fan_connected'] !== null) {
                        self.is_fan_connected(mrb_state['fan_connected']);
                    }
                }
                if ('rtl_mode' in mrb_state) {
                    self.is_rtl_mode(mrb_state['rtl_mode'])
                }

                self.setDialog();
            }
//            console.log("_fromData() ["+event+"] pause_mode: "+self.is_pause_mode()+", interlocks_closed: "+self.interlocks_closed()+", is_cooling_mode: "+self.is_cooling_mode()+", is_fan_connected: "+self.is_fan_connected() +", is_rtl_mode: "+self.is_rtl_mode());
        }

        self.is_dialog_open = function(){
            return self.is_pause_mode() || self.is_rtl_mode();
        }

        self._setReadyToLaserCancel = function(notifyServer){
            self._debugDaShit("_setReadyToLaserCancel() notifyServer: ", notifyServer)
            self.hideDialog();
            if (notifyServer) {
                self._sendCancelReadyToLaserMode();
            }
            self.gcodeFile = undefined;
        };

        self.setDialog = function() {
            if (self.is_dialog_open()) {
                self.showDialog();
            } else {
                self.hideDialog();
            }
        }

        self.showDialog = function(force) {
            self._debugDaShit("showDialog() " + (force ? "force!" : ""));
            self.dialogShouldBeOpen = true;
            if ((!self.dialogIsInTransition && !self.dialogElement.hasClass('in')) || force) {
                var param = 'show'
                if (!self.is_rtl_mode()) {
                    // not dismissible in paused mode
                    param = {backdrop: 'static', keyboard: (MRBEAM_ENV_LOCAL == "DEV")}
                }

                self._debugDaShit("showDialog() dialogIsInTransition <= true");
                self.dialogIsInTransition = true;
                self._debugDaShit("showDialog() show");
                self.dialogElement.modal(param);

                self._setTimeoutForDialog();
            } else {
                self._debugDaShit("showDialog() skip");
            }
        };

        self.hideDialog = function(force) {
            self._debugDaShit("hideDialog() "  + (force ? "force!" : ""));
            self.dialogShouldBeOpen = false;
            if ((!self.dialogIsInTransition && self.dialogElement.hasClass('in')) || force) {
                self._debugDaShit("hideDialog() dialogIsInTransition <= true");
                self.dialogIsInTransition = true;
                self._debugDaShit("hideDialog() hide");
                self.dialogElement.modal("hide");

                self._setTimeoutForDialog();
            } else {
                self._debugDaShit("hideDialog() skip");
            }
        };

        self._sendCancelReadyToLaserMode = function() {
            data = {rtl_cancel: true}
            OctoPrint.simpleApiCommand("mrbeam", "ready_to_laser", data);
        }

        self._sendReadyToLaserRequest = function(ready, dev_start_button) {
            data = {gcode: self.gcodeFile, ready: ready}
            if (dev_start_button) {
                data.dev_start_button = 'start'
            }
            OctoPrint.simpleApiCommand("mrbeam", "ready_to_laser", data);
        };

        self._setTimeoutForDialog = function(){
            if (self.dialogTimeoutId < 0){
                self.dialogTimeoutId = setTimeout(self._timoutCallbackForDialog, 500);
                self._debugDaShit("_setTimeoutForDialog() timeout id: " + self.dialogTimeoutId);
            } else {
                self._debugDaShit("_setTimeoutForDialog() already timeout existing, id" + self.dialogTimeoutId);
            }
        };

        self._timoutCallbackForDialog = function(){
            self._debugDaShit("_timoutCallbackForDialog() ");
            clearTimeout(self.dialogTimeoutId);
            self.dialogTimeoutId = -1;

            if (self.dialogShouldBeOpen == true && !self.dialogElement.hasClass('in')){
                self._debugDaShit("_timoutCallbackForDialog() calling showDialog() : self.dialogShouldBeOpen="+self.dialogShouldBeOpen+", self.dialogElement.hasClass('in')"+self.dialogElement.hasClass('in'));
                self.showDialog(true);
            }else if (self.dialogShouldBeOpen == false && self.dialogElement.hasClass('in')){
                self._debugDaShit("_timoutCallbackForDialog() calling hideDialog() : self.dialogShouldBeOpen="+self.dialogShouldBeOpen+", self.dialogElement.hasClass('in')"+self.dialogElement.hasClass('in'));
                self.hideDialog(true);
            } else {
                self._debugDaShit("_timoutCallbackForDialog() dialogIsInTransition <= false");
                self.dialogIsInTransition = false;
            }
        };

        self._debugDaShit = function(stuff){
            if (self.DEBUG) {
                if (typeof(stuff) === "object") {
                    console.log("_debugDaShit " + stuff.shift(), stuff);
                } else {
                    console.log("_debugDaShit " + stuff);
                }
            }
        }
    }

    OCTOPRINT_VIEWMODELS.push([
        ReadyToLaserViewModel,
        ["loginStateViewModel", "printerStateViewModel", "laserCutterProfilesViewModel"],
        ["#ready_to_laser_dialog"]
    ]);
});
