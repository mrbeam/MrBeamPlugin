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
if ((browser.is_chrome) && (browser.is_safari)) {
    browser.is_safari = false;
}
if ((browser.is_chrome) && (browser.is_opera)) {
    browser.is_chrome = false;
}
if ((browser.is_chrome) && (browser.is_edge)) {
    browser.is_chrome = false;
}

browser.chrome_version = navigator.userAgent.match(/Chrom(e|ium)\/([0-9]+)\./);
browser.chrome_version = browser.chrome_version ? parseInt(browser.chrome_version[2], 10) : null;

// supported browser
browser.is_supported = (browser.is_chrome && browser.chrome_version >= 60) || browser.is_ipad;
mrbeam.browser = browser;

// Mr Beam models
mrbeam.model = {
    MRBEAM2: "MRBEAM2",
    MRBEAM2_DC_R1: "MRBEAM2_DC_R1",
    MRBEAM2_DC_R2: "MRBEAM2_DC_R2",
    MRBEAM2_DC: "MRBEAM2_DC",
    is_mrbeam2: function () {
        return (window.MRBEAM_MODEL === window.mrbeam.model.MRBEAM2);
    },
    is_mrbeam2_dreamcut_ready1: function () {
        return (window.MRBEAM_MODEL === window.mrbeam.model.MRBEAM2_DC_R1);
    },
    is_mrbeam2_dreamcut_ready2: function () {
        return (window.MRBEAM_MODEL === window.mrbeam.model.MRBEAM2_DC_R2);
    },
    is_mrbeam2_dreamcut: function () {
        return (window.MRBEAM_MODEL === window.mrbeam.model.MRBEAM2_DC);
    },
};


/**
 * Test if OctoPrint of a specific or higher version is running.
 * @param expectedOctPrintVersion
 * @returns Boolean or undefined if VERSION is not set
 */
