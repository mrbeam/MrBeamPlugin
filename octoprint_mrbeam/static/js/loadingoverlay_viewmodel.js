

$(function() {
    function LoadingOverlayViewModel(parameters) {
        var self = this;
        window.mrbeam.viewModels['loadingOverlayViewModel'] = self;

        self.allViewModels = null;

        self.TEXT_RELOADING = gettext("beamOS is reloading...");

        self.display_state = ko.observable($('#loading_overlay_message').text());

        self.onAllBound = function(allViewModels){
            self.allViewModels = allViewModels;
        };

        $( window ).on('beforeunload', function(){
            // do not show reloadingOverlay when it's a file download
            if (!event.target.activeElement.href) {
                console.log("Display reload overlay.");
                self.showReloading();
                callViewModels(self.allViewModels, 'onCurtainClosed');
            }
        });

        self.removeLoadingOverlay = function(){
			$('body').addClass('ready');
			setTimeout(function(){
				$('#loading_overlay').fadeOut();
				$('body').removeClass('loading_step1');
				$('body').removeClass('loading_step2');
				$('body').removeClass('loading_step3');
				$('body').removeClass('loading_step4');
				$('body').removeClass('loading_step5');
				$('body').removeClass('loading_step6');
				$('body').removeClass('loading_step7');
				$('body').removeClass('loading_step8');
				$('body').removeClass('loading_step9');
				
			}, 3000);
            callViewModels(self.allViewModels, 'onCurtainOpened');
            console.log("beamOS started. overlay removed.");
            console.log("%c      ", "color: transparent; font-size: 150px; background:url('https://www.mr-beam.org/wp-content/themes/mrbeam/mysite/images/logo-icon.svg') no-repeat bottom left");
        };

        self.showReloading = function(){
            $('body').removeClass('ready');
			self.display_state(self.TEXT_RELOADING);
            $('#loading_overlay').show();
        };


    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        LoadingOverlayViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        [],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        [ document.getElementById("loading_overlay") ]
    ]);
});
