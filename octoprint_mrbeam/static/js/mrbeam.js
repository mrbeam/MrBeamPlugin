/*
 * View model for Mr_Beam
 *
 * Author: Teja
 * License: AGPLv3
 */

/**
    browser detection code
    https://stackoverflow.com/a/7768006/2631798
    Might not be perfect, but for now it's ok.
 */
var mrbeam = window.mrbeam;
var browser = {
    is_chrome: navigator.userAgent.indexOf('Chrome') > -1,
    is_explorer: navigator.userAgent.indexOf('MSIE') > -1,
    is_firefox: navigator.userAgent.indexOf('Firefox') > -1,
    is_safari: navigator.userAgent.indexOf("Safari") > -1,
    is_edge: navigator.userAgent.indexOf("Edge") > -1,
    is_opera: navigator.userAgent.toLowerCase().indexOf("op") > -1,
    is_ipad: navigator.userAgent.indexOf("iPad") > -1,
    is_supported: null,
    chrome_version: null
};
if ((browser.is_chrome)&&(browser.is_safari)) {browser.is_safari=false;}
if ((browser.is_chrome)&&(browser.is_opera)) {browser.is_chrome=false;}
if ((browser.is_chrome)&&(browser.is_edge)) {browser.is_chrome=false;}

browser.chrome_version = navigator.userAgent.match(/Chrom(e|ium)\/([0-9]+)\./);
browser.chrome_version = browser.chrome_version ? parseInt(browser.chrome_version[2], 10) : null;

// supported browser
browser.is_supported = (browser.is_chrome && browser.chrome_version >= 60) || browser.is_ipad;
mrbeam.browser = browser;

// Mr Beam models
mrbeam.model ={
    MRBEAM2:        "MrB2",
    MRBEAM2_DC:     "MrB2-DC",
    MRBEAM2_DCR:    "Mrb2-DCR",
    isMrb2:     function(){return (window.MRBEAM_MODEL === window.mrbeam.model.MRBEAM2);},
    isMrb2DC:   function(){return (window.MRBEAM_MODEL === window.mrbeam.model.MRBEAM2_DC);},
    isMrb2DCR:  function(){return (window.MRBEAM_MODEL === window.mrbeam.model.MRBEAM2_DCR);},
};


/**
 * Test if OctoPrint of a specific or higher version is running.
 * @param expectedOctPrintVersion
 * @returns Boolean or undefined if VERSION is not set
 */
mrbeam.isOctoPrintVersionMin = function(expectedOctPrintVersion){
    if (VERSION) {
        return mrbeam._isVersionOrHigher(VERSION.replace('v', ''), expectedOctPrintVersion);
    } else {
        return undefined;
    }
};

/**
 * compare two versions, return true if actualVersion is up to date, false otherwise
 * if both versions are in the form of major[.minor][.patch] then the comparison parses and compares as such
 * otherwise the versions are treated as strings and normal string compare is done
 * taken from: https://gist.github.com/prenagha/98bbb03e27163bc2f5e4
 * @param actualVersion
 * @param expectedVersion
 * @returns {boolean}
 */
mrbeam._isVersionOrHigher = function(actualVersion, expectedVersion) {
    var VPAT = /^\d+(\.\d+){0,2}$/;

    if (!actualVersion || !expectedVersion || actualVersion.length === 0 || expectedVersion.length === 0)
        return false;
    if (actualVersion == expectedVersion)
        return true;
    if (VPAT.test(actualVersion) && VPAT.test(expectedVersion)) {
        var lparts = actualVersion.split('.');
        while(lparts.length < 3)
            lparts.push("0");
        var rparts = expectedVersion.split('.');
        while (rparts.length < 3)
            rparts.push("0");
        for (var i=0; i<3; i++) {
            var l = parseInt(lparts[i], 10);
            var r = parseInt(rparts[i], 10);
            if (l === r)
                continue;
            return l > r;
        }
        return true;
    } else {
        return actualVersion >= expectedVersion;
    }
};


mrbeam.mrb_state = undefined;
mrbeam.viewModels = {};

