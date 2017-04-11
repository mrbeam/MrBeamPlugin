/**
 * Created by andy on 03/03/2017.
 */
$(function() {
    function ReadyToLaserViewModel(parameters) {
        var self = this;

        self.loginState = parameters[0];

        self.dialogElement = undefined;
        self.gcodeFile = undefined;

        self.interlocks_closed = ko.observable(undefined);
        self.interlocks_open = ko.pureComputed(function() {
            return !self.interlocks_closed();
        }, self);


        self.onStartup = function() {
            self.dialogElement = $('#ready_to_laser_dialog');
            self.dialogElement.on('hidden', function () {
                self.setReadyToLaserCancel();
            })
        }

        self.setReadyToLaser = function(gcodeFile){
            self.gcodeFile = gcodeFile;
            self.showDialog();
            self._sendReadyToLaserRequest(true);
        }

        self.setReadyToLaserCancel = function(notifyServer){
            if (self.gcodeFile == undefined) {
                return
            }
            notifyServer = notifyServer == false ? false : true // true if undefined
            console.log("setReadyToLaserCancel() notifyServer: ", notifyServer)
            self.hideDialog();
            if (notifyServer) {
                self._sendReadyToLaserRequest(false);
            }
            self.gcodeFile = undefined;
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
                console.log("ReadyToLaser state was ended by the server.");
                self.setReadyToLaserCancel(false);

                if (data.ready_to_laser == "end_lasering") {
                    new PNotify({
                        title: gettext("Laser Started"),
                        text: _.sprintf(gettext("It's real laser, baby!!! Be a little careful, don't leave Mr Beam alone...")),
                        type: "success"
                    });
                }
            }

            if ('interlocks_closed' in data) {
                self.interlocks_closed(Boolean(data.interlocks_closed));
            }
        }


        self.showDialog = function() {
            if (!self.dialogElement.hasClass('in')) {
                self.dialogElement.modal("show");
            }
        }

        self.hideDialog = function() {
            if (self.dialogElement.hasClass('in')) {
                self.dialogElement.modal("hide");
            }
        }

        self._sendReadyToLaserRequest = function(ready) {
            OctoPrint.simpleApiCommand("mrbeam", "ready_to_laser", {gcode: self.gcodeFile, ready: ready});
        }

    }

    OCTOPRINT_VIEWMODELS.push([
        ReadyToLaserViewModel,
        ["loginStateViewModel"],
        ["#ready_to_laser_dialog"]
    ]);
});
