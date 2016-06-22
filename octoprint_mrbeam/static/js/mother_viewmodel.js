$(function(){

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

		self.laserPos = ko.computed(function () {
			if(typeof self.state.currentPos === "function"){
				var pos = self.state.currentPos();
				if (!pos) {
					return "(?, ?)";
				} else {
					return "(" + pos.x + ", " + pos.y + ")";
				}
			}
		}, this);

		self.onStartup = function(){
			// TODO fetch machine profile on start
			//self.requestData(); 
			self.control.showZAxis = ko.computed(function(){
//				var has = self.currentProfileData()['zAxis']();
//				return has;
				return false;
			}); 
			
			self.control.setCoordinateOrigin = function () {
				self.control.sendCustomCommand({type: 'command', command: "G92 X0 Y0"});
			};
			
			self.control.jogDistanceInMM = ko.observable(undefined);
			
			self.control.manualPosition = function(){
						$('#manual_position').removeClass('warning');
				var s = $('#manual_position').val();
				var tmp = s.split(/[^0-9.,-\\+]+/);
				if (tmp.length === 2) {
					var x = parseFloat(tmp[0]);
					var y = parseFloat(tmp[1]);
					if(!isNaN(x) && !isNaN(y)) {
						self.sendCustomCommand({type: 'command', command: "G0X"+x+"Y"+y});
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
			
			self.state.intensityOverride = ko.observable(100);
			self.state.feedrateOverride = ko.observable(100);
			self.state.intensityOverride.extend({ rateLimit: 500 });
			self.state.feedrateOverride.extend({ rateLimit: 500 });
			self.state.numberOfPasses = ko.observable(1);
			self.state.isConnecting = ko.observable(undefined);
		};
		
		self.fromCurrentData = function(data) {
            self._fromData(data);
        };

        self.fromHistoryData = function(data) {
            self._fromData(data);
        };
		
		self._fromData = function (data) {
			self._processStateData(data.state);
//            self._processJobData(data.job);
//            self._processProgressData(data.progress);
//            self._processZData(data.currentZ);
//            self._processBusyFiles(data.busyFiles);
			self._processWPosData(data.workPosition);
		};

		self._processStateData = function (data) {
//            var prevPaused = self.state.isPaused();
//            self.stateString(gettext(data.text));
//            self.isErrorOrClosed(data.flags.closedOrError);
//            self.isOperational(data.flags.operational);
//            self.isPaused(data.flags.paused);
//            self.isPrinting(data.flags.printing);
//            self.isError(data.flags.error);
//            self.isReady(data.flags.ready);
//            self.isSdReady(data.flags.sdReady);
			self.state.isLocked(data.flags.locked);
			self.state.isFlashing(data.flags.flashing);
			self.state.isConnecting(data.text === "Connecting" || data.text === "Opening serial port");

//            if (self.isPaused() != prevPaused) {
//                if (self.isPaused()) {
//                    self.titlePrintButton(self.TITLE_PRINT_BUTTON_PAUSED);
//                    self.titlePauseButton(self.TITLE_PAUSE_BUTTON_PAUSED);
//                } else {
//                    self.titlePrintButton(self.TITLE_PRINT_BUTTON_UNPAUSED);
//                    self.titlePauseButton(self.TITLE_PAUSE_BUTTON_UNPAUSED);
//                }
//            }
		};

		self._processWPosData = function (data) {
			if (data == null) {
				self.state.currentPos({x: 0, y: 0});
			} else {
				self.state.currentPos({x: data[0], y: data[1]});
			}
		};
	}
	
	
	// view model class, parameters for constructor, container to bind to
    ADDITIONAL_VIEWMODELS.push([MotherViewModel,
		["loginStateViewModel", "settingsViewModel", "printerStateViewModel",  "gcodeFilesViewModel",
		"connectionViewModel", "controlViewModel", "terminalViewModel", "workingAreaViewModel", "vectorConversionViewModel"],
		[document.getElementById("mrb_state"), 
			document.getElementById("mrb_control"),
			document.getElementById("mrb_connection_wrapper"),
			document.getElementById("mrb_state_wrapper"),
			document.getElementById("mrb_term"),
			document.getElementById("focus"),
		]]);

		// third party model binding
	//OCTOPRINT_ADDITIONAL_BINDINGS.push(['loginStateViewModel', ["#state_wrapper"]]);
});

