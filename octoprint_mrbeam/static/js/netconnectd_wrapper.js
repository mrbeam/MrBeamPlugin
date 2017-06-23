$(function() {
    function NetconnectdWrapperViewModel(parameters) {
        var self = this;
		self.netconnectdViewModel = parameters[0];

		// Disable paging. Scrolling is the new paging...
		self.netconnectdViewModel.listHelper.pageSize(0);

        self.hasDataLoaded = ko.computed(function() {
            var result = (self.netconnectdViewModel.hostname() != undefined);
                    return result;
        });

        self.onStartup = function(){
            // needs to be scrollable on touch devices
            $('#wizard_dialog .modal-body').addClass('scrollable');
        };

	}


    // view model class, parameters for constructor, container to bind to
    ADDITIONAL_VIEWMODELS.push([NetconnectdWrapperViewModel, ["netconnectdViewModel"], "#wizard_plugin_corewizard_wifi_netconnectd"]);
});
