/*
 * View model for Mr_Beam
 *
 * Author: Teja
 * License: AGPLv3
 */
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
        };


        self.onOrientationchange = function(){
            self.setBodyScrollTop();
        };

        self.setBodyScrollTop = function(){
            $('body').scrollTop(0);
        }

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
