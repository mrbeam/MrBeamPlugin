$(function(){

	function MotherViewModel(params) {
		var self = this;
		self.loginstate = params[0];
		self.settings = params[1];
		self.state = params[2];
		self.gcodefiles = params[3];
		self.connection = params[4];
		self.control = params[5];
		self.terminal = params[6];
		self.workingarea = params[7];
		
//		self.onBeforeBinding = function(){
//			self.printerstate.isLocked = ko.observable(undefined);
//		};

		
		self.laserPos = function () { console.warn("dummy! TODO implement."); };
//		self.laserPos = ko.computed(function () {
//			var pos = self.printerState.currentPos();
//			if (!pos) {
//				return "(?, ?)";
//			} else {
//				return "(" + pos.x + ", " + pos.y + ")";
//			}
//		}, this);

		self.onStartup = function(){
			self.requestData();
			self.control.showZAxis = ko.computed(function(){
				var has = self.currentProfileData()['zAxis']();
				return has;
			}); // dependency injection
			
				// TODO forward to control viewmodel
		self.state.isLocked = ko.observable(undefined);
		self.state.isReady = ko.observable(undefined);
		self.state.isFlashing = ko.observable(undefined);

		};
		
	}
	
	
	// view model class, parameters for constructor, container to bind to
    ADDITIONAL_VIEWMODELS.push([MotherViewModel,
		["loginStateViewModel", "settingsViewModel", "printerStateViewModel",  "gcodeFilesViewModel",
		"connectionViewModel", "controlViewModel", "terminalViewModel", "workingAreaViewModel"],
		[document.getElementById("mrb_state"), document.getElementById("mrb_control")]]);

		// third party model binding
	//OCTOPRINT_ADDITIONAL_BINDINGS.push(['loginStateViewModel', ["#state_wrapper"]]);
});

