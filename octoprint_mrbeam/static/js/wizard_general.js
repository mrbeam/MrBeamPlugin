$(function() {
    function WizardWhatsnewViewModel(parameters) {
        var self = this;
        window.mrbeam.viewModels['wizardWhatsnewViewModel'] = self;

        self.SAFETY_LINK = 'wizard_plugin_corewizard_lasersafety_link';
        self.ANALYTICS_LINK = 'wizard_plugin_corewizard_analytics_link';
        self.ACL_LINK = 'wizard_plugin_corewizard_acl_link';

        self.MANDATORY_STEPS = [
            'wizard_plugin_corewizard_lasersafety_link',
            'wizard_plugin_corewizard_analytics_link',
            'wizard_plugin_corewizard_acl_link'
        ];

        self.settings = parameters[0];
        self.analytics = parameters[1];

        self.isWhatsnew = MRBEAM_WIZARD_TO_SHOW === 'WHATSNEW';
        self.isWelcome = MRBEAM_WIZARD_TO_SHOW === 'WELCOME';
        self.aboutToStart = true;

        // WHATSNEW variables
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

            if (self.isWhatsnew) {
                if (!window.mrbeam.isBeta()) {
                    $('#wizard_dialog div.modal-header h3').text("✨ " + gettext("What's New") + " ✨");
                } else {
                    $('#wizard_dialog div.modal-header h3').text("✨ " + gettext("What's New in the Stable Channel") + " ✨");
                }
            }
        };

        self.onStartupComplete = function () {
            if (self.isWhatsnew) {
                self.verifyByFrontend();

                $("#try_findmrbeam_btn").button().click(function () {
                    self.tryItButtonClicked = true
                });
            }
        };

        self.onAllBound = function () {
            if (self.isWhatsnew) {
                self.uuid(self.settings.settings.plugins.findmymrbeam.uuid());
                self.registered(self.settings.settings.plugins.findmymrbeam.registered());
                self.ping(self.settings.settings.plugins.findmymrbeam.ping());
            }
        };

        self.onCurtainOpened = function () {
            if (self.isWelcome) {
                self.analytics.send_fontend_event('welcome_start', {})
            }
        };

        self.onWizardDetails = function(response) {
            if (self.aboutToStart) {
                let links = response.mrbeam.details.links;

                links.forEach(function (linkId) {
                    $('#' + linkId).attr('class', 'wizard-nav-list-next')
                });

                self.aboutToStart = false;
            }
        };

        self.onBeforeWizardTabChange = function(next, current) {
            if(current !== undefined && !self.isMandatoryStep(current)) {
                $('#' + current).attr('class', 'wizard-nav-list-past')
            }
        };

        self.onAfterWizardTabChange = function(current) {
            try {
                $('#' + current).attr('class', 'wizard-nav-list-active')
            } catch (e) {
                console.log('Could not change style of #' + current)
            }
        };

        self.onWizardFinish = function(){
            if (self.isWhatsnew) {
                let event = 'whatsnew_findmrbeam';
                let payload = {
                    btn_shown: self.findMrBeamWorks(),
                    btn_clicked: self.tryItButtonClicked
                };
                self.analytics.send_fontend_event(event, payload);
            } else if (self.isWelcome) {
                self.analytics.send_fontend_event('welcome_finish', {})
                // avoid reloading of the frontend by a CLIENT_CONNECTED / MrbPluginVersion event
                CONFIG_FIRST_RUN = false
            }
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

        self.isMandatoryStep = function(currentTab) {
            return self.MANDATORY_STEPS.includes(currentTab);
        }

    }

    var DOM_ELEMENT_TO_BIND_TO = "wizard_plugin_corewizard_whatsnew_0";
    OCTOPRINT_VIEWMODELS.push([
        WizardWhatsnewViewModel,
        ['settingsViewModel', 'analyticsViewModel'],
        "#"+DOM_ELEMENT_TO_BIND_TO
    ]);
});
