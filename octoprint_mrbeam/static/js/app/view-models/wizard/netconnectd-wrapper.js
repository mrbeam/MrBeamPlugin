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
            self.onConnectionOptionSelection(
                $("#connection-wizard__a--option-a"),
                $("#connection-wizard--selected-option-a")
            );
            self.onConnectionOptionSelection(
                $("#connection-wizard__a--option-b"),
                $("#connection-wizard--selected-option-b")
            );
            self.onConnectionOptionSelection(
                $("#connection-wizard__a--option-c"),
                $("#connection-wizard--selected-option-c")
            );
            $(".connection-wizard__btn--back").click(function () {
                self.onBackToAllOptions();
            });
        };

        self.onConnectionOptionSelection = function (
            triggerElement,
            divElementToShow
        ) {
            console.log(divElementToShow);
            triggerElement.click(function () {
                $("#connection-wizard--general-connection-details").hide(300);
                $("#connection-wizard--selected-option").show(300);
                divElementToShow.show(300);
                self.scrollTop();
            });
        };

        self.onBackToAllOptions = function () {
            $("#connection-wizard--selected-option").hide(300);
            $(".connection-wizard--selected-option").hide(300);
            $("#connection-wizard--general-connection-details").show(500);
            self.scrollTop();
        };

        self.scrollTop = function () {
            const wizardModalBody = $("#wizard_dialog > .modal-body");
            wizardModalBody.animate({ scrollTop: 0 }, "slow");
        };
    }

    // view model class, parameters for constructor, container to bind to
    ADDITIONAL_VIEWMODELS.push([
        NetconnectdWrapperViewModel,
        ["netconnectdViewModel"],
        "#wizard_plugin_corewizard_connection",
    ]);
});
