$(function () {
    function NetconnectdWrapperViewModel(parameters) {
        var self = this;
        self.netconnectdViewModel = parameters[0];

        // Disable paging. Scrolling is the new paging...
        self.netconnectdViewModel.listHelper.pageSize(0);

        self.hasDataLoaded = ko.computed(function () {
            var result = self.netconnectdViewModel.hostname() != undefined;
            return result;
        });
        // ip_addresses were introduces in netconnect plugin 0.1.1
        self.ip_available = ko.computed(function () {
            var result =
                self.netconnectdViewModel.status.ip_addresses != undefined;
            return result;
        });

        self.onStartup = function () {
            // needs to be scrollable on touch devices
            $("#wizard_dialog .modal-body").addClass("scrollable");

            $("#wizard_welcome_wifi_config_btn").click(function () {
                $("#wizard_welcome_wifi_configuration").show(500);
                $("#wizard_dialog > .modal-body").animate(
                    { scrollTop: $("#wizard_dialog > .modal-body").height() },
                    "slow"
                );
            });
        };
    }

    // view model class, parameters for constructor, container to bind to
    ADDITIONAL_VIEWMODELS.push([
        NetconnectdWrapperViewModel,
        ["netconnectdViewModel"],
        "#wizard_plugin_corewizard_wifi_netconnectd",
    ]);
});
