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
        self.is_pause_mode = ko.observable(false);

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
                 * these fucking bootstrap callbacks are unreliable as fuck!!!
                 */
                self.dialogElement.on('show.bs.modal', function (e) {
                    if (self.dialogShouldBeOpen != true) {
                        if (typeof e !== "undefined") {
                            self._debugDaShit("on(show.bs.modal) skip");
                            e.preventDefault()
                        } else {
                            self._debugDaShit("on(show.bs.modal) cant prevent default event");
                        }
                    } else {
                        self._debugDaShit("on(show.bs.modal) dialogIsInTransition <= true");
                        self.dialogIsInTransition = true;
                    }
                });

                self.dialogElement.on('hide.bs.modal', function () {
                    if (self.dialogShouldBeOpen != false) {
                        if (typeof e !== "undefined") {
                            self._debugDaShit("on(hide.bs.modal) skip");
                            e.preventDefault()
                        } else {
                            self._debugDaShit("on(hide.bs.modal) cant prevent default event");
                        }
                    } else {
                        self._debugDaShit("on(hide.bs.modal) dialogIsInTransition <= true");
                        self.dialogIsInTransition = true;
                    }
                });

                self.dialogElement.on('shown.bs.modal', function () {
                    if (self.dialogShouldBeOpen == true) {
                        self._debugDaShit("on(shown.bs.modal) dialogIsInTransition <= false");
                        self.dialogIsInTransition = false;
                    } else {
                        self._debugDaShit("on(shown.bs.modal) set timeout (dialogShouldBeOpen not true)");
                        self._setTimeoutForDialog();
                    }
                });

                self.dialogElement.on('hidden', function () {
                    if (self.dialogShouldBeOpen == false) {
                        self._debugDaShit("on(hidden.bs.modal) dialogIsInTransition <= false");
                        self.dialogIsInTransition = false;
                    } else {
                        self._debugDaShit("on(hidden.bs.modal) set timeout (dialogShouldBeOpen not false)");
                        self._setTimeoutForDialog();
                    }
                });

                if (MRBEAM_ENV_LOCAL == "DEV") {
                    $('.dev_start_button').on('click', function () {
                        console.log("dev_start_button pressed...")
                        self._sendReadyToLaserRequest(true, true);
                    })
                };

                self.onEventPrintPaused = function () {
                    self._set_paused();
                };

                self.onEventPrintCancelled = function (payload) {
                    self._debugDaShit("onEventPrintCanceled() payload: ", payload);
                    self._setReadyToLaserCancel(false);
                };

                // this is listening for data coming through the socket connection
                self.onDataUpdaterPluginMessage = function(plugin, data) {
                    if (plugin != "mrbeam") {
                        return;
                    }

                    self._debugDaShit("onDataUpdaterPluginMessage() ", data);

                    if (!data) {
                        console.warn("onDataUpdaterPluginMessage() received empty data for plugin '"+mrbeam+"'");
                        return;
                    }

                    if ('ready_to_laser' in data && data.ready_to_laser.startsWith("end")) {
                        console.log("ReadyToLaser state was ended by the server. data.ready_to_laser=", data.ready_to_laser);
                        self._setReadyToLaserCancel(false);

                        if (data.ready_to_laser == "end_lasering") {
                            new PNotify({
                                title: gettext("Laser Started"),
                                text: _.sprintf(gettext("It's real laser, baby!!! Be a little careful, don't leave Mr Beam alone...")),
                                type: "success"
                            });
                        }
                    } else if ('ready_to_laser' in data && data.ready_to_laser.startsWith("start")) {
                        console.log("ReadyToLaser state was started by the server. data.ready_to_laser=", data.ready_to_laser);
                        if (data.ready_to_laser == "start_pause") {
                            self._set_paused();
                        } else {
                            self.showDialog();
                        }
                    }

                    if ('interlocks_closed' in data) {
                        self.interlocks_closed(Boolean(data.interlocks_closed));
                    }
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

        // bound to both cancel buttons
        self.cancel_btn = function(){
            self._debugDaShit("cancel_btn() ");
            if (self.is_pause_mode()) {
                self.state.cancel();
            } else {
                self._setReadyToLaserCancel();
            }
        };

        self._set_paused = function(){
            self.is_pause_mode(true);
            self.showDialog();
        };

        self._setReadyToLaserCancel = function(notifyServer){
            notifyServer = notifyServer == false ? false : true // true if undefined
            self._debugDaShit("_setReadyToLaserCancel() notifyServer: ", notifyServer)
            self.hideDialog();
            if (notifyServer) {
                self._sendReadyToLaserRequest(false);
            }
            self.gcodeFile = undefined;
            self.is_pause_mode(false)
        };

        self.showDialog = function(force) {
            self._debugDaShit("showDialog() " + (force ? "force!" : ""));
            self.dialogShouldBeOpen = true;
            if ((!self.dialogIsInTransition && !self.dialogElement.hasClass('in')) || force) {
                var param = 'show'
                if (self.is_pause_mode()) {
                    // not dismissable in paused mode
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

        self._sendReadyToLaserRequest = function(ready, dev_start_button) {
            data = {gcode: self.gcodeFile, ready: ready}
            if (dev_start_button) {
                data.dev_start_button = 'start'
            }
            OctoPrint.simpleApiCommand("mrbeam", "ready_to_laser", data);
        };

        self._setTimeoutForDialog = function(){
            if (self.dialogTimeoutId < 0){
                self.dialogTimeoutId = setTimeout(self._timoutCallbackForDialog, 1500);
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
                    console.log("ANDYTEST " + stuff.shift(), stuff);
                } else {
                    console.log("ANDYTEST " + stuff);
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