mrbeam.isBeta = function() {
    return MRBEAM_SW_TIER === 'BETA';
};

mrbeam.isDev = function() {
    return MRBEAM_SW_TIER === 'DEV';
};

mrbeam.isProd = function() {
    return MRBEAM_SW_TIER === 'PROD';
};



$(function() {
    // MR_BEAM_OCTOPRINT_PRIVATE_API_ACCESS
    // Force input of the "Add User" E-mail address in Settings > Access Control to lowercase.
    $('#settings-usersDialogAddUserName').attr('data-bind','value: $root.users.editorUsername, valueUpdate: \'afterkeydown\'');
    // Check if the entered e-mail address is valid and show error if not.
    $('#settings-usersDialogAddUser > div.modal-body > form > div:nth-child(1)').attr('data-bind', 'css: {error: $root.mrbeam.userTyped() && !$root.mrbeam.validUsername()}');
    $('#settings-usersDialogAddUser > div.modal-body > form > div:nth-child(1) > div').append('<span class="help-inline" data-bind="visible: $root.mrbeam.userTyped() && !$root.mrbeam.validUsername(), text: $root.mrbeam.invalidEmailHelp"></span>');

    function MrbeamViewModel(parameters) {
        var self = this;
        window.mrbeam.viewModels['mrbeamViewModel'] = self;

        self.settings = parameters[0];
        self.wizardacl = parameters[1];
        self.users = parameters[2];

        // MR_BEAM_OCTOPRINT_PRIVATE_API_ACCESS
        self.settings.mrbeam = self;

        self.userTyped = ko.observable(false);
        self.invalidEmailHelp = gettext("Invalid e-mail address");

        // This extender forces the input value to lowercase. Used in loginsreen_viewmode.js and wizard_acl.js
        window.ko.extenders.lowercase = function(target, option) {
            target.subscribe(function(newValue) {
                if(newValue !== undefined) {
                    target(newValue.toLowerCase());
                }
            });
            return target;
        };

        self.users.currentUser.subscribe(function(currentUser) {
            if (currentUser === undefined) {
                // MR_BEAM_OCTOPRINT_PRIVATE_API_ACCESS
                // For "Add User" set the Admin checked by default
                self.users.editorAdmin(true)
            }
        });

        self.users.editorUsername.subscribe(function(username) {
            if (username) {
                self.userTyped(true)
            } else {
                self.userTyped(false)
            }
        });

        self.validUsername = ko.pureComputed(function() {
            return self.wizardacl.regexValidateEmail.test(self.users.editorUsername())
        });


        self.onStartup = function(){
            // self.setScrollModeForTouchDevices();

            $(window).on("orientationchange",self.onOrientationchange);
            self.setBodyScrollTop();

            // MR_BEAM_OCTOPRINT_PRIVATE_API_ACCESS
            // Change "Username" label in Settings > Access Control > Add user
            $('#settings-usersDialogAddUser > div.modal-body > form > div:nth-child(1) > label').text(gettext('E-mail address'));

        };

        self.onStartupComplete = function(){
            console.log("Supported Browser: " + mrbeam.browser.is_supported);
            if (!mrbeam.browser.is_supported){
                new PNotify({
                        title: gettext("Browser not supported."),
                        text: _.sprintf(gettext("Mr Beam II makes use of latest web technologies which are not fully supported by your browser.%(br)sPlease use the latest version of%(br)s%(open)sGoogle Chrome%(close)s for Mr Beam II."), {br: "<br/>", open: '<a href=\'http://www.google.de/chrome/\' target=\'_blank\'>', close:'</a>'}),
                        type: 'warn',
                        hide: false
                    });
            }

            if (mrbeam.isBeta() && !self.settings.settings.plugins.mrbeam.analyticsEnabled()){
                new PNotify({
                        title: gettext("Beta user: Please consider enabling Mr Beam analytics!"),
                        text: _.sprintf(gettext("As you are currently in our Beta channel, you would help us " +
                            "tremendously sharing%(br)sthe laser job insights, so we can improve%(br)san overall experience " +
                            "working with the%(br)s Mr Beam II. Thank you!%(br)s%(open)sGo to analytics settings%(close)s"),
                            {open: '<a href=\'#\' data-toggle="tab" id="settings_analytics_link" style="font-weight:bold">', close:'</a>', br: '<br>'}),
                        type: 'warn',
                        hide: false
                    });

                $('#settings_analytics_link').on('click', function(event) {
                    // Prevent url change
                    event.preventDefault();
                    // Open the "Settings" menu
                    $("#settings_tab_btn").tab('show');
                    // Go to the "Analytics" tab
                    $('[data-toggle="tab"][href="#settings_plugin_mrbeam_analytics"]').trigger('click');
                    // Close notification
                    $('[title="Close"]')[0].click();
                })
            }

            if (mrbeam.isBeta()) {
                 new PNotify({
                        title: gettext("You're using Mr Beam's beta software channel. "),
                        text: _.sprintf(gettext("Find out%(br)s%(link1_open)swhat's new in the beta channel.%(link1_close)s%(br)s%(br)s" +
                            "Should you experience any issues you can always switch back to our stable channel in the software update settings.%(br)s%(br)s " +
                            "Please don't forget to%(br)s%(link2_open)stell us about your experience%(link2_close)s."),
                            {br: '</br>',
                                link1_open: '<a href="https://mr-beam.freshdesk.com/support/solutions/articles/43000507827" target="_blank"><i class="fa fa-external-link" aria-hidden="true"></i> ',
                                link1_close: '</a>',
                                link2_open: '<a href="https://www.mr-beam.org/ticket" target="_blank"><i class="fa fa-external-link" aria-hidden="true"></i> ',
                                link2_close: '</a>'}),
                        type: 'info',
                        hide: true
                    });

            }
        };

        // removed this, seems to be better without. needs testing
        //
        // self.setScrollModeForTouchDevices = function(){
        //     // from https://stackoverflow.com/a/14244680/2631798
        //     var selScrollable = '.scrollable';
        //     // Uses document because document will be topmost level in bubbling
        //     $(document).on('touchmove',function(e){
        //       e.preventDefault();
        //     });
        //     // Uses body because jQuery on events are called off of the element they are
        //     // added to, so bubbling would not work if we used document instead.
        //     $('body').on('touchstart', selScrollable, function(e) {
        //       if (e.currentTarget.scrollTop === 0) {
        //         e.currentTarget.scrollTop = 1;
        //       } else if (e.currentTarget.scrollHeight === e.currentTarget.scrollTop + e.currentTarget.offsetHeight) {
        //         e.currentTarget.scrollTop -= 1;
        //       }
        //     });
        //     // Stops preventDefault from being called on document if it sees a scrollable div
        //     $('body').on('touchmove', selScrollable, function(e) {
        //         // Only block default if internal div contents are large enough to scroll
        //         // Warning: scrollHeight support is not universal. (https://stackoverflow.com/a/15033226/40352)
        //         if($(this)[0].scrollHeight > $(this).innerHeight() || $(this).scrollTop() > 0) {
        //             e.stopPropagation();
        //         }
        //     });
        //
        //     // Still, somethime body scrolls... this fixes it in a very brutal way.
        //     $('body').on('touchend', function(e) {
        //         if ($('body').scrollTop() != 0) {
        //             $('body').scrollTop(0);
        //             console.log("Scroll on body happened. Hard Corrected.");
        //         }
        //     });
        // };


        self.onOrientationchange = function(){
            self.setBodyScrollTop();
        };

        self.setBodyScrollTop = function(){
            $('body').scrollTop(0);
        };

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin != "mrbeam") {
                return;
            }

            if ('frontend_notification' in data) {
                var notification = data['frontend_notification'];
                var delay = (notification['delay']) ? notification['delay'] * 1000 : 10 * 1000;
                new PNotify({
                    title: notification['title'],
                    text: notification['text'],
                    type: notification['type'] || 'info',
                    hide: !(notification['hide'] == false || notification['sticky'] == true),
                    delay: delay
                });
            }
        };

    };

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        MrbeamViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["settingsViewModel", "wizardAclViewModel", "usersViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        [ /* ... */ ]
    ]);
});
