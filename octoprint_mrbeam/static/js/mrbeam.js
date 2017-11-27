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
var is_chrome = navigator.userAgent.indexOf('Chrome') > -1;
var is_explorer = navigator.userAgent.indexOf('MSIE') > -1;
var is_firefox = navigator.userAgent.indexOf('Firefox') > -1;
var is_safari = navigator.userAgent.indexOf("Safari") > -1;
var is_opera = navigator.userAgent.toLowerCase().indexOf("op") > -1;
if ((is_chrome)&&(is_safari)) {is_safari=false;}
if ((is_chrome)&&(is_opera)) {is_chrome=false;}


$(function() {
    function MrbeamViewModel(parameters) {
        var self = this;


        self.onStartup = function(){
            self.setScrollModeForTouchDevices();

            $(window).on("orientationchange",self.onOrientationchange);
            self.setBodyScrollTop();
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
