/* global _ */

$(function () {

    function MotherViewModel(params) {
        var self = this;
        window.mrbeam.viewModels['motherViewModel'] = self;

        self.loginState = params[0];
        self.settings = params[1];
        self.state = params[2];
        self.files = params[3];
        self.gcodefiles = params[4];
        self.connection = params[5];
        self.control = params[6];
        self.terminal = params[7];
        self.workingArea = params[8];
        self.conversion = params[9];
        self.readyToLaser = params[10];
        self.navigation = params[11];
        self.appearance = params[12];
        self.loadingOverlay = params[13];
        self.softwareUpdate = params[14];
        self.analytics = params[15];

        self.isStartupComplete = false;
        self.storedSocketData = [];

        self.localPrintTime = 0;
        self.serverPrintTime = 0;
        self.printTimeInterval = null;

        // MrBeam Logo click activates workingarea tab
        $('#mrbeam_logo_link').click(function() {
            $('#wa_tab_btn').tab('show');
        });

        // get the hook when softwareUpdate get data from server
        self.fromCheckResponse_copy = self.softwareUpdate.fromCheckResponse;
        self.softwareUpdate.fromCheckResponse = function(data, ignoreSeen, showIfNothingNew) {
            self.fromCheckResponse_copy(data, ignoreSeen, showIfNothingNew);
            self.writeBranchesToSwUpdateScreen();
        };

        self.state.TITLE_PRINT_BUTTON_UNPAUSED = gettext("Starts the laser job");

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

            self.control.manualPosition = function () {
                $('#manual_position').removeClass('warning');
                var s = $('#manual_position').val();
                var pos = WorkingAreaHelper.splitStringToTwoValues(s)
                if (pos) {
                    self.control.sendCustomCommand({type: 'command', command: "G0X" + pos[0] + "Y" + pos[1]});
                    $('#manual_position').val('');
                } else {
                    $('#manual_position').addClass('warning');
                }
            };

			$("#manual_position").on('keyup', function (e) {
				if (e.keyCode === 13) {
					self.control.manualPosition();
				}
			});
			$("#manual_position").on('blur', function (e) {
				self.control.manualPosition();
			});

			$("body").on('keydown', function (event) {

				if (!self.settings.feature_keyboardControl()) return;
				if(	event.target.nodeName === "INPUT"
					|| event.target.nodeName === "TEXTAREA"
					|| $('.modal.in').length > 0
				) return;

				var button = undefined;
				var wa_id = $('nav li.active a').attr('href');
				switch (event.which) {
					case 37: // left arrow key:
						// button = $("#control-xdec");
                        if(wa_id === '#workingarea'){
							self.workingArea.moveSelectedDesign(-1,0);
							return;
						}
						break;
					case 38: // up arrow key
						// button = $("#control-yinc");
						if(wa_id === '#workingarea') {
                            self.workingArea.moveSelectedDesign(0, -1);
                            return;
                        }
						break;
					case 39: // right arrow key
						// button = $("#control-xinc");
						if(wa_id === '#workingarea') {
                            self.workingArea.moveSelectedDesign(1, 0);
                            return;
                        }
                        break;
					case 40: // down arrow key
						// button = $("#control-ydec");
                        if(wa_id === '#workingarea'){
							self.workingArea.moveSelectedDesign(0, 1);
							return;
						}
						break;
					case 33: // page up key
					case 87: // w key
						button = $("#control-zinc");
						break;
					case 34: // page down key
					case 83: // s key
						button = $("#control-zdec");
						break;
					case 36: // home key
						button = $("#control-xyhome");
						break;
					case 8: // del key
					case 46: // backspace key
						if(wa_id === '#workingarea'){
							self.workingArea.removeSelectedDesign();
							return;
						}
						break;
					default:
						return;
//						event.preventDefault();
//						return false;
				}
				if (button === undefined) {
					return false;
				} else {
					event.preventDefault();
					button.addClass("active");
					setTimeout(function () {
						button.removeClass("active");
					}, 150);
					button.click();
				}
			});

            // TODO forward to control viewmodel
            self.state.isLocked = ko.observable(true);
//            self.state.isReady = ko.observable(undefined); // not sure why this is injected here. should be already present in octoprints printerstate VM
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
                    return pos.x + ", " + pos.y;
                }
            }, this);
			self.state.printTimeString = ko.computed(function() {
				if (!self.state.printTime())
					return "-";
				return formatDuration(self.state.printTime());
			});

			// self.inject_software_update_channel();
            self.setupFullscreenContols();
        };

        self.onAllBound = function (allViewModels) {
            self._force_reload_on_inconsitent_version();

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

			// terminal stuff
            terminalMaxLines = self.settings.settings.plugins.mrbeam.dev.terminalMaxLines();
            self.terminal.upperLimit(terminalMaxLines*2);
            self.terminal.buffer(terminalMaxLines);

            $("#terminal-output").scroll(function() {
                 self.terminal.checkAutoscroll();
            });
            self.terminal.activeAllFilters();

            // MR_BEAM_OCTOPRINT_PRIVATE_API_ACCESS
            // our implementation here should be used instead of octoprints
            // to fix issues with the laser job time display
            self.state._processProgressData = function(){};
        };

        self.onStartupComplete = function() {
            self.set_Design_lib_defaults();
            self._handleStoredSocketData();
            self.isStartupComplete = true;
            self.removeLoadingOverlay();
        };

        self.onEventMrbPluginVersion = function(payload) {
            if ('version' in payload || 'is_first_run' in payload) {
                self._force_reload_on_inconsitent_version(payload['version'], payload['is_first_run']);
            }
        };

        self.set_Design_lib_defaults = function(){
			self.gcodefiles.setFilter('design');
            self.files.listHelper.removeFilter('model');
            self.files.listHelper.changeSorting('upload');

            $("#design_lib_sort_upload_radio").prop("checked", true);
            $("#design_lib_filter_design_radio").prop("checked", true);
        };

        self.removeLoadingOverlay = function(){
            // firstImageLoaded is based on jQuery.load() which is not reliable and deprecated.
            // Therefore we lift the curtain for unsupported browsers without waiting for the bgr image to be loaded.
            // this might not look so nice but at least it doesn't block functionality and
            // allows the user to see the notification that his browser is not supported.
            if (self.isStartupComplete && (!window.mrbeam.browser.is_supported || self.workingArea.camera.firstImageLoaded)) {
                self.loadingOverlay.removeLoadingOverlay();
            } else {
                setTimeout(self.removeLoadingOverlay, 100);
            }
        };

        /**
         * Reloads the frontend bypassing any cache if backend version of mr beam plugin is different from the frontend version
         * or id the firstRunFlag is different.
         * This happens sometimes after a software update or if the user used a reset stick
         * @private
         * @param backend_version (optional) If no version is given the function reads it from self.settings
         * @param isFirstRun (optional) If no firstRun flag is given the function reads it from self.settings
         */
        self._force_reload_on_inconsitent_version = function(backend_version, isFirstRun){
            backend_version = backend_version || self.settings.settings.plugins.mrbeam._version();
            if (isFirstRun === undefined) {
                isFirstRun = self.settings.settings.plugins.mrbeam.isFirstRun();
            }
            if (backend_version != BEAMOS_VERSION || isFirstRun != CONFIG_FIRST_RUN) {
                console.log("Frontend reload check: RELOAD! (version: frontend=" + BEAMOS_VERSION + ", backend=" + backend_version +
                    ", isFirstRun: frontend=" + CONFIG_FIRST_RUN + ", backend=" + isFirstRun + ")");
                console.log("Reloading frontend...");
                window.location.href = "/?ts=" + Date.now();
            } else {
                console.log("Frontend reload check: OK (version: "+BEAMOS_VERSION + ", isFirstRun: " + CONFIG_FIRST_RUN + ")");
            }
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

                    self.analytics.send_fontend_event('link_click', {link: 'go_fullscreen_menu_item'})
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

        /**
         * Shows branch info in Software Update Settings if branch is not TIER-default
         * Takes data from softwareUpdatePlugin and sneaks branch information into it.
         */
        self.writeBranchesToSwUpdateScreen = function(){
            var software_update_branches = self.settings.settings.plugins.mrbeam.software_update_branches;
            // only if we really have some branch names inject
            if (Object.keys(software_update_branches).length > 0) {
                var allItems = self.softwareUpdate.versions.items();
                var nuItems = []

                for (var i = 0; i < allItems.length; i++) {
                    var plugin_id = allItems[i]['key']
                    var my_conf = jQuery.extend({}, allItems[i]);
                    if (software_update_branches[plugin_id]) {
                        var branch = software_update_branches[plugin_id]();
                        console.log(plugin_id+": "+branch);
                        my_conf['displayVersion'] += ' ('+branch+')';
                    }
                    nuItems.push(my_conf);
                }
                self.softwareUpdate.versions.updateItems(nuItems);
            }
        }


        self.fromCurrentData = function (data) {
            self._fromData(data);
        };

        self.fromHistoryData = function (data) {
            self._fromData(data);
        };

        self._fromData = function (data, noStore, force) {
            if (self.isStartupComplete || force) {
                self._processStateData(data.state);
                self._processWPosData(data.workPosition);
                self._processProgressData(data.progress);
			    self._processJobData(data.job);
            } else if (!noStore){
                self.storedSocketData.push(data);
            }
        };

        self._handleStoredSocketData = function(){
            if (self.storedSocketData.length > 0) {
                console.log("Handling stored socked data: " + self.storedSocketData.length);
                for (var i = 0; i < self.storedSocketData.length; i++) {
                    self._fromData(self.storedSocketData[i], noStore=true, force=true);
                }
                self.storedSocketData = [];
            }
        };

        self._processStateData = function (data) {
				self.state.isLocked(data.flags.locked);
				self.state.isFlashing(data.flags.flashing);
				self.state.isConnecting(data.text === "Connecting" || data.text === "Opening serial port");
		};

        self._processWPosData = function (data) {
            if (data === undefined || data === null || data[0] === null || data[1] === null || isNaN(data[0]) || isNaN(data[1])) {
                self.state.currentPos({x: 0, y: 0});
            } else {
                self.state.currentPos({x: data[0], y: data[1]});
            }
        };

        self.state.isPaused.subscribe(function (newIsPaused) {
            if(newIsPaused) {
                clearInterval(self.printTimeInterval);
            } else {
                self.printTimeInterval = setInterval(function () {
                    self.localPrintTime++;
                    self.state.printTime(self.localPrintTime);
                }, 1000)
            }
        });

        self._processProgressData = function(data) {
            if (data.completion) {
                self.state.progress(data.completion);
            } else {
                self.state.progress(undefined);
            }
            self.state.filepos(data.filepos);
            if(data.printTime !== self.serverPrintTime) {
                self.serverPrintTime = data.printTime;
                self.localPrintTime = data.printTime;
                self.state.printTime(self.localPrintTime);

                clearInterval(self.printTimeInterval);
                self.printTimeInterval = setInterval(function () {
                    self.localPrintTime++;
                    self.state.printTime(self.localPrintTime);
                }, 1000)
            }
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


        // files.js viewmodel extensions
		self.gcodefiles.selectedFiles = ko.observable("0 " + gettext("Files"));
		self.gcodefiles.selectedFilesSize = ko.observable(0);
		self.gcodefiles.selectedFilesTypes = ko.observable("");
		self.gcodefiles.updateSelection = function(data, event){
			event.currentTarget.classList.toggle('selected');
			let items = $('#files .file_list_entry:has(.selection_box.selected)');
			let str = items.length === 1 ? gettext("1 File") : items.length + " " + gettext("Files");
			let totalSelectionSize = 0;
			let types = {};
			for (var i = 0; i < items.length; i++) {
				var elem = items[i];
				let data = ko.dataFor(elem);
				totalSelectionSize += data.size;
				let t;
				if(data.type === 'recentjob'){
					t = gettext('recent job');
				} else {
					t = gettext(_.last(data.typePath));
				}
				types[t] = (types[t] + 1) || 1;
			}
			let typeStr = _.map(types, function(val, key){ return(val + 'x\u00A0' + key); }).join(', '); // \u00A0 is a non breaking space.
			self.gcodefiles.selectedFiles(str);
			self.gcodefiles.selectedFilesTypes(typeStr);
			self.gcodefiles.selectedFilesSize(totalSelectionSize);
			if(items.length > 0){
				$('#bulkActions').slideDown();
			} else {
				$('#bulkActions').slideUp();
			}
		}
		self.gcodefiles.cancelSelection = function(){
			$('#files .file_list_entry .selection_box.selected').removeClass('selected');
			$('#bulkActions').slideUp();
		}
		self.gcodefiles.deleteSelection = function(){
			let items = $('#files .file_list_entry:has(.selection_box.selected)');
			for (var i = 0; i < items.length; i++) {
				var elem = items[i];
				let data = ko.dataFor(elem);
				if(data.type === 'folder'){
					self.gcodefiles.removeFolder(data);
				}else{
					self.gcodefiles.removeFile(data);
				}
			}
			items.remove();
			$('#bulkActions').slideUp();
		}
		
		/**
		 * gcodefiles viewmodel methods for folder support
		 * changeFolder: ƒ (data)
		 * navigateUp: ƒ ()
		 * changeFolderByPath: ƒ (path)
		 * showAddFolderDialog: ƒ ()
		 * addFolder: ƒ ()
		 * removeFolder: ƒ (folder, event)
		 */

		// fetches the right templates according to file type for knockouts foreach loop
        self.gcodefiles.templateFor = function (data) {
            if (data.type === 'folder') {
                return 'files_template_folder';
            } else {
                return "files_template_" + data.typePath.join('_');
            }
        };

        // starts a single GCode file.
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
                title: gettext("Preparation done"),
                text: _.sprintf(gettext("Converted %(stl)s to %(gcode)s, took %(time).2f seconds"), payload),
                type: "success"
            });

            // self.gcodefiles.requestData(undefined, undefined, self.gcodefiles.currentPath());
            self.gcodefiles.requestData({switchToPath: self.gcodefiles.currentPath()});
        };

		// filter function for the file list. Easier to modify than the original listHelper(). listHelper is still used for sorting.
		self.gcodefiles.setFilter = function(filter){
			var elem = $('#designlib');
			// class 'tab-pane' needs to remain there at all times
            elem.removeClass('show_recentjob');
            elem.removeClass('show_machinecode');
            elem.removeClass('show_design');
			if(filter === 'recentjob'){
				elem.addClass('show_recentjob');
			} else if(filter === 'machinecode'){
				elem.addClass('show_machinecode');
			} else {
				elem.addClass('show_design');
			}
		};

        // settings.js viewmodel extensions

        self.settings.saveall = function (e, v, force) {
            if (self.settings.savetimer !== undefined) {
                clearTimeout(self.settings.savetimer);
            }
			// only trigger autosave if there is something changed.
			// the port scanning from the backend otherwise triggers it frequently
			var data = getOnlyChangedData(self.settings.getLocalData(), self.settings.lastReceivedSettings);
			if(force || Object.getOwnPropertyNames(data).length > 0){
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
            self.terminal.tabActive = current === "#mrb_term";
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
//                    self.state.numberOfPasses(parseInt(self.conversion.set_passes()));
//                    self.state._overrideCommand({name: "passes", value: self.state.numberOfPasses()});
                    callback(e);
                }
            };
            showConfirmationDialog(options);
        };
    };


    // view model class, parameters for constructor, container to bind to
    ADDITIONAL_VIEWMODELS.push([MotherViewModel,
        ["loginStateViewModel", "settingsViewModel", "printerStateViewModel", "filesViewModel", "gcodeFilesViewModel",
            "connectionViewModel", "controlViewModel", "terminalViewModel", "workingAreaViewModel",
            "vectorConversionViewModel", "readyToLaserViewModel", "navigationViewModel", "appearanceViewModel",
            "loadingOverlayViewModel", "softwareUpdateViewModel", "analyticsViewModel"],
        [document.getElementById("mrb_state"),
            document.getElementById("mrb_control"),
            document.getElementById("mrb_connection_wrapper"),
            document.getElementById("mrb_state_wrapper"),
            document.getElementById("mrb_state_header"),
            document.getElementById("mrb_term"),
            document.getElementById("focus")
        ]]);

    // third party model binding
    OCTOPRINT_ADDITIONAL_BINDINGS.push(['gcodeFilesViewModel', ["#design_lib_search"]]);
});

