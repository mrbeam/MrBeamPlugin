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
		self.workingarea = params[7];
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

