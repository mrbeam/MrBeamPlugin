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
    is_opera: navigator.userAgent.toLowerCase().indexOf("op") > -1,
    is_supported: null,
    chrome_version: null
};
if ((browser.is_chrome)&&(browser.is_safari)) {browser.is_safari=false;}
if ((browser.is_chrome)&&(browser.is_opera)) {browser.is_chrome=false;}
browser.chrome_version = navigator.userAgent.match(/Chrom(e|ium)\/([0-9]+)\./);
browser.chrome_version = browser.chrome_version ? parseInt(browser.chrome_version[2], 10) : null;

// supported browser
browser.is_supported = browser.is_chrome && browser.chrome_version >= 60;
mrbeam.browser = browser;

/**
 * Test if OctoPrint of a specific or higher version is running.
 * @param ecpectedOctoPrintVersion
 * @returns Boolean or undefined if VERSION is not set
 */
mrbeam.isOctoPrintVersionMin = function(ecpectedOctoPrintVersion){
    if (VERSION) {
        return mrbeam._isVersionOrHigher(VERSION.replace('v', ''), ecpectedOctoPrintVersion);
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



$(function() {
    function MrbeamViewModel(parameters) {
        var self = this;


        self.onStartup = function(){
            self.setScrollModeForTouchDevices();

            $(window).on("orientationchange",self.onOrientationchange);
            self.setBodyScrollTop();
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
        };


        self.setScrollModeForTouchDevices = function(){
            // from https://stackoverflow.com/a/14244680/2631798
            var selScrollable = '.scrollable';
            // Uses document because document will be topmost level in bubbling
            $(document).on('touchmove',function(e){
              e.preventDefault();
            });
            // Uses body because jQuery on events are called off of the element they are
            // added to, so bubbling would not work if we used document instead.
            $('body').on('touchstart', selScrollable, function(e) {
              if (e.currentTarget.scrollTop === 0) {
                e.currentTarget.scrollTop = 1;
              } else if (e.currentTarget.scrollHeight === e.currentTarget.scrollTop + e.currentTarget.offsetHeight) {
                e.currentTarget.scrollTop -= 1;
              }
            });
            // Stops preventDefault from being called on document if it sees a scrollable div
            $('body').on('touchmove', selScrollable, function(e) {
                // Only block default if internal div contents are large enough to scroll
                // Warning: scrollHeight support is not universal. (https://stackoverflow.com/a/15033226/40352)
                if($(this)[0].scrollHeight > $(this).innerHeight() || $(this).scrollTop() > 0) {
                    e.stopPropagation();
                }
            });

            // Still, somethime body scrolls... this fixes it in a very brutal way.
            $('body').on('touchend', function(e) {
                if ($('body').scrollTop() != 0) {
                    $('body').scrollTop(0);
                    console.log("Scroll on body happened. Hard Corrected.");
                }
            });
        };


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
                new PNotify({
                    title: notification['title'],
                    text: notification['text'],
                    type: notification['type'] || 'info',
                    hide: !(notification['hide'] == false || notification['sticky'] == true)
                });
            }
        };

    };

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        MrbeamViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        [ /* "loginStateViewModel", "settingsViewModel" */ ],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        [ /* ... */ ]
    ]);
});