mrbeam.isOctoPrintVersionMin = function (expectedOctPrintVersion) {
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
mrbeam._isVersionOrHigher = function (actualVersion, expectedVersion) {
    var VPAT = /^\d+(\.\d+){0,2}$/;

    if (!actualVersion || !expectedVersion || actualVersion.length === 0 || expectedVersion.length === 0)
        return false;
    if (actualVersion == expectedVersion)
        return true;
    if (VPAT.test(actualVersion) && VPAT.test(expectedVersion)) {
        var lparts = actualVersion.split('.');
        while (lparts.length < 3)
            lparts.push("0");
        var rparts = expectedVersion.split('.');
        while (rparts.length < 3)
            rparts.push("0");
        for (var i = 0; i < 3; i++) {
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

/**
 * Opens an offline version of the KB (pdf) in a new tab/window respecting user's language
 * @param document - document name without path: '43000431865_custom_materials.pdf'
 *                   The document itself needs to be located in static/docs/offline_kb/{locale}/{doc}
 * @param availableLanguages - Array of languages in which the document is available. default: ['en', 'de']
 * @returns false
 */
mrbeam.openOfflineKbUrl = function (document, availableLanguages) {
    availableLanguages = availableLanguages || ['en', 'de']
    var myLang = 'en'
    if (typeof LOCALE !== 'undefined' && availableLanguages.includes(LOCALE)) {
        myLang = LOCALE
    }
    var url = "/plugin/mrbeam/static/docs/offline_kb/" + myLang + "/" + document;
    window.open(url, '_blank')
    return false;
}

/**
 * For debugging offline_kb articles.
 * Stops periodic online check and sets the state to offline/
 * @param locale - if set changes the global LOCALE param.
 *                 (Note that most content doesn't change right away, but offline_kb links do.)
 */
mrbeam.debugSetOfflineState = function(locale){
    if (locale) {
        LOCALE = locale;
    }
    // this will terribly crash if page is not initialized as expected.
    mrbeam.viewModels.mrbeamViewModel.debugSetOfflineState();
};


mrbeam.mrb_state = undefined;
mrbeam.isOnline = undefined;
mrbeam.viewModels = {};

mrbeam.isBeta = function () {
    return MRBEAM_SW_TIER === 'BETA';
};

mrbeam.isDev = function () {
    return MRBEAM_SW_TIER === 'DEV';
};

mrbeam.isProd = function () {
    return MRBEAM_SW_TIER === 'PROD';
};


$(function () {
    // MR_BEAM_OCTOPRINT_PRIVATE_API_ACCESS
    // Force input of the "Add User" E-mail address in Settings > Access Control to lowercase.
    $('#settings-usersDialogAddUserName').attr('data-bind', 'value: $root.users.editorUsername, valueUpdate: \'afterkeydown\'');
    // Check if the entered e-mail address is valid and show error if not.
    $('#settings-usersDialogAddUser > div.modal-body > form > div:nth-child(1)').attr('data-bind', 'css: {error: $root.mrbeam.userTyped() && !$root.mrbeam.validUsername()}');
    $('#settings-usersDialogAddUser > div.modal-body > form > div:nth-child(1) > div').append('<span class="help-inline" data-bind="visible: $root.mrbeam.userTyped() && !$root.mrbeam.validUsername(), text: $root.mrbeam.invalidEmailHelp"></span>');

    function MrbeamViewModel(parameters) {
        var self = this;
        window.mrbeam.viewModels['mrbeamViewModel'] = self;

        self.settings = parameters[0];
        self.wizardacl = parameters[1];
        self.users = parameters[2];
        self.loginState = parameters[3];

        // MR_BEAM_OCTOPRINT_PRIVATE_API_ACCESS
        self.settings.mrbeam = self;

        self._online_check_last_state = null;
        self._online_check_interval = null;

        self.userTyped = ko.observable(false);
        self.invalidEmailHelp = gettext("Invalid e-mail address");

        // This extender forces the input value to lowercase. Used in loginsreen_viewmode.js and wizard_acl.js
        window.ko.extenders.lowercase = function (target, option) {
            target.subscribe(function (newValue) {
                if (newValue !== undefined) {
                    target(newValue.toLowerCase());
                }
            });
            return target;
        };

        self.users.currentUser.subscribe(function (currentUser) {
            if (currentUser === undefined) {
                // MR_BEAM_OCTOPRINT_PRIVATE_API_ACCESS
                // For "Add User" set the Admin checked by default
                self.users.editorAdmin(true)
            }
        });

        self.users.editorUsername.subscribe(function (username) {
            if (username) {
                self.userTyped(true)
            } else {
                self.userTyped(false)
            }
        });

        self.validUsername = ko.pureComputed(function () {
            return self.wizardacl.regexValidateEmail.test(self.users.editorUsername())
        });


        self.onStartup = function () {
            self.start_online_check_interval();

            // set env flag in body for experimental_feature_beta and  experimental_feature_dev
            if (mrbeam.isDev()) {
             $('body').addClass('env_dev')
             $('body').removeClass('env_prod')
            } else if (mrbeam.isBeta()) {
             $('body').addClass('env_beta')
             $('body').removeClass('env_prod')
            }

            $(window).on("orientationchange",self.onOrientationchange);
            self.setBodyScrollTop();

            // MR_BEAM_OCTOPRINT_PRIVATE_API_ACCESS
            // Change "Username" label in Settings > Access Control > Add user
            $('#settings-usersDialogAddUser > div.modal-body > form > div:nth-child(1) > label').text(gettext('E-mail address'));
        };

        self.onAllBound = function(){
            self.set_settings_analytics_links()
        }

        self.onStartupComplete = function(){
            self.presetLoginUser()
        }

        self.onCurtainOpened = function(){
            self.showBrowserWarning()
            self.showBetaNotificaitons()
        }

        self.onOrientationchange = function () {
            self.setBodyScrollTop();
        };

        self.setBodyScrollTop = function () {
            $('body').scrollTop(0);
        };

        self.onDataUpdaterPluginMessage = function (plugin, data) {
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

        self.onUserLoggedOut = function(){
            self.presetLoginUser()
        }

        self.start_online_check_interval = function () {
            self.do_online_check();
            self._online_check_interval = setInterval(self.do_online_check, 60*1000);
        };

        self.debugSetOfflineState = function(offline) {
            let online = typeof offline !== 'undefined' ? offline : false;
            clearInterval(self._online_check_interval)
            mrbeam.isOnline = online;
            self.set_offline_links(online)
        }

        self.do_online_check = function () {
            $.ajax({
                type: "HEAD",
                async: true,
                url: "http://find.mr-beam.org/onlinecheck",
            })
                .done(function () {
                    if (self._online_check_last_state !== true) {
                        console.log("Online check: Online");
                    }
                    self._online_check_last_state = true;
                    mrbeam.isOnline = true;
                    self.set_offline_links(self._online_check_last_state);
                })
                .fail(function () {
                    if (self._online_check_last_state !== false) {
                        console.log("Online check: Offline");
                    }
                    mrbeam.isOnline = false;
                    self._online_check_last_state = false;
                    self.set_offline_links(self._online_check_last_state);

                });
        };

        self.set_offline_links = function (online) {
            if (online) {
                $('body').addClass('online')
                $('body').removeClass('offline')
            } else {
                $('body').addClass('offline')
                $('body').removeClass('online')
            }
        };

        self.set_settings_analytics_links = function(){
            $('.settings_analytics_link').on('click', function (event) {
                // Prevent url change
                event.preventDefault();
                // Open the "Settings" menu
                $("#settings_tab_btn").tab('show');
                // Go to the "Analytics" tab
                $('[data-toggle="tab"][href="#settings_plugin_mrbeam_analytics"]').trigger('click');
            })
        }

        self.showBrowserWarning = function() {
            console.log("Supported Browser: " + mrbeam.browser.is_supported);
            if (!mrbeam.browser.is_supported) {
                new PNotify({
                    title: gettext("Browser not supported."),
                    text: _.sprintf(gettext("Mr Beam makes use of latest web technologies which might not be fully supported by your browser.%(br)sPlease use the latest version of%(br)s%(open)sGoogle Chrome%(close)s for Mr Beam."), {
                        br: "<br/>",
                        open: '<a href=\'https://www.google.com/chrome/\' target=\'_blank\'>',
                        close: '</a>'
                    }),
                    type: 'warn',
                    hide: false
                });
            }
        }

        self.showBetaNotificaitons = function() {
            if (mrbeam.isBeta() && !self.settings.settings.plugins.mrbeam.analyticsEnabled()) {
                new PNotify({
                    title: gettext("Beta user: Please consider enabling Mr Beam analytics!"),
                    text: _.sprintf(gettext("As you are currently in our Beta channel, you would help us " +
                        "tremendously sharing%(br)sthe laser job insights, so we can improve%(br)san overall experience " +
                        "working with the%(br)s Mr Beam. Thank you!%(br)s%(open)sGo to analytics settings%(close)s"),
                        {
                            open: '<a href=\'#\' data-toggle="tab" id="beta_notification_analytics_link" class="settings_analytics_link" style="font-weight:bold">',
                            close: '</a>',
                            br: '<br>'
                        }),
                    type: 'warn',
                    hide: false
                });

                self.set_settings_analytics_links()
                $('#beta_notification_analytics_link').one('click', function (event) {
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
                        {
                            br: '</br>',
                            link1_open: '<a href="https://mr-beam.freshdesk.com/support/solutions/articles/43000507827" target="_blank"><i class="fa fa-external-link" aria-hidden="true"></i> ',
                            link1_close: '</a>',
                            link2_open: '<a href="https://www.mr-beam.org/ticket" target="_blank"><i class="fa fa-external-link" aria-hidden="true"></i> ',
                            link2_close: '</a>'
                        }),
                    type: 'info',
                    hide: true
                });

            }
        }

        self.presetLoginUser = function(){
            if (MRBEAM_ENV_SUPPORT_MODE) {
                self.loginState.loginUser('support'+String.fromCharCode(0x0040)+'mr-beam.org')
                self.loginState.loginPass('a')
            } else if (MRBEAM_ENV === 'DEV') {
                self.loginState.loginUser('dev'+String.fromCharCode(0x0040)+'mr-beam.org')
                self.loginState.loginPass('a')
            }
        }

    };

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        MrbeamViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["settingsViewModel", "wizardAclViewModel", "usersViewModel", "loginStateViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        [ /* ... */]
    ]);
});
