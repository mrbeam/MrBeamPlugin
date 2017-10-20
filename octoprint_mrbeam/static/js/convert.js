$(function(){

	function VectorConversionViewModel(params) {
		var self = this;

		self.loginState = params[0];
		self.settings = params[1];
		self.state = params[2];
		self.workingArea = params[3];
		self.files = params[4];

		self.target = undefined;
		self.file = undefined;
		self.data = undefined;
		self.slicing_progress = ko.observable(5);
		self.slicing_in_progress = ko.observable(false);

		self.title = ko.observable(undefined);

		// expert settings
		self.showHints = ko.observable(false);
		self.showExpertSettings = ko.observable(false);
		self.gcodeFilename = ko.observable();
		self.pierceTime = ko.observable(0);

		// vector settings
		self.show_vector_parameters = ko.observable(true);
		self.maxSpeed = ko.observable(3000);
		self.minSpeed = ko.observable(20);


		// material menu
		//TODO make not hardcoded
		// TODO: should be a structure like this:

//		material = {
//			name: 'Kraftplex',
//			color: 'default',
//			engrave: {intensity: 300, feedrate: 500, pierceTime: 0, comment: '', rating: -1, rating_amount: 0}, // do we need passes here ?
//			cut: [
//				{thicknessMM:.8, intensity: 1000, feedrate: 120, pierceTime: 0, passes:1, comment: 'single pass, ugly edges', rating: -1, rating_amount: 0},
//				{thicknessMM:1.5, intensity: 1000, feedrate: 80, pierceTime: 0, passes:1, comment: 'single pass, ugly edges', rating: -1, rating_amount: 0},
//				{thicknessMM:1.5, intensity: 1000, feedrate: 240, pierceTime: 0, passes:3, comment: '3 faster passes, nice edges', rating: -1, rating_amount: 0},
//			],
//			description: 'natural MDF like material from Kraftplex.com',
//			hints: '',
//			safety_notes: 'super fine structures are subject to ignition!'
//			laser_type: 'MrBeamII-1.0'
//		}

		self.materials_settings = {
			'default':{cut_i:0, cut_f:0, cut_p:1, eng_i:[0,0], eng_f:[0,0]},
//			'material_name thickness':{cut_i:0, cut_f:0, cut_p:0, eng_i:[0,0], eng_f:[0,0]},
			// new copper embedded laser
			'Anodized Aluminum':{cut_i:0, cut_f:2000, cut_p:1, eng_i:[100,1], eng_f:[30,1000]}, // engrave only
			'Balsa 1mm':{cut_i:70, cut_f:600, cut_p:1, eng_i:[0,0], eng_f:[0,0]}, // min speed 300, max intensity 70 !!! ignition warning
			'Balsa 2mm':{cut_i:100, cut_f:600, cut_p:1, eng_i:[0,0], eng_f:[0,0]}, // min speed 300 !!! ignition warning
			'Balsa 3mm':{cut_i:100, cut_f:800, cut_p:2, eng_i:[0,0], eng_f:[0,0]}, // min speed 300 !!! ignition warning
			'Balsa 4mm':{cut_i:100, cut_f:600, cut_p:3, eng_i:[0,0], eng_f:[0,0]}, // min speed 500 !!! ignition warning
			'Balsa 5mm':{cut_i:100, cut_f:300, cut_p:3, eng_i:[0,0], eng_f:[0,0]}, // min speed 300 !!! ignition warning
			'Bamboo':{cut_i:0, cut_f:2000, cut_p:1, eng_i:[20,100], eng_f:[2000,350]}, // engrave only
			'Cardboard corrugated, single wave 2mm':{cut_i:100, cut_f:500, cut_p:2, eng_i:[10,25], eng_f:[2000,850]}, // warning, not slower than 180
			'Cardboard corrugated, single wave 3mm':{cut_i:100, cut_f:400, cut_p:2, eng_i:[10,25], eng_f:[2000,850]}, // warning, not slower than 180
			'Cardboard corrugated, single wave 4mm':{cut_i:100, cut_f:400, cut_p:3, eng_i:[10,25], eng_f:[2000,850]}, // warning, not slower than 180
			'Cardboard corrugated, double wave 5mm':{cut_i:100, cut_f:400, cut_p:3, eng_i:[10,25], eng_f:[2000,850]}, // warning, not slower than 180
			'Finn Cardboard 2.5mm':{cut_i:100, cut_f:200, cut_p:2, eng_i:[0,0], eng_f:[0,0]},
//			'Felt 2mm':{cut_i:100, cut_f:200, cut_p:2, eng_i:[10,35], eng_f:[2000,850]},
//			'Felt 3mm':{cut_i:100, cut_f:200, cut_p:2, eng_i:[10,35], eng_f:[2000,850]},
			'Felt 4mm green':{cut_i:100, cut_f:300, cut_p:1, eng_i:[0,0], eng_f:[0,0]},
//			'Felt 4mm grass':{cut_i:100, cut_f:300, cut_p:1, eng_i:[10,35], eng_f:[2000,850]},
			'Felt 4mm baby blue':{cut_i:100, cut_f:100, cut_p:5, eng_i:[0,0], eng_f:[0,0]},
			'Felt 4mm royal blue':{cut_i:100, cut_f:350, cut_p:2, eng_i:[0,0], eng_f:[0,0]},
			'Felt 4mm yellow':{cut_i:100, cut_f:350, cut_p:2, eng_i:[0,0], eng_f:[0,0]},
			'Felt 4mm purple':{cut_i:100, cut_f:500, cut_p:2, eng_i:[0,0], eng_f:[0,0]},
			'Felt 4mm gray':{cut_i:100, cut_f:400, cut_p:2, eng_i:[0,0], eng_f:[0,0]},
			'Felt 4mm black':{cut_i:100, cut_f:400, cut_p:2, eng_i:[0,0], eng_f:[0,0]},
			'Felt 4mm orange':{cut_i:100, cut_f:500, cut_p:2, eng_i:[0,0], eng_f:[0,0]},
			'Foam Rubber 2mm blue':{cut_i:100, cut_f:600, cut_p:1, eng_i:[0,0], eng_f:[0,0]},
			'Foam Rubber 2mm orange':{cut_i:75, cut_f:800, cut_p:1, eng_i:[0,0], eng_f:[0,0]},
			'Foam Rubber 2mm white':{cut_i:100, cut_f:190, cut_p:1, eng_i:[0,0], eng_f:[0,0]},
			'Foam Rubber 2mm black':{cut_i:100, cut_f:800, cut_p:1, eng_i:[0,0], eng_f:[0,0]},
			'Foam Rubber 3mm green':{cut_i:100, cut_f:600, cut_p:1, eng_i:[0,0], eng_f:[0,0]},
			'Foam Rubber 3mm blue':{cut_i:100, cut_f:600, cut_p:1, eng_i:[0,0], eng_f:[0,0]},
			'Kraftplex 0.8mm':{cut_i:100, cut_f:350, cut_p:2, eng_i:[10,35], eng_f:[2000,850]},
			'Kraftplex 1.5mm':{cut_i:100, cut_f:175, cut_p:2, eng_i:[10,35], eng_f:[2000,850]},
//			'Kraftplex 3mm':{cut_i:100, cut_f:200, cut_p:2, eng_i:[10,35], eng_f:[2000,850]},
			'Paper':{cut_i:75, cut_f:800, cut_p:1, eng_i:[0,0], eng_f:[0,0]},
			'Plywood 3mm':{cut_i:100, cut_f:150, cut_p:3, eng_i:[18,35], eng_f:[2000,750]},
			'Plywood 4mm':{cut_i:100, cut_f:120, cut_p:3, eng_i:[18,35], eng_f:[2000,750]},
			'Wellboard 6mm':{cut_i:100, cut_f:225, cut_p:2, eng_i:[10,35], eng_f:[2000,850]},
			'Wellboard 10mm':{cut_i:100, cut_f:140, cut_p:3, eng_i:[10,35], eng_f:[2000,850]},
			// 'Wellboard rect':{cut_i:100, cut_f:200, cut_p:3, eng_i:[10,35], eng_f:[2000,850]},
			// old laser
//			'Acrylic':[1000,80,0,350,4500,850, 1],
//			'Foam Rubber':{cut_i:625, cut_f:400, cut_p:1, eng_i:[0,200], eng_f:[3000,1000]},
//			'Felt engrave':{cut_i:300, cut_f:1000, cut_p:1, eng_i:[0,300], eng_f:[2000,1000]},
//			'Felt cut':{cut_i:1000, cut_f:1000, cut_p:1, eng_i:[0,300], eng_f:[2000,1000]},
//			'Jeans Fabric':[1000,500,0,200,3000,500, 1], // 2 passes todo check engraving
//			'Grey cardboard':[1000,500,0,300,3000,750, 1], // 2-3 passes
//			'Cardboard':[1000,300,0,300,3000,750, 3], // 2-3 passes
//			'Kraftplex engrave':{cut_i:400, cut_f:850, cut_p:1, eng_i:[0,500], eng_f:[3000,850]},
//			'Kraftplex cut':{cut_i:1000, cut_f:80, cut_p:2, eng_i:[0,500], eng_f:[3000,850]}, //1-2 pass
//			'Wood engrave':{cut_i:350, cut_f:850, cut_p:1, eng_i:[0,350], eng_f:[3000,850]},
//			'Wood cut':{cut_i:1000, cut_f:250, cut_p:2, eng_i:[0,350], eng_f:[3000,850]},
//			'Balsa cut':{cut_i:700, cut_f:500, cut_p:2, eng_i:[0,350], eng_f:[3000,850]} //2 passes
		};


        var material_keys_cut = [];
		for(var materialKey in self.materials_settings){
		    if (self.materials_settings[materialKey]
                && self.materials_settings[materialKey].cut_i > 0
                && self.materials_settings[materialKey].cut_f > 0
                && self.materials_settings[materialKey].cut_p > 0) {
			    material_keys_cut.push(materialKey);
            }
		}

        var material_keys_eng = [];
		for(var materialKey in self.materials_settings){
            if (self.materials_settings[materialKey]
                && self.materials_settings[materialKey].eng_i[0] > 0
                && self.materials_settings[materialKey].eng_i[1] > 0
                && self.materials_settings[materialKey].eng_f[0] > 0
                && self.materials_settings[materialKey].eng_f[1] > 0) {
			    material_keys_eng.push(materialKey);
            }
		}

		self.material_menu_cut = ko.observableArray(material_keys_cut);
		self.material_menu_eng = ko.observableArray(material_keys_eng);
		self.selected_material = ko.observable();
		self.old_material = 'default';

		// color settings
//		self.old_color = '';
//		self.selected_color = ko.observable();

		self.color_key_update = function(){
			var cols = self.workingArea.getUsedColors();
			$('.job_row_vector .used_color').addClass('not-used');
			for (var idx = 0; idx < cols.length; idx++) {
				var c = cols[idx];
				var selection = $('#cd_color_'+c.hex.substr(1));
				var exists = selection.length > 0;
				if(! exists){
					var drop_zone = $('#first_job .color_drop_zone');
					var i = self._getColorIcon(c);
					drop_zone.append(i);
				} else {
					selection.removeClass('not-used');
				}
			}
			$('.job_row_vector .not-used').remove();
		};

		self._getColorIcon = function(color){
			var i = $('<div />',{
				id: 'cd_color_'+color.hex.substr(1),
				style: "background-color: "+color.hex+";",
				draggable: "true",
				class: 'used_color'
			})
			.on({
				dragstart: function(ev){ colorDragStart(ev.originalEvent); },
				dragend: function(ev){ colorDragEnd(ev.originalEvent); }
			});

			return i;
		};

		self.set_material = function(material, ev){
			if(typeof ev !== 'undefined'){
				var param_set = self.materials_settings[material];
				var p = $(ev.target).parents('.job_row_vector');
				$(p).find('.job_title').html(material);
				$(p).find('.param_intensity').val(param_set.cut_i);
				$(p).find('.param_feedrate').val(param_set.cut_f);
				$(p).find('.param_passes').val(param_set.cut_p || 0);
				$(p).find('.param_piercetime').val(param_set.cut_pierce || 0);
			}
		};

		self.set_material_engraving = function(material, ev){
			if(typeof ev !== 'undefined'){
				var param_set = self.materials_settings[material];
				var p = $('#engrave_job');
				$(p).find('.job_title').html("Engrave " + material);

				self.imgIntensityWhite(param_set.eng_i[0]);
				self.imgIntensityBlack(param_set.eng_i[1]);
				self.imgFeedrateWhite(param_set.eng_f[0]);
				self.imgFeedrateBlack(param_set.eng_f[1]);
				//self.imgDithering();
				self.engravingPiercetime(param_set.eng_pierce || 0);
			}
		};

		// image engraving stuff
		// preset values are a good start for wood engraving
		self.images_placed = ko.observable(false);
		self.text_placed = ko.observable(false);
		self.filled_shapes_placed = ko.observable(false);
		self.engrave_outlines = ko.observable(false);

		self.show_image_parameters = ko.computed(function(){
			return (self.images_placed() || self.text_placed() || self.filled_shapes_placed());
		});
		self.imgIntensityWhite = ko.observable(0);
		self.imgIntensityBlack = ko.observable(50);
		self.imgFeedrateWhite = ko.observable(1500);
		self.imgFeedrateBlack = ko.observable(250);
		self.imgDithering = ko.observable(false);
		self.imgSharpening = ko.observable(1);
		self.imgContrast = ko.observable(1);
		self.beamDiameter = ko.observable(0.15);
		self.engravingPiercetime = ko.observable(0);

		self.sharpeningMax = 25;
		self.contrastMax = 2;

		// preprocessing preview ... returns opacity 0.0 - 1.0
		self.sharpenedPreview = ko.computed(function(){
			if(self.imgDithering()) return 0;
			else {
				var sharpeningPercents = (self.imgSharpening() - 1)/(self.sharpeningMax - 1);
				var contrastPercents = (self.imgContrast() - 1)/(self.contrastMax - 1);
				return sharpeningPercents - contrastPercents/2;
			}
		}, self);
		self.contrastPreview = ko.computed(function(){
			if(self.imgDithering()) return 0;
			else {
				var sharpeningPercents = (self.imgSharpening() - 1)/(self.sharpeningMax - 1);
				var contrastPercents = (self.imgContrast() - 1)/(self.contrastMax - 1);
				return contrastPercents - sharpeningPercents/2;
			}
		}, self);


		self.maxSpeed.subscribe(function(val){
			self._configureFeedrateSlider();
		});

		// shows conversion dialog and extracts svg first
		self.show_conversion_dialog = function() {
			self.workingArea.abortFreeTransforms();
			self.gcodeFilesToAppend = self.workingArea.getPlacedGcodes();
			self.show_vector_parameters(self.workingArea.getPlacedSvgs().length > 0);
			self.filled_shapes_placed(self.workingArea.hasFilledVectors());
			self.images_placed(self.workingArea.getPlacedImages().length > 0);
			self.text_placed(self.workingArea.hasTextItems());
			self.color_key_update();

			if(self.show_vector_parameters() || self.show_image_parameters()){

				var gcodeFile = self.create_gcode_filename(self.workingArea.placedDesigns());
				self.gcodeFilename(gcodeFile);

				self.title(gettext("Converting"));
				$("#dialog_vector_graphics_conversion").modal("show"); // calls self.convert() afterwards
			} else if(self.gcodeFilesToAppend.length > 0){
				// just gcodes were placed. Start lasering right away.
				self.convert();
			} else {
				console.warn('Nothing to laser.');
			}
		};

		self.create_gcode_filename = function(placedDesigns){
			if(placedDesigns.length > 0){
				var filemap = {};
				for(var idx in placedDesigns){
					var design = placedDesigns[idx];
					var end = design.name.lastIndexOf('.');
					if(end < 0){
					    end = design.name.length;
                    }
					var name = design.name.substring(0, end);
					if(filemap[name] !== undefined) filemap[name] += 1;
					else filemap[name] = 1;
				}
				var mostPlaced;
				var placed = 0;
				for(var name in filemap){
					if(filemap[name] > placed){
						mostPlaced = name;
						placed = filemap[name];
					}
				}
				var uniqueDesigns = Object.keys(filemap).length;
				var gcode_name = mostPlaced;
				if(placed > 1) gcode_name += "." + placed + "x";
				if(uniqueDesigns > 1){
					gcode_name += "_"+(uniqueDesigns-1)+"more";
				}

				return gcode_name;
			} else {
				console.error("no designs placed.");
				return;
			}
		};


		self.get_current_multicolor_settings = function () {
			var data = [];
			$('.job_row_vector').each(function(i, pass){
				var intensity = $(pass).find('.param_intensity').val() * 10 ;
				var feedrate = $(pass).find('.param_feedrate').val();
				var piercetime = $(pass).find('.param_piercetime').val();
				var passes = $(pass).find('.param_passes').val();
				$(pass).find('.used_color').each(function(j, col){
					var hex = '#' + $(col).attr('id').substr(-6);
					data.push({
						job: i,
						color: hex,
						intensity: intensity,
						feedrate: feedrate,
						pierce_time: piercetime,
						passes: passes
					});
				});
			});
			return data;
		};

		self.get_current_engraving_settings = function () {
			var data = {
				"engrave_outlines" : self.engrave_outlines(),
				"intensity_black" : self.imgIntensityBlack() * 10,
				"intensity_white" : self.imgIntensityWhite() * 10,
				"speed_black" : self.imgFeedrateBlack(),
				"speed_white" : self.imgFeedrateWhite(),
				"contrast" : self.imgContrast(),
				"sharpening" : self.imgSharpening(),
				"dithering" : self.imgDithering(),
				"beam_diameter" : self.beamDiameter(),
				"pierce_time": self.engravingPiercetime()
			};
			return data;
		};



		self.enableConvertButton = ko.computed(function() {
			if (self.slicing_in_progress() || self.workingArea.placedDesigns().length === 0 ) {
				return false;
			} else {
				return true;
			}
		});

		self._allParametersSet = function(){
			var allSet = true;
			var vector_jobs = $('.job_row_vector');
			for (var i = 0; i < vector_jobs.length; i++) {
				var vjob = vector_jobs[i];

				var colorDrops = $(vjob).find('.color_drop_zone');
				if (colorDrops.children().length > 0){
					var intensityInput = $(vjob).find('.param_intensity');
					var feedrateInput = $(vjob).find('.param_feedrate');
					var intensity = intensityInput.val();
					var feedrate = feedrateInput.val();
					if(intensity === ''){
						intensityInput.addClass('checkInput');
						setTimeout(
							function() { intensityInput.removeClass('checkInput'); },
							2000
						);
						allSet = false;
					}
					if(feedrate === ''){
						feedrateInput.addClass('checkInput');
						setTimeout(
							function() { feedrateInput.removeClass('checkInput'); },
							2000
						);
						allSet = false;
					}
				}
			}
			return allSet;
		};

		self.requestData = function() {
			$.ajax({
				url: API_BASEURL + "slicing",
				type: "GET",
				dataType: "json",
				success: self.fromResponse
			});
		};

		self.fromResponse = function(data) {
			self.data = data;
		};

		self.convert = function() {
			if(self.gcodeFilesToAppend.length === 1 && self.svg === undefined){
				self.files.startGcodeWithSafetyWarning(self.gcodeFilesToAppend[0]);
			} else {
				if(self._allParametersSet()){
					//self.update_colorSettings();
					self.slicing_in_progress(true);
					var pixPerMM = 1/self.beamDiameter();
//					snap.select('#userContent').embed_gc(); // hack
					self.workingArea.getCompositionSVG(self.do_engrave(), pixPerMM, self.engrave_outlines(), function(composition){
						self.svg = composition;
						var filename = self.gcodeFilename();
						var gcodeFilename = self._sanitize(filename) + '.gco';

						var multicolor_data = self.get_current_multicolor_settings();
						var engraving_data = self.get_current_engraving_settings();
						var colorStr = '<!--COLOR_PARAMS_START' +JSON.stringify(multicolor_data) + 'COLOR_PARAMS_END-->';
						var data = {
							command: "convert",
							engrave: self.do_engrave(),
							vector : multicolor_data,
							raster : engraving_data,
							slicer: "svgtogcode",
							gcode: gcodeFilename
						};

						if(self.svg !== undefined){
							// TODO place comment within initial <svg > tag.
							data.svg = colorStr +"\n"+ self.svg;
						} else {
							data.svg = colorStr +"\n"+ '<svg height="0" version="1.1" width="0" xmlns="http://www.w3.org/2000/svg"><defs/></svg>';
						}
						if(self.gcodeFilesToAppend !== undefined){
							data.gcodeFilesToAppend = self.gcodeFilesToAppend;
						}

						$.ajax({
							url: "plugin/mrbeam/convert",
							type: "POST",
							dataType: "json",
							contentType: "application/json; charset=UTF-8",
							data: JSON.stringify(data)
						});

					});
				} else {
					console.log('params missing');
				}
			}
		};

		self.do_engrave = function(){
			const assigned_images = $('#engrave_job .assigned_colors').children().length;
			return (assigned_images > 0 && self.show_image_parameters());
		};

		self._sanitize = function(name) {
		    let no_special_chars = name.replace(/[^a-zA-Z0-9\-_.() ]/g, "").replace(/ /g, "_"); // remove spaces,non-Ascii chars
            const pattern = /[a-zA-Z0-9_\-()]$/g; //check if last character is a valid one
            const is_valid = pattern.test(no_special_chars);
            if(!is_valid || no_special_chars.length <= 1){
                const time_stamp = Date.now();
                no_special_chars = 'mb'+no_special_chars+time_stamp;
            }
            return no_special_chars;
		};

		self.onStartup = function() {
			self.requestData();
			self.state.conversion = self; // hack! injecting method to avoid circular dependency.
			self.files.conversion = self;
//			self._configureIntensitySlider();
//			self._configureFeedrateSlider();
			self._configureImgSliders();

            $("#dialog_vector_graphics_conversion").on('hidden', function(){
                self.slicing_in_progress(false);
                self.slicing_progress(5);
            });
		};

		self.onSlicingProgress = function(slicer, model_path, machinecode_path, progress){
			self.slicing_progress(progress);
		};

		self.onEventSlicingStarted = function(payload){
			self.slicing_in_progress(true);
		};

		self.onEventSlicingDone = function(payload){
		    self.slicing_progress(100);
            // let's wait for onEventFileSelected() to remove the convert dialog and got to the next step
		};

		// This indicates that the slicing is really done.
		// called several times once slicing is done. we react only to the first call
		self.onEventFileSelected = function(payload){
            if (self.slicing_in_progress()) {
                self.gcodeFilename(undefined);
                self.svg = undefined;
                $("#dialog_vector_graphics_conversion").modal("hide");
            }
        };

		self.cancel_conversion = function(){
			if(self.slicing_in_progress()){
				// TODO cancel slicing at the backend properly
				var filename = self.gcodeFilename() + '.gco';
				var gcodeFilename = self._sanitize(filename);

				var data = {
						command: "cancel",
						gcode: gcodeFilename
					};
				$.ajax({
						url: "plugin/mrbeam/cancel",
						type: "POST",
						dataType: "json",
						contentType: "application/json; charset=UTF-8",
						data: JSON.stringify(data)
					});
			}else{
				$("#dialog_vector_graphics_conversion").modal("hide");
			}
		};

		self.onEventSlicingCancelled = function(payload){
			self.gcodeFilename(undefined);
			self.svg = undefined;
			self.slicing_in_progress(false);
			self.slicing_progress(5);
			$("#dialog_vector_graphics_conversion").modal("hide");
			//console.log("onSlicingCancelled" , payload);
		};
		self.onEventSlicingFailed = function(payload){
			self.slicing_in_progress(false);
			//console.log("onSlicingFailed" , payload);
		};

		self._calcRealSpeed = function(sliderVal){
			return Math.round(self.minSpeed() + sliderVal/100 * (self.maxSpeed() - self.minSpeed()));
		};

		self._configureImgSliders = function() {
			var el1 = $("#svgtogcode_contrast_slider");
			if(el1.length > 0){
				self.contrastSlider = el1.slider({
					step: .1,
					min: 1,
					max: self.contrastMax,
					value: 1,
					tooltip: 'hide'
				}).on("slide", function(ev){
					self.imgContrast(ev.value);
				});
			}

			var el2 = $("#svgtogcode_sharpening_slider");
			if(el2.length > 0){
				self.sharpeningSlider = el2.slider({
					step: 1,
					min: 1,
					max: self.sharpeningMax,
					value: 1,
					class: 'img_slider',
					tooltip: 'hide'
				}).on("slide", function(ev){
					self.imgSharpening(ev.value);
				});
			}
		};

		self.showExpertSettings.subscribe(function(){
			$('#dialog_vector_graphics_conversion').trigger('resize');
		});

		self._update_color_assignments = function(){
			var jobs = $('#additional_jobs .job_row_vector');
			for (var idx = 0; idx < jobs.length; idx++) {
				var j = jobs[idx];
				var colors = $(j).find('.used_color');
				if(colors.length === 0){
					$(j).remove();
				}
			}
		};

	}


    ADDITIONAL_VIEWMODELS.push([VectorConversionViewModel,
		["loginStateViewModel", "settingsViewModel", "printerStateViewModel", "workingAreaViewModel", "gcodeFilesViewModel"],
		document.getElementById("dialog_vector_graphics_conversion")]);

});


