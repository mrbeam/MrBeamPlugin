$(function() {
    function NetconnectdWrapperViewModel(parameters) {
        var self = this;
		self.netconnectdViewModel = parameters[0];
	}
	
    // view model class, parameters for constructor, container to bind to
	console.log("ANDYEST beam//js/netconnectd_wrapper.js: pushing NetconnectdWrapperViewModel to ADDITIONAL_VIEWMODELS");
    ADDITIONAL_VIEWMODELS.push([NetconnectdWrapperViewModel, ["netconnectdViewModel"], "#wizard_plugin_corewizard_wifi_netconnectd"]);
});