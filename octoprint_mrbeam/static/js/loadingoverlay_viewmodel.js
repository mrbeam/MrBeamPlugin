

$(function() {
    function LoadingOverlayViewModel(parameters) {
        var self = this;

        self.TEXT_RELOADING = gettext('beamOS is reloading...');

        self.display_state = ko.observable($('#loading_overlay_message').text());

        window.onbeforeunload = function(event){
            // do not show reloadingOverlay when it's a file download
            if (!event.target.activeElement.href) {
                console.log("Display reload overlay.");
                self.showReloading();
            }
        };

        self.removeLoadingOverlay = function(){
            $('#loading_overlay').hide();
            console.log("beamOS started. overlay removed.");
            console.log("%c      ", "color: transparent; font-size: 150px; background:url('http://www.mr-beam.org/img/logo2_path.svg') no-repeat bottom left");
        };

        self.showReloading = function(){
            self.display_state(self.TEXT_RELOADING);
            $('#loading_overlay').show();
        };


    };

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        LoadingOverlayViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        [ /* "loginStateViewModel", "settingsViewModel" */ ],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        [ document.getElementById("loading_overlay") ]
    ]);
});