// Drag functions outside the viewmodel are way less complicated
function colorAllowDrop(ev) {
    ev.preventDefault();
	$('.color_drop_zone, .img_drop_zone').addClass('hover');
}

function colorDragStart(ev) {
	$("body").addClass("colorDragInProgress");
	if(ev.target.id === "cd_engraving"){
		$('body').addClass('engravingDrag');
	} else {
		$('body').addClass('vectorDrag');
	}
	ev.dataTransfer.setData("text", ev.target.id);
	ev.dataTransfer.effectAllowed = "move";
}

function colorDrop(ev) {
    ev.preventDefault();
	$('body').removeClass('vectorDrag engravingDrag');
	setTimeout(function(){$("body").removeClass("colorDragInProgress");}, 200);
	$('.color_drop_zone, .img_drop_zone').removeClass('hover');
    var data = ev.dataTransfer.getData("text");
	var required_class = 'color_drop_zone';
	if(data === 'cd_engraving'){
		required_class = 'img_drop_zone';
	}
	var parent = $(ev.target).parents('.job_row');
	if (parent.length === 1) {
		var drop_target = $(parent[0]).find('.'+required_class);
		if (drop_target.length === 1) {
			// TODO check if parent is allowed drop zone.
			drop_target[0].appendChild(document.getElementById(data));
			ko.dataFor(document.getElementById("dialog_vector_graphics_conversion"))._update_color_assignments();
		}
	}
}

function colorDropCreateJob(ev) {
    ev.preventDefault();
	setTimeout(function(){$("body").removeClass("colorDragInProgress");}, 200);
	$('.color_drop_zone, .img_drop_zone').removeClass('hover');

	var newJob = $('#first_job').clone(true);
	newJob.attr('id','');
	newJob.find('.used_color').remove();
	newJob.appendTo($('#additional_jobs'));

    var data = ev.dataTransfer.getData("text");
    var color = document.getElementById(data);
	$(newJob).find('.assigned_colors').append(color);
	ko.dataFor(document.getElementById("dialog_vector_graphics_conversion"))._update_color_assignments();
}


function colorDragEnd(ev){
    ev.preventDefault();
	$('#drop_overlay').removeClass('in'); // workaround
	setTimeout(function(){$("body").removeClass("colorDragInProgress vectorDrag engravingDrag");}, 200);
	$('.color_drop_zone, .img_drop_zone').removeClass('hover');
}
