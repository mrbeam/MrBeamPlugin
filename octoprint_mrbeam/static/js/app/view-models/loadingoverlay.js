$(function () {
    function LoadingOverlayViewModel(parameters) {
        var self = this;
        window.mrbeam.viewModels["loadingOverlayViewModel"] = self;

        self.TEXT_RELOADING = gettext("connecting...");
        self.allViewModels = null;
        self.showAnimation = true;
        self.display_state = ko.observable(
            $("#loading_overlay_message").text()
        );

        $(".loading_overlay_outer").on("click", function () {
            self.skipClick();
        });
        $("body").addClass("loading_step4");

        self.onStartup = function () {
            $("body").addClass("loading_step5");
        };

        self.onBeforeBinding = function () {
            $("body").addClass("loading_step6");
        };

        self.onAllBound = function (allViewModels) {
            self.allViewModels = allViewModels;
        };

        self.onStartupComplete = function () {
            $("body").addClass("loading_step7");
        };

        $(window).on("beforeunload", function () {
            // do not show reloadingOverlay when it's a file download
            if (!event.target.activeElement.href) {
                console.log("Display reload overlay.");
                self.showReloading();
                callViewModels(self.allViewModels, "onCurtainClosed");
            }
        });

        self.onCurtainOpened = function () {
            const dataUri =
                "data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg enable-background='new 0 0 77.6259842 71.9291306' version='1.1' viewBox='0 0 77.626 71.929' xml:space='preserve' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath fill='%23383e42' d='m58.671 48.069c-1.1834 2.6978-3.1601 3.0271-4.6736 2.4997-1.5136-0.52571-4.0793-5.5938-5.3305-6.844 0.58039-0.060841 1.2816 0.088673 1.6465 0.26328-0.59258-1.054-2.3702-1.3833-5.1332-0.98701 0.32756-0.46053 0.92014-1.053 2.3677-1.4484-5.0012-0.26419-7.0413 3.6197-8.2255 5.989h-0.139c-1.186-2.3694-3.2252-6.2523-8.2272-5.989 1.4475 0.39534 2.0401 0.98785 2.3694 1.4484-2.7647-0.39625-4.5433-0.066944-5.1332 0.98701 0.36316-0.17468 1.0661-0.32412 1.6447-0.26328-1.2503 1.2503-3.8169 6.3175-5.3305 6.844-1.5135 0.5274-3.4893 0.19893-4.6735-2.4997-0.26328 2.7639 0.39527 5.3965 1.2503 6.0551-0.19641 0.082573-0.43796 0.19374-1.054 0-0.32931 0.065117 1.7777 2.3702 6.7137 1.3163 0.054745 0.29629 0.16942 0.68637-0.32847 1.2503 2.7639-0.65778 4.7509-1.7846 6.5816-3.2252 1.6292-1.2833 5.387-1.9315 5.7258-3.4884 0.37445-0.41097 0.74287-0.35363 1.0601 0h-6.87e-5c0.26328 1.5144 4.0967 2.2051 5.7258 3.4884 1.8324 1.4406 3.8187 2.5675 6.5825 3.2252-0.49697-0.56392-0.38146-0.95491-0.32931-1.2503 4.9369 1.0539 7.0413-1.2503 6.7137-1.3163-0.61607 0.19374-0.8567 0.082573-1.0531 0 0.85587-0.65862 1.5136-3.2913 1.2495-6.0551z M70.392 16.93h-25.986c-0.71764 0-1.8155 0.5473-2.1578 0.96003-0.34319 0.41272-1.2225 1.5948-1.2225 1.5948h-3.3982s-0.88012-1.1821-1.2225-1.5948c-0.34143-0.41356-1.4401-0.96003-2.1578-0.96003h-26.044c-0.35272 0-0.5473 0.26952-0.5473 0.54058v2.2655c0 0.17293 0.097643 0.50455 0.24449 0.58095 0.40228 0.20853 1.1714 0.61095 1.3234 0.69086 0.20678 0.10774 0.58572 0.70733 0.66394 1.0183 0.078226 0.31108 3.0271 11.989 3.1896 12.631 0.19031 0.75507 0.85684 1.366 1.7092 1.366h15.827c0.97923 0 2.0688-0.59715 2.5571-1.4782 0.48919-0.88362 5.325-9.6182 5.325-9.6182h1.6599s4.8381 8.7354 5.3272 9.6182c0.4892 0.88194 1.5756 1.4782 2.5548 1.4782h15.831c0.8506 0 1.519-0.61095 1.7092-1.366 0.16164-0.63429 2.4386-9.6608 3.1649-12.534 0.13725-0.54737 0.55046-1.0446 0.90843-1.2314 0.22241-0.11559 0.68792-0.35721 1.0094-0.52487 0.19633-0.10164 0.3387-0.31662 0.3387-0.60338v-2.344c-0.0023117-0.21891-0.21603-0.48899-0.60786-0.48899zm-36.026 4.2798-2.3866 10.363c-0.2841 1.2338-1.5536 2.2408-2.8195 2.2408h-11.72c-1.2659 0-2.4682-1.0228-2.6715-2.2722l-1.6711-10.302c-0.20328-1.2494 0.66759-2.2722 1.9335-2.2722v7.06e-5h17.552c1.2633-8.411e-4 2.0673 1.0092 1.7832 2.243zm31.643 0.029089-1.6711 10.302c-0.20335 1.2495-1.4042 2.2722-2.6692 2.2722h-11.722c-1.2659 0-2.5354-1.0092-2.8195-2.243l-2.3866-10.363c-0.28325-1.2337 0.51955-2.243 1.7855-2.243h17.552c1.2642 9.117e-4 2.1329 1.0251 1.9313 2.2745z'/%3E%3C/svg%3E%0A";
            console.log("beamOS started. Overlay removed.");
            console.log(
                "%c      ",
                `color: transparent; font-size: 150px; background:url("${dataUri}") no-repeat bottom left`
            );
        };

        self.removeLoadingOverlay = function () {
            $("body").addClass("loading_step8");
            self.hideBlockedMessage();

            callViewModels(self.allViewModels, "onCurtainOpening");

            $("body").addClass("run_loading_overlay_animation");
            if (self.showAnimation) {
                setTimeout(function () {
                    $("#loading_overlay").fadeOut();
                    self.resetLoadingSteps();
                    setTimeout(function () {
                        callViewModels(self.allViewModels, "onCurtainOpened");
                    }, 500);
                }, 3000);
            } else {
                $("#loading_overlay").fadeOut();
                self.resetLoadingSteps();
                setTimeout(function () {
                    callViewModels(self.allViewModels, "onCurtainOpened");
                }, 500);
            }
        };

        self.skipClick = function () {
            self.showAnimation = false;
            if (self.isAnimationRunning()) {
                $("#loading_overlay").fadeOut();
                self.resetLoadingSteps();
            }
        };

        self.resetLoadingSteps = function () {
            $("body").removeClass("loading_step1");
            $("body").removeClass("loading_step2");
            $("body").removeClass("loading_step3");
            $("body").removeClass("loading_step4");
            $("body").removeClass("loading_step5");
            $("body").removeClass("loading_step6");
            $("body").removeClass("loading_step7");
            $("body").removeClass("loading_step8");
        };

        self.showReloading = function () {
            $("body").removeClass("run_loading_overlay_animation");
            self.display_state(self.TEXT_RELOADING);
            self.hideBlockedMessage();
            $("#loading_overlay").show();
        };

        self.isAnimationRunning = function () {
            return $("body").hasClass("run_loading_overlay_animation");
        };

        self.hideBlockedMessage = function () {
            $("#loading_overlay_error").hide();
            $("#loading_overlay_error_specific").html("");
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        LoadingOverlayViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        [],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        [document.getElementById("loading_overlay")],
    ]);
});
