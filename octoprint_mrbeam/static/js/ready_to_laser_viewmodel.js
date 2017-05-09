/**
 * Created by andy on 03/03/2017.
 */
$(function() {
    function ReadyToLaserViewModel(parameters) {
        var self = this;

        self.loginState = parameters[0];

        self.dialogElement = undefined;
        self.gcodeFile = undefined;

        self.interlocks_closed = ko.observable(true);
        self.interlocks_open = ko.pureComputed(function() {
            return !self.interlocks_closed();
        }, self);
        self.allow_canceling = ko.observable(true);


        self.onStartup = function() {
            self.dialogElement = $('#ready_to_laser_dialog');
            self.dialogElement.on('hidden', function () {
                self.setReadyToLaserCancel();
            })

            if (MRBEAM_ENV_LOCAL == "DEV") {
                $('#dev_start_button').on('click', function () {
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
                return
            }
            console.log("setReadyToLaserCancel() notifyServer: ", notifyServer)
            self.hideDialog();
            if (notifyServer) {
                self._sendReadyToLaserRequest(false);
            }
            self.gcodeFile = undefined;
            self.allow_canceling(true)
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
                    self.allow_canceling(false)
                }
                self.showDialog();
            }

            if ('interlocks_closed' in data) {
                self.interlocks_closed(Boolean(data.interlocks_closed));
            }
        }


        self.showDialog = function() {
            if (!self.dialogElement.hasClass('in')) {
                if (self.allow_canceling()) {
                    self.dialogElement.modal("show");
                } else {
                    self.dialogElement.modal({backdrop: 'static', keyboard: true})
                }
            }
        }

        self.hideDialog = function() {
            if (self.dialogElement.hasClass('in')) {
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
        ["loginStateViewModel"],
        ["#ready_to_laser_dialog"]
    ]);
});
