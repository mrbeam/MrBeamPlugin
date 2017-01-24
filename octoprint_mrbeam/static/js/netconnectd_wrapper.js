$(function() {
    function NetconnectdWrapperViewModel(parameters) {
        var self = this;
		self.netconnectdViewModel = parameters[0];
		
		// Disable paging. Scrolling is the new paging...
		self.netconnectdViewModel.listHelper.pageSize(0);
		
		self.hasDataLoaded = ko.computed(function() {
			return (self.netconnectdViewModel.hostname() != undefined);
		});
		
        
        self.netconnectdViewModel.confirmWifiConfiguration = function() {
            var self = this;
            
            self.sendWifiConfig(self.editorWifiSsid(), self.editorWifiPassphrase1(),
            // successCallback 
            function() {
                var myWifi = self.editorWifiSsid();
                // console.log("ANDYTEST confirmWifiConfiguration successCallback() - " + myWifi);
                self.editorWifi = undefined;
                self.editorWifiSsid(undefined);
                self.editorWifiPassphrase1(undefined);
                self.editorWifiPassphrase2(undefined);
                self.refresh();
                $("#settings_plugin_netconnectd_wificonfig").modal("hide");
                new PNotify({
                    title: gettext("Wifi Connected"),
                    text: _.sprintf(gettext("Mr Beam 2 is now connceted to your wifi '%s'."), myWifi),
                    type: "success"
                });
            },
            // failureCallback
            function() {
                var myWifi = self.editorWifiSsid();
                // console.log("ANDYTEST confirmWifiConfiguration failureCallback() - " + myWifi);
                self.refresh();
                $("#settings_plugin_netconnectd_wificonfig").modal("hide");
                new PNotify({
                    title: gettext("Connection failed"),
                    text: _.sprintf(gettext("Mr Beam 2 could not connect to your wifi '%s'. Did you enter the correct passphrase?"), myWifi),
                    type: "error"
                });
            });
        };
        
        // the whole difference is that I increased the timeout for _postCommand 
        self.netconnectdViewModel.sendWifiConfig = function(ssid, psk, successCallback, failureCallback) {
            var self = this;
            
            if (!self.loginState.isAdmin()) return;

            self.working(true);
            if (self.status.connections.ap()) {
                self.reconnectInProgress = true;

                var reconnectText = gettext("OctoPrint is now switching to your configured Wifi connection and therefore shutting down the Access Point. I'm continuously trying to reach it at <strong>%(hostname)s</strong> but it might take a while. If you are not reconnected over the next couple of minutes, please try to reconnect to OctoPrint manually because then I was unable to find it myself.");

                showOfflineOverlay(
                    gettext("Reconnecting..."),
                    _.sprintf(reconnectText, {hostname: self.hostname()}),
                    self.tryReconnect
                );
            }
            self._postCommand("configure_wifi", {ssid: ssid, psk: psk}, successCallback, failureCallback, function() {
                self.working(false);
                if (self.reconnectInProgress) {
                    self.tryReconnect();
                }
            }, 80000);
        };
	}
	
    // view model class, parameters for constructor, container to bind to
    ADDITIONAL_VIEWMODELS.push([NetconnectdWrapperViewModel, ["netconnectdViewModel"], "#wizard_plugin_corewizard_wifi_netconnectd"]);
});