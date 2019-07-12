$(function() {
    function WizardWhatsnewViewModel(parameters) {
        var self = this;
        window.mrbeam.viewModels['wizardWhatsnewViewModel'] = self;

        self.settings = parameters[0];
        self.analytics = parameters[1];
        // self.mrbeam = parameters[2];

        self.uuid = ko.observable(null);
        self.registered = ko.observable(null);
        self.ping = ko.observable(false);
        self.verified = ko.observable(false);
        self.tryItButtonClicked = false;
        self.findMrBeamWorks = ko.computed(function(){
            return self.registered() && (self.ping() || self.verified())
        });

        self.onAfterBinding = function(){
            $('#wizard_dialog div.modal-footer button.button-finish').text(gettext("Let's go!"));
            $('#wizard_dialog div.modal-footer div.text-center').hide();
            if (self.is_bound()) {
                // test if bound, only then it's a what's new wizard
                $('#wizard_dialog div.modal-header h3').text("✨ " + gettext("What's New") + " ✨");
                // if(!self.mrbeam.isBeta()) {
                //     $('#wizard_dialog div.modal-header h3').text("✨ " + gettext("What's New") + " ✨");
                // } else {
                //     $('#wizard_dialog div.modal-header h3').text("✨ " + gettext("What's New in the Stable channel") + " ✨");
                // }
            } else{
                // welcome wizard
            }
        };

        self.onStartupComplete = function () {
            self.verifyByFrontend();

            $("#try_findmrbeam_btn").button().click(function(){
                self.tryItButtonClicked = true
            });
        };

        self.onAllBound = function () {
            self.uuid(self.settings.settings.plugins.findmymrbeam.uuid());
            self.registered(self.settings.settings.plugins.findmymrbeam.registered());
            self.ping(self.settings.settings.plugins.findmymrbeam.ping());
        };

        self.onWizardFinish = function(){
            let event = 'whatsnew_findmrbeam';
            let payload = {
                btn_shown: self.findMrBeamWorks(),
                btn_clicked: self.tryItButtonClicked
            };
            self.analytics.send_fontend_event(event, payload);

        };

        self.verifyByFrontend = function() {
            if (self.registered()) {
                let registryUrl = "http://find.mr-beam.org/verify";
                let requestData = {
                    uuid: self.uuid(),
                    frontendHost: document.location.host
                };
                $.get(registryUrl, requestData)
                    .done(function (response) {
                        self.verified(response['verified'] || false);
                        self.verification_response = response
                    })
                    .fail(function () {
                        self.verified(false);
                        self.verification_response = null;

                    })
            } else {
                self.verified(false);
            }
        };

        self.is_bound = function(){
           var elem = document.getElementById(DOM_ELEMENT_TO_BIND_TO);
           return elem ? (!!ko.dataFor(elem)) : false;
        };
    }

    var DOM_ELEMENT_TO_BIND_TO = "wizard_plugin_corewizard_whatsnew_0";
    OCTOPRINT_VIEWMODELS.push([
        WizardWhatsnewViewModel,
        ['settingsViewModel', 'analyticsViewModel'],
        "#"+DOM_ELEMENT_TO_BIND_TO
    ]);
});
