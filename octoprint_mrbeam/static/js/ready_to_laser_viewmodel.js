/**
 * Created by andy on 03/03/2017.
 */
$(function() {
    function ReadyToLaserViewModel(params) {
        var self = this;
        self.loginState = params[0];
        self.state = params[1];

        self.dialogElement = undefined;
        self.dialogShouldBeOpen = false;
        self.dialogIsInTransition = false;
        self.dialogTimeoutId = -1;
        self.gcodeFile = undefined;

        self.interlocks_closed = ko.observable(true);
        self.interlocks_open = ko.pureComputed(function() {
            return !self.interlocks_closed();
        }, self);
        self.is_pause_mode = ko.observable(false);


        self.onStartup = function() {
            self.dialogElement = $('#ready_to_laser_dialog');

            /**
             * these fucking bs callbacks are unreliable as fuck!!!
             *
             */
            self.dialogElement.on('show.bs.modal', function (e) {
                if (self.dialogShouldBeOpen != true && e != undefined) {
                    console.log("ANDYTEST on(show.bs.modal) skip");
                    e.preventDefault()
                } else {
                    console.log("ANDYTEST on(show.bs.modal) dialogIsInTransition <= true");
                    self.dialogIsInTransition = true;
                }
            });
            self.dialogElement.on('hide.bs.modal', function () {
                if (self.dialogShouldBeOpen != false) {
                    console.log("ANDYTEST on(hide.bs.modal) skip");
                    e.preventDefault()
                } else {
                    console.log("ANDYTEST on(hide.bs.modal) dialogIsInTransition <= true");
                    self.dialogIsInTransition = true;
                }
            });
            self.dialogElement.on('shown.bs.modal', function () {
                if (self.dialogShouldBeOpen == true) {
                    console.log("ANDYTEST on(shown.bs.modal) dialogIsInTransition <= false");
                    self.dialogIsInTransition = false;
                } else {
                    console.log("ANDYTEST on(shown.bs.modal) set timeout (dialogShouldBeOpen not true)");
                    self.setTimeoutForDialog();
                }
            });
            self.dialogElement.on('hidden', function () {
                if (self.dialogShouldBeOpen == false) {
                    console.log("ANDYTEST on(hidden.bs.modal) dialogIsInTransition <= false");
                    self.dialogIsInTransition = false;
                } else {
                    console.log("ANDYTEST on(hidden.bs.modal) set timeout (dialogShouldBeOpen not false)");
                    self.setTimeoutForDialog();
                }
            })

            if (MRBEAM_ENV_LOCAL == "DEV") {
                $('.dev_start_button').on('click', function () {
                    console.log("dev_start_button pressed...")
                    self._sendReadyToLaserRequest(true, true);
                })
            };
        };


        self.setTimeoutForDialog = function(){
            if (self.dialogTimeoutId < 0){
                self.dialogTimeoutId = setTimeout(self.timoutCallbackForDialog, 1500);
                console.log("ANDYTEST setTimeoutForDialog() timeout id: " + self.dialogTimeoutId);
            } else {
                console.log("ANDYTEST setTimeoutForDialog() already timeout existing, id" + self.dialogTimeoutId);
            }
        };

        self.timoutCallbackForDialog = function(){
            console.log("ANDYTEST timoutCallbackForDialog() ");
            clearTimeout(self.dialogTimeoutId);
            self.dialogTimeoutId = -1;

            if (self.dialogShouldBeOpen == true && !self.dialogElement.hasClass('in')){
                console.log("ANDYTEST timoutCallbackForDialog() calling showDialog() : self.dialogShouldBeOpen="+self.dialogShouldBeOpen+", self.dialogElement.hasClass('in')"+self.dialogElement.hasClass('in'));
                self.showDialog(true);
            }else if (self.dialogShouldBeOpen == false && self.dialogElement.hasClass('in')){
                console.log("ANDYTEST timoutCallbackForDialog() calling hideDialog() : self.dialogShouldBeOpen="+self.dialogShouldBeOpen+", self.dialogElement.hasClass('in')"+self.dialogElement.hasClass('in'));
                self.hideDialog(true);
            } else {
                console.log("ANDYTEST timoutCallbackForDialog() dialogIsInTransition <= false");
                self.dialogIsInTransition = false;
            }
        }

        self.setReadyToLaser = function(gcodeFile){
            self.gcodeFile = gcodeFile;
            self.showDialog();
            self._sendReadyToLaserRequest(true);
        }

        self.setReadyToLaserCancel = function(notifyServer){
            notifyServer = notifyServer == false ? false : true // true if undefined
            console.log("setReadyToLaserCancel() notifyServer: ", notifyServer)
            self.hideDialog();
            if (notifyServer) {
                self._sendReadyToLaserRequest(false);
            }
            self.gcodeFile = undefined;
            self.is_pause_mode(false)
        }

        self.cancel_btn = function(){
            if (self.is_pause_mode()) {
                self.state.cancel();
            } else {
                self.setReadyToLaserCancel();
            }
        }

        self.onEventPrintPaused = function(){
            self._set_paused();
        }

        self.onEventPrintCancelled = function(payload) {
            console.log("onEventPrintCanceled() payload: ", payload);
            self.setReadyToLaserCancel(false);
        }

        /**
         * this is listening for data coming through the socket connection
         */
        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin != "mrbeam") {
                return;
            }

            console.log("onDataUpdaterPluginMessage() ", data);

            if (!data) {
                console.warn("onDataUpdaterPluginMessage() received empty data for plugin '"+mrbeam+"'");
                return;
            }

            if ('ready_to_laser' in data && data.ready_to_laser.startsWith("end")) {
                console.log("ReadyToLaser state was ended by the server. data.ready_to_laser=", data.ready_to_laser);
                self.setReadyToLaserCancel(false);

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
        }

        self._set_paused = function(){
            self.is_pause_mode(true);
            self.showDialog();
        }


        self.showDialog = function(force) {
            console.log("ANDYTEST showDialog() " + (force ? "force!" : ""));
            self.dialogShouldBeOpen = true;
            if ((!self.dialogIsInTransition && !self.dialogElement.hasClass('in')) || force) {
                var param = 'show'
                if (self.is_pause_mode()) {
                    // not dismissable in paused mode
                    param = {backdrop: 'static', keyboard: false}
                }

                console.log("ANDYTEST showDialog() dialogIsInTransition <= true");
                self.dialogIsInTransition = true;
                console.log("ANDYTEST showDialog() show");
                self.dialogElement.modal(param);

                self.setTimeoutForDialog();
            } else {
                console.log("ANDYTEST showDialog() skip");
            }
        }

        self.hideDialog = function(force) {
            console.log("ANDYTEST hideDialog() "  + (force ? "force!" : ""));
            self.dialogShouldBeOpen = false;
            if ((!self.dialogIsInTransition && self.dialogElement.hasClass('in')) || force) {
                console.log("ANDYTEST hideDialog() dialogIsInTransition <= true");
                self.dialogIsInTransition = true;
                console.log("ANDYTEST hideDialog() hide");
                self.dialogElement.modal("hide");

                self.setTimeoutForDialog();
            } else {
                console.log("ANDYTEST hideDialog() skip");
            }
        }

        self._sendReadyToLaserRequest = function(ready, dev_start_button) {
            data = {gcode: self.gcodeFile, ready: ready}
            if (dev_start_button) {
                data.dev_start_button = 'start'
            }
            OctoPrint.simpleApiCommand("mrbeam", "ready_to_laser", data);
        }

    }

    OCTOPRINT_VIEWMODELS.push([
        ReadyToLaserViewModel,
        ["loginStateViewModel", "printerStateViewModel"],
        ["#ready_to_laser_dialog"]
    ]);
});
