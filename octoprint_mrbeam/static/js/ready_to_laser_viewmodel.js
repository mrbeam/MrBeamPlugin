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
        self.gcodeFile = undefined;

        self.interlocks_closed = ko.observable(true);
        self.interlocks_open = ko.pureComputed(function() {
            return !self.interlocks_closed();
        }, self);
        self.is_pause_mode = ko.observable(false);


        self.onStartup = function() {
            self.dialogElement = $('#ready_to_laser_dialog');

            self.dialogElement.on('show.bs.modal', function (e) {
                self.dialogIsInTransition = true;
                if (self.dialogShouldBeOpen != true) {
                    e.preventDefault()
                }
            });
            self.dialogElement.on('hide.bs.modal', function () {
                self.dialogIsInTransition = true;
                if (self.dialogShouldBeOpen != false) {
                    e.preventDefault()
                }
            });
            self.dialogElement.on('shown.bs.modal', function () {
                if (self.dialogShouldBeOpen == true) {
                    self.dialogIsInTransition = false;
                } else {
                    self.hideDialog(true);
                }
            });
            self.dialogElement.on('hidden', function () {
                if (self.dialogShouldBeOpen == false) {
                    self.dialogIsInTransition = false;
                    self.setReadyToLaserCancel();
                } else {
                    self.showDialog(true);
                }
            })

            if (MRBEAM_ENV_LOCAL == "DEV") {
                $('.dev_start_button').on('click', function () {
                    console.log("dev_start_button pressed...")
                    self._sendReadyToLaserRequest(true, true);
                })
            };
        }

        self.setReadyToLaser = function(gcodeFile){
            self.gcodeFile = gcodeFile;
            self.showDialog();
            self._sendReadyToLaserRequest(true);
        }

        self.setReadyToLaserCancel = function(notifyServer){
            notifyServer = notifyServer == false ? false : true // true if undefined
            if (notifyServer && self.gcodeFile == undefined) {
                console.warn("setReadyToLaserCancel() skipping because no gcode file.")
                return
            }
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
            self.dialogShouldBeOpen = true;
            if (!self.dialogIsInTransition || force) {
                if (!self.is_pause_mode()) {
                    self.dialogElement.modal("show");
                } else {
                    // not dismissable in paused mode
                    self.dialogElement.modal({backdrop: 'static', keyboard: false})
                }
            }
        }

        self.hideDialog = function(force) {
            self.dialogShouldBeOpen = false;
            if (!self.dialogIsInTransition || force) {
                self.dialogElement.modal("hide");
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
