$(function () {

    function MotherViewModel(params) {
        var self = this;
        self.loginState = params[0];
        self.settings = params[1];
        self.state = params[2];
        self.gcodefiles = params[3];
        self.connection = params[4];
        self.control = params[5];
        self.terminal = params[6];
        self.workingArea = params[7];
        self.conversion = params[8];
        self.readyToLaser = params[9];
        self.navigation = params[10];
        self.appearance = params[10];

        self.onStartup = function () {
            // TODO fetch machine profile on start
            //self.requestData();
            self.control.showZAxis = ko.computed(function () {
//				var has = self.currentProfileData()['zAxis']();
//				return has;
                return false;
            });

            self.control.setCoordinateOrigin = function () {
                self.control.sendCustomCommand({type: 'command', command: "G92 X0 Y0"});
            };

            self.control.jogDistanceInMM = ko.observable(undefined);

            self.control.manualPosition = function () {
                $('#manual_position').removeClass('warning');
                var s = $('#manual_position').val();
                var tmp = s.split(/[^0-9.,-\\+]+/);
                if (tmp.length === 2) {
                    var x = parseFloat(tmp[0]);
                    var y = parseFloat(tmp[1]);
                    if (!isNaN(x) && !isNaN(y)) {
                        self.control.sendCustomCommand({type: 'command', command: "G0X" + x + "Y" + y});
                        $('#manual_position').val('');
                    } else {
                        $('#manual_position').addClass('warning');
                    }
                } else {
                    $('#manual_position').addClass('warning');
                }
            };

            // TODO forward to control viewmodel
            self.state.isLocked = ko.observable(undefined);
            self.state.isReady = ko.observable(undefined);
            self.state.isFlashing = ko.observable(undefined);
            self.state.currentPos = ko.observable(undefined);
			self.state.filename = ko.observable(undefined);
			self.state.filesize = ko.observable(undefined);
			self.state.filepos = ko.observable(undefined);
			self.state.progress = ko.observable(undefined);
			self.state.printTime = ko.observable(undefined);

            self.state.intensityOverride = ko.observable(100);
            self.state.feedrateOverride = ko.observable(100);
            self.state.intensityOverride.extend({rateLimit: 500});
            self.state.feedrateOverride.extend({rateLimit: 500});
            self.state.numberOfPasses = ko.observable(1);
            self.state.isConnecting = ko.observable(undefined);

            self.state.intensityOverride.subscribe(function (factor) {
                self.state._overrideCommand({name: "intensity", value: factor});
            });
            self.state.feedrateOverride.subscribe(function (factor) {
                self.state._overrideCommand({name: "feedrate", value: factor});
            });

			self.state.byteString = ko.computed(function() {
				if (!self.state.filesize())
					return "-";
				var filepos = self.state.filepos() ? formatSize(self.state.filepos()) : "-";
				return filepos + " / " + formatSize(self.state.filesize());
			});
            self.state.laserPos = ko.computed(function () {
                var pos = self.state.currentPos();
                if (!pos) {
                    return "(?, ?)";
                } else {
                    return "(" + pos.x + ", " + pos.y + ")";
                }
            }, this);
			self.state.printTimeString = ko.computed(function() {
				if (!self.state.printTime())
					return "-";
				return formatDuration(self.state.printTime());
			});

            self.setupFullscreenContols();
        };

        self.onAllBound = function (allViewModels) {
            var tabs = $('#mrbeam-main-tabs a[data-toggle="tab"]');
            tabs.on('show', function (e) {
                var current = e.target.hash;
                var previous = e.relatedTarget.hash;
//                log.debug("Selected OctoPrint tab changed: previous = " + previous + ", current = " + current);
                OctoPrint.coreui.selectedTab = current;
                callViewModels(allViewModels, "onTabChange", [current, previous]);
            });

            tabs.on('shown', function (e) {
                var current = e.target.hash;
                var previous = e.relatedTarget.hash;
                callViewModels(allViewModels, "onAfterTabChange", [current, previous]);
            });

            self._configureOverrideSliders();

			self.gcodefiles.listHelper.toggleFilter('model');

			// adjust height of designlib scroll element
			var height = $('#designlib').height();
			$("#designlib .slimScrollDiv").height(height);
			$(".gcode_files").height(height);

			// terminal stuff
            $("#terminal-output").scroll(function() {
                 self.terminal.checkAutoscroll();
            });
            self.terminal.activeAllFilters();
        };

        self.onStartupComplete = function() {
            $('#loading_overlay').remove();
        };


        /**
         * controls fullscreen functionality unsing on screenfull.js
         */
        self.setupFullscreenContols = function(){
            // Doesnt seem to work with Knockout so ket's do it manually...
            console.log("screenfull: screenfull.enabled: ", screenfull.enabled);

            if (screenfull.enabled) {
                self._updateFullscreenButton();

                screenfull.onerror(function(event){
                    console.log('screenfull: Failed to enable fullscreen ', event);
                });

                $('#go_fullscreen_menu_item').on( "click", function() {
                    console.log("screenfull: go_fullscreen_menu_item click");
                    screenfull.request();
                    self._updateFullscreenButton(true);
                });
                $('#exit_fullscreen_menu_item').on( "click", function() {
                    console.log("screenfull: exit_fullscreen_menu_item click");
                    screenfull.exit();
                    self._updateFullscreenButton(false);
                });
                $('#burger_menu_link').on( "click", function() {
                    self._updateFullscreenButton();
                });
            } else {
                $('.fullscreen').hide();
            }
        };


        self._updateFullscreenButton = function(isFullscreen){
            if (isFullscreen === undefined) {
                isFullscreen = screenfull.isFullscreen;
            }
            if (isFullscreen) {
                $('#go_fullscreen_menu_item').hide();
                $('#exit_fullscreen_menu_item').show();
            } else {
                $('#go_fullscreen_menu_item').show();
                $('#exit_fullscreen_menu_item').hide();
            }
        };

        self.fromCurrentData = function (data) {
            self._fromData(data);
        };

        self.fromHistoryData = function (data) {
            self._fromData(data);
        };

        self._fromData = function (data) {
            self._processStateData(data.state);
            self._processWPosData(data.workPosition);
			self._processProgressData(data.progress);
			self._processJobData(data.job);
        };

        self._processStateData = function (data) {
            self.state.isLocked(data.flags.locked);
            self.state.isFlashing(data.flags.flashing);
            self.state.isConnecting(data.text === "Connecting" || data.text === "Opening serial port");
        };

        self._processWPosData = function (data) {
            if (data == null) {
                self.state.currentPos({x: 0, y: 0});
            } else {
                self.state.currentPos({x: data[0], y: data[1]});
            }
        };

        self._processProgressData = function(data) {
            if (data.completion) {
                self.state.progress(data.completion);
            } else {
                self.state.progress(undefined);
            }
            self.state.filepos(data.filepos);
            self.state.printTime(data.printTime);
            //self.printTimeLeft(data.printTimeLeft);
        };

        self._processJobData = function(data) {
            if (data.file) {
                self.state.filename(data.file.name);
                self.state.filesize(data.file.size);
            } else {
                self.state.filename(undefined);
                self.state.filesize(undefined);
            }
            // TODO make the estimated print time work
            //self.estimatedPrintTime(data.estimatedPrintTime);
            //self.lastPrintTime(data.lastPrintTime);
        };

        self._configureOverrideSliders = function () {
            self.state.intensityOverrideSlider = $("#intensity_override_slider").slider({
                step: 1,
                min: 10,
                max: 200,
                value: 100,
            }).on("slideStop", function (ev) {
                self.state.intensityOverride(ev.value);
            });

            self.state.feedrateOverrideSlider = $("#feedrate_override_slider").slider({
                step: 1,
                min: 10,
                max: 200,
                value: 100,
            }).on("slideStop", function (ev) {
                self.state.feedrateOverride(ev.value);
            });

        };

        self.state.resetOverrideSlider = function () {
            self.state.feedrateOverrideSlider.slider('setValue', 100);
            self.state.intensityOverrideSlider.slider('setValue', 100);
            self.state.intensityOverride(100);
            self.state.feedrateOverride(100);
        };

		self.state.increasePasses = function(){
			self.state.numberOfPasses(self.state.numberOfPasses()+1);
            self.state._overrideCommand({name: "passes", value: self.state.numberOfPasses()});
		};

		self.state.decreasePasses = function(){
			var passes = Math.max(self.state.numberOfPasses()-1, 1);
			self.state.numberOfPasses(passes);
            self.state._overrideCommand({name: "passes", value: self.state.numberOfPasses()});
		};

        self.state._overrideCommand = function (data, callback) {
            $.ajax({
                url: API_BASEURL + "plugin/mrbeam",
                type: "POST",
                dataType: "json",
                contentType: "application/json; charset=UTF-8",
                data: JSON.stringify({command: data.name, value: data.value}),
                success: function (response) {
                    if (callback != undefined) {
                        callback();
                    }
                }
            });
        };


        // files.js viewmodel extensions

        self.gcodefiles.templateFor = function (data) {
            if (data.type === 'folder') {
                return 'files_template_folder';
            } else {
                return "files_template_" + data.typePath.join('_');
            }
        };

        self.gcodefiles.startGcodeWithSafetyWarning = function (gcodeFile) {
            self.gcodefiles.loadFile(gcodeFile, false);
            if (self.readyToLaser.oneButton) {
                self.readyToLaser.setGcodeFile(gcodeFile.path);
            } else {
                self.show_safety_glasses_warning(function () {
                    var do_print = self.gcodefiles.loadFile(gcodeFile, true);
                });
            }
        };

        self.gcodefiles.takePhoto = function () {
            $('#take_photo_dialog').modal("show");
        };

        self.gcodefiles.hasCamera = function () {
            var fGetUserMedia = (
                navigator.getUserMedia ||
                navigator.webkitGetUserMedia ||
                navigator.mozGetUserMedia ||
                navigator.oGetUserMedia ||
                navigator.msieGetUserMedia ||
                false
            );
            return !!fGetUserMedia;
        };

        self.gcodefiles.onEventSlicingDone = function (payload) {
            var url = API_BASEURL + "files/" + payload.gcode_location + "/" + payload.gcode;
            var data = {refs: {resource: url}, origin: payload.gcode_location, path: payload.gcode};
            self.gcodefiles.loadFile(data, false); // loads gcode into gcode viewer
            if (self.readyToLaser.oneButton) {
                self.readyToLaser.setGcodeFile(payload.gcode);
            } else {
                var callback = function (e) {
                    e.preventDefault();
                    self.gcodefiles.loadFile(data, true); // starts print
                };
                self.show_safety_glasses_warning(callback);
            }
			self.gcodefiles.uploadProgress
                .removeClass("progress-striped")
                .removeClass("active");
            self.gcodefiles.uploadProgressBar
                .css("width", "0%");
            self.gcodefiles.uploadProgressBar.text("");

            new PNotify({
                title: gettext("Slicing done"),
                text: _.sprintf(gettext("Sliced %(stl)s to %(gcode)s, took %(time).2f seconds"), payload),
                type: "success"
            });

            // self.gcodefiles.requestData(undefined, undefined, self.gcodefiles.currentPath());
            self.gcodefiles.requestData({switchToPath: self.gcodefiles.currentPath()});
        };


        // settings.js viewmodel extensions

        self.settings.saveall = function (e, v) {
            if (self.settings.savetimer !== undefined) {
                clearTimeout(self.settings.savetimer);
            }
			// only trigger autosave if there is something changed.
			// the port scanning from the backend otherwise triggers it frequently
			var data = getOnlyChangedData(self.settings.getLocalData(), self.settings.lastReceivedSettings);
			if(Object.getOwnPropertyNames(data).length > 0){
			    $("#settingsTabs").find("li.active").addClass('saveInProgress');
				self.settings.savetimer = setTimeout(function () {
					self.settings.saveData(undefined, function () {
						$("#settingsTabs").find("li.active").removeClass('saveInProgress');
						self.settings.savetimer = undefined;
					});
				}, 2000);
			}
        };

        $('#settings_dialog_content').has('input, select, textarea').on('change', function () {
            self.settings.saveall();
        });

        self.terminal.onAfterTabChange = function (current, previous) {
            self.terminal.tabActive = current == "#mrb_term";
            self.terminal.updateOutput();
        };

        self.terminal.checkAutoscroll = function(){
            var elem = $("#terminal-output");
            var isScrolledToBottom = elem[0].scrollHeight <= elem.scrollTop() + elem.outerHeight();
            self.terminal.autoscrollEnabled(isScrolledToBottom);
        };

        self.terminal.activeAllFilters = function(){
            var filters = self.terminal.filters();
            for (var i = 0; i < filters.length; i++) {
                if (filters[i].activated) {
                    self.terminal.activeFilters.push(filters[i].regex);
                }
            }
        };

        self.show_safety_glasses_warning = function (callback) {
            var options = {};
            options.title = gettext("Ready to laser?");

            if (self.workingArea.profile.currentProfileData().glasses()) {
            options.cancel = gettext("Cancel");
            options.proceed = gettext("Proceed");
                options.message = gettext("The laser will now start. Protect yourself and everybody in the room appropriately before proceeding!");
                options.question = gettext("Are you sure you want to proceed?");
                options.proceedClass = "danger";
                options.dialogClass = "safety_glasses_heads_up";
            } else {
                options.message = gettext("The laser will now start. Please make sure the lid is closed.");
                options.question = gettext("Please confirm to proceed.");
            }

            options.onproceed = function (e) {
                if (typeof callback === 'function') {
                    self.state.resetOverrideSlider();
//                    self.state.numberOfPasses(parseInt(self.conversion.set_passes()));
//                    self.state._overrideCommand({name: "passes", value: self.state.numberOfPasses()});
                    callback(e);
                }
            };
            showConfirmationDialog(options);
        };


        // who calls this????
        // self.print_with_safety_glasses_warning = function () {
        //     var callback = function (e) {
        //         e.preventDefault();
        //         /// ...and where is this function 'print()' defined???
        //         self.print();
        //     };
        //     self.show_safety_glasses_warning(callback);
        // };
    }


    // view model class, parameters for constructor, container to bind to
    ADDITIONAL_VIEWMODELS.push([MotherViewModel,
        ["loginStateViewModel", "settingsViewModel", "printerStateViewModel", "gcodeFilesViewModel",
            "connectionViewModel", "controlViewModel", "terminalViewModel", "workingAreaViewModel",
            "vectorConversionViewModel", "readyToLaserViewModel", "navigationViewModel", "appearanceViewModel"],
        [document.getElementById("mrb_state"),
            document.getElementById("mrb_control"),
            document.getElementById("mrb_connection_wrapper"),
            document.getElementById("mrb_state_wrapper"),
            document.getElementById("mrb_term"),
            document.getElementById("focus")
        ]]);

    // third party model binding
    OCTOPRINT_ADDITIONAL_BINDINGS.push(['gcodeFilesViewModel', ["#design_lib_search"]]);
});

