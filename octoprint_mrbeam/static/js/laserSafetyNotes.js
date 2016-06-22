$(function() {
    
	function LaserSafetyNotesViewModel(params) {
		var self = this;

		self.settings = params[0];
		self.s = ko.observable(self.settings.settings);
		
		self.agreed_to_safety_notes = ko.computed(function(){
//			console.log(self.s());
//			if(self.s && self.s().plugins)
//					return self.s.plugins.laser_safety_notes;
			return false;
		});

		self.onStartup = function(){
			$('#laser_safety_overlay').modal("show");
//			console.log("settings", self.settings.settings);
		};
		
		self.agree = function(){
			$('#laser_safety_overlay').modal("hide");
		}
	}

	
    // view model class, identifier, parameters for constructor, container to bind to
    ADDITIONAL_VIEWMODELS.push([LaserSafetyNotesViewModel,
		["settingsViewModel"], 
		document.getElementById("laser_safety_overlay")]);
	
});
