

$(function() {

    function LoadingOverlayViewModel(parameters) {
        var self = this;
        window.mrbeam.viewModels['loadingOverlayViewModel'] = self;

        self.TEXT_RELOADING = gettext("connecting...");
        self.allViewModels = null;
        self.showAnimation = true;
        self.display_state = ko.observable($('#loading_overlay_message').text());

        $('.loading_overlay_outer').on('click', function(){
            self.skipClick();
        });
        $('body').addClass('loading_step4');


        self.onStartup = function(){
            $('body').addClass('loading_step5');
        };

        self.onBeforeBinding = function(){
            $('body').addClass('loading_step6');
        };

        self.onAllBound = function(allViewModels){
            self.allViewModels = allViewModels;
        };

        self.onStartupComplete = function(){
            $('body').addClass('loading_step7');
        };

        $( window ).on('beforeunload', function(){
            // do not show reloadingOverlay when it's a file download
            if (!event.target.activeElement.href) {
                console.log("Display reload overlay.");
                self.showReloading();
                callViewModels(self.allViewModels, 'onCurtainClosed');
            }
        });

        self.onCurtainOpened = function(){
            console.log("beamOS started. Overlay removed.");
            console.log("%c      ", "color: transparent; font-size: 150px; background:url('https://www.mr-beam.org/wp-content/themes/mrbeam/mysite/images/logo-icon.svg') no-repeat bottom left");
        };

        self.removeLoadingOverlay = function(){
            $('body').addClass('loading_step8');
            $('body').addClass('run_loading_overlay_animation');
            if (self.showAnimation) {
                setTimeout(function () {
                    $('#loading_overlay').fadeOut();
                    self.resetLoadingSteps();
                }, 3000);
            } else {
                $('#loading_overlay').hide();
                self.resetLoadingSteps();
            }
            callViewModels(self.allViewModels, 'onCurtainOpened');
        };

        self.skipClick = function(){
            self.showAnimation = false;
            if (self.isAnimationRunning()) {
                $('#loading_overlay').hide();
                self.resetLoadingSteps();
            }
        };

        self.resetLoadingSteps = function(){
            $('body').removeClass('loading_step1');
            $('body').removeClass('loading_step2');
            $('body').removeClass('loading_step3');
            $('body').removeClass('loading_step4');
            $('body').removeClass('loading_step5');
            $('body').removeClass('loading_step6');
            $('body').removeClass('loading_step7');
            $('body').removeClass('loading_step8');
        };

        self.showReloading = function(){
            $('body').removeClass('run_loading_overlay_animation');
			self.display_state(self.TEXT_RELOADING);
            $('#loading_overlay').show();
        };

        self.isAnimationRunning = function() {
            return $('body').hasClass('run_loading_overlay_animation');
        }

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
