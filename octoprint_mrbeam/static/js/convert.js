/* global ADDITIONAL_VIEWMODELS */

$(function(){

	function VectorConversionViewModel(params) {
		var self = this;

		self.BRIGHTNESS_VALUE_RED   = 0.299;
		self.BRIGHTNESS_VALUE_GREEN = 0.587;
		self.BRIGHTNESS_VALUE_BLUE  = 0.114;

		self.loginState = params[0];
		self.settings = params[1];
		self.state = params[2];
		self.workingArea = params[3];
		self.files = params[4];
		self.profile = params[5];

		self.target = undefined;
		self.file = undefined;
		self.data = undefined;
		self.slicing_progress = ko.observable(5);
		self.slicing_in_progress = ko.observable(false);

		self.dialog_state = ko.observable('color_assignment');

		// expert settings
		self.showHints = ko.observable(false);
		self.showExpertSettings = ko.observable(false);
		self.gcodeFilename = ko.observable();
		self.pierceTime = ko.observable(0);

		// vector settings
		self.show_vector_parameters = ko.observable(true);
		self.maxSpeed = ko.observable(3000);
		self.minSpeed = ko.observable(20);

		self.vectorJobs = ko.observableArray([]);
		self.show_line_color_mappings = ko.observable(false);

		// material menu
		self.material_settings2 = {
			'Anodized Aluminum': {
				name: 'Anodized Aluminum',
				img: 'anodized_aluminum.jpg',
				description: 'Dark anodized aluminum can be engraved. Works on iPhones.',
				hints: 'Requires very precise focus.',
				safety_notes: 'If engraving an iPhone, switch it off. Vibration alarms can ruin the result.',
				laser_type: 'MrBeamII-1.0',
				colors: {
					'000000': {
						engrave: {eng_i:[100,0], eng_f:[30,1000], pierceTime: 0, dithering: false },
						cut: []
					}
				}
			},
			'Balsa Wood': {
				name: 'Balsa Wood',
				img: 'balsa_wood.jpg',
				description: '',
				hints: '',
				safety_notes: 'Take care about ignitions. Never run a job slower than 300 mm/min!',
				laser_type: 'MrBeamII-1.0',
				colors: {
					'd4b26f': {
						engrave: {eng_i:[0,20], eng_f:[2000,350], pierceTime: 0, dithering: false },
						cut: [
							{thicknessMM: 1, cut_i:80, cut_f:700, cut_p:2},
							{thicknessMM: 2, cut_i:100, cut_f:700, cut_p:1},
							{thicknessMM: 3, cut_i:100, cut_f:700, cut_p:2},
							{thicknessMM: 4, cut_i:100, cut_f:600, cut_p:3},
							{thicknessMM: 5, cut_i:100, cut_f:300, cut_p:3}
						]
					}
				}
			},
			'Bamboo': {
				name: 'Bamboo Wood',
				img: 'bamboo.jpg',
				description: '',
				hints: '',
				safety_notes: '',
				laser_type: 'MrBeamII-1.0',
				colors: {
					'9c642b': {
						engrave: {eng_i:[0,100], eng_f:[2000,350], pierceTime: 0, dithering: false },
						cut: []
					}
				}
			},
			'Cardboard, corrugated single wave': {
				name: 'Cardboard, corrugated single wave',
				img: 'cardboard_single_wave.jpg',
				description: 'Ordinary cardboard like most packaging is made of.',
				hints: 'Engraving looks great if just the first layer is lasered away, that the wave is visible underneath.',
				safety_notes: 'Take care about ignitions. Never run a job slower than 180 mm/min!',
				laser_type: 'MrBeamII-1.0',
				colors: {
					'8b624a': {
						engrave: {eng_i:[10,25], eng_f:[2000,850], pierceTime: 0, dithering: false },
						cut: [
							{thicknessMM: 2, cut_i:100, cut_f:500, cut_p:4},
							{thicknessMM: 3, cut_i:100, cut_f:500, cut_p:4},
							{thicknessMM: 4, cut_i:100, cut_f:400, cut_p:4}
							// {thicknessMM: 5, cut_i:100, cut_f:400, cut_p:4}
						]
					}
				}
			},
			'Cardboard, corrugated double wave': {
				name: 'Cardboard, corrugated double wave',
				img: 'cardboard_double_wave.jpg',
				description: 'Ordinary cardboard like strong packaging is made of.',
				hints: 'Engraving looks great if just the first layer is lasered away, that the wave is visible underneath.',
				safety_notes: 'Take care about ignitions. Never run a job slower than 180 mm/min!',
				laser_type: 'MrBeamII-1.0',
				colors: {
					'8b624a': {
						engrave: {eng_i:[10,25], eng_f:[2000,850], pierceTime: 0, dithering: false },
						cut: [
							{thicknessMM: 5, cut_i:100, cut_f:400, cut_p:4}
						]
					}
				}
			},
			'Fabric Cotton': null,
			'Fabric Polyester': null,
			'Finn Cardboard': {
				name: 'Finn Cardboard',
				img: 'finn_cardboard.jpg',
				description: 'Made out of purely wooden fibres, often used for architectural models.',
				hints: '',
				safety_notes: '',
				laser_type: 'MrBeamII-1.0',
				colors: {
					'c7c97c': {
						engrave: {eng_i:[10,25], eng_f:[2000,1300], pierceTime: 0, dithering: false },
						cut: [
							{thicknessMM: 2.5, cut_i:100, cut_f:450, cut_p:3}
						]
					}
				}
			},
			'Felt': {
				name: 'Felt',
				img: 'felt.jpg',
				description: 'Acrylic felt like the one sold in many arts and craft stores.',
				hints: 'Be aware, natural felt is something different.',
				safety_notes: '',
				laser_type: 'MrBeamII-1.0',
				colors: {
					'00b000': {
						name: 'green',
						engrave: null, // not tested yet
						cut: [
							{thicknessMM: 4, cut_i:100, cut_f:300, cut_p:1}
						]
					},
					'4dcaca': {
						name: 'baby blue',
						engrave: null, // not tested yet
						cut: [
							{thicknessMM: 4, cut_i:100, cut_f:100, cut_p:5}
						]
					},
					'181866': {
						name: 'royal blue',
						engrave: null, // not tested yet
						cut: [
							{thicknessMM: 4, cut_i:100, cut_f:350, cut_p:2}
						]
					},
					'c98600': {
						name: 'yellow',
						engrave: null, // not tested yet
						cut: [
							{thicknessMM: 4, cut_i:100, cut_f:350, cut_p:2}
						]
					},
					'eca100': {
						name: 'sunny yellow',
						engrave: null, // not tested yet
						cut: [
							{thicknessMM: 4, cut_i:100, cut_f:300, cut_p:2}
						]
					},
					'550024': {
						name: 'purple',
						engrave: null, // not tested yet
						cut: [
							{thicknessMM: 4, cut_i:100, cut_f:500, cut_p:2}
						]
					},
					'393939': {
						name: 'gray',
						engrave: null, // not tested yet
						cut: [
							{thicknessMM: 4, cut_i:100, cut_f:400, cut_p:2}
						]
					},
					'000000': {
						name: 'black',
						engrave: null, // not tested yet
						cut: [
							{thicknessMM: 4, cut_i:100, cut_f:400, cut_p:2}
						]
					},
					'e03800': {
						name: 'orange',
						engrave: null, // not tested yet
						cut: [
							{thicknessMM: 4, cut_i:100, cut_f:500, cut_p:2}
						]
					},
				}
			},
			'Foam Rubber': {
				name: 'Foam Rubber',
				img: 'foam_rubber.jpg',
				description: 'Consists of poly urethane foam.',
				hints: 'Laser parameters are highly color dependant, bright colors might need pierce time.',
				safety_notes: '',
				laser_type: 'MrBeamII-1.0',
				colors: {
					'0057a8': {
						engrave: null,
						cut: [{thicknessMM: 2, cut_i:100, cut_f:650, cut_p:1},
                              {thicknessMM: 3, cut_i:100, cut_f:600, cut_p:1}]
					},
					'ee6d2c': {
						engrave: null,
						cut: [{thicknessMM: 2, cut_i:75, cut_f:800, cut_p:1}]
					},
					'e6e6e6': {
						engrave: null,
						cut: [{thicknessMM: 2, cut_i:100, cut_f:190, cut_p:1}]
					},
					'000000': {
						engrave: null,
						cut: [{thicknessMM: 2, cut_i:100, cut_f:800, cut_p:1}]
					},
					'41c500': {
						engrave: null,
						cut: [{thicknessMM: 2, cut_i:100, cut_f:800, cut_p:1}]
					},
				}
			},
			'Kraftplex': {
				name: 'Kraftplex',
				img: 'kraftplex.jpg',
				description: '100% natural fibers compressed under high temperature. Strong and bendable like metal.',
				hints: '',
				safety_notes: '',
				laser_type: 'MrBeamII-1.0',
				colors: {
					'795f39': {
						engrave: {eng_i:[0,35], eng_f:[2000,850], pierceTime: 0, dithering: false },
						cut: [
							{thicknessMM: 0.8, cut_i:100, cut_f:300, cut_p:2},
							{thicknessMM: 1.5, cut_i:100, cut_f:150, cut_p:2},
							{thicknessMM: 3,   cut_i:100, cut_f:100, cut_p:4}
						]
					}
				}
			},
			'Latex': null,
			'Paper': {
				name: 'Paper',
				img: 'paper.jpg',
				description: 'Ordinary paper like from an office printer.',
				hints: '',
				safety_notes: 'Very fine structures may be subject of ignition.',
				laser_type: 'MrBeamII-1.0',
				colors: {
					'e7d27f': {
						engrave: null,
						cut: [
							{thicknessMM: 0.1, cut_i:75, cut_f:800, cut_p:1},
							{thicknessMM: 0.2, cut_i:85, cut_f:800, cut_p:2} //  >300g is what we said in the old system
						]
					}
				}
			},
			'Plywood Poplar': {
				name: 'Plywood Poplar',
				img: 'plywood.jpg',
				description: 'Plywood from an ordinary hardware store or arts and craft supply.',
				hints: 'Watch out for dedicated laser plywood - it has better surface quality and only natural glue.',
				safety_notes: 'Very fine structures may be subject of ignition.',
				laser_type: 'MrBeamII-1.0',
				colors: {
					'e7d27f': {
						engrave: {eng_i:[18,35], eng_f:[2000,750], pierceTime: 0, dithering: false },
						cut: [
							{thicknessMM: 3, cut_i:100, cut_f:150, cut_p:3},
							{thicknessMM: 4, cut_i:100, cut_f:120, cut_p:3},
						]
					}
				}
			},
			'Wellboard': {
				name: 'Wellboard',
				img: 'wellboard.jpg',
				description: '100% natural fibers similar to Kraftplex, but wavy.',
				hints: 'Thickness is measured over the whole wave.',
				safety_notes: '',
				laser_type: 'MrBeamII-1.0',
				colors: {
					'e7d27f': {
						engrave: {eng_i:[10,35], eng_f:[2000,850], pierceTime: 0, dithering: false },
						cut: [
							{thicknessMM: 6,  cut_i:100, cut_f:225, cut_p:2},
							{thicknessMM: 10, cut_i:100, cut_f:140, cut_p:3},
						]
					}
				}
			}
		};
		self.engrave_only_thickness = {thicknessMM: -1, cut_i:'', cut_f:'', cut_p: 1};
		self.no_engraving = {eng_i:['',''], eng_f:['',''], pierceTime: 0, dithering: false };

		self.material_colors = ko.observableArray([]);
		self.material_thicknesses = ko.observableArray([]);
		self.selected_material = ko.observable(null);
		self.selected_material_color = ko.observable(null);
		self.selected_material_thickness = ko.observable(null);
		self.material_safety_notes = ko.observable('');
		self.material_hints = ko.observable('');
		self.material_description = ko.observable('');
		self.has_engraving_proposal = ko.observable(false);
		self.has_cutting_proposal = ko.observable(false);
		
//		self._engraving_params_available = function(){
//			var mat = self.selected_material();
//			var col = self.selected_material_color();
//			var th = self.selected_material_thickness();
//			if(mat === null || col === null || th === null){
//				return false;
//			} else {
//				var param_set = self.get_closest_color_params();
//				return param_set.engrave !== null;
//			}
//		};
//		self._cutting_params_available = function(){
//			var mat = self.selected_material();
//			var col = self.selected_material_color();
//			var th = self.selected_material_thickness();
//			if(mat === null || col === null || th === null){
//				return false;
//			} else {
//				var param_set = self.get_closest_thickness_params();
//				return param_set.thicknessMM > 0;
//			}
//		};

		self.expandMaterialSelector = ko.computed(function(){
			return self.selected_material() === null || self.selected_material_color() === null || self.selected_material_thickness() === null;
		});


		self.mm2px = ko.observable(1.37037); // TODO put in user settings
		self.selected_material_name = ko.computed(function(){
			var mat = self.selected_material();
			return mat === null ? '' : mat.name;
		 });
		self.selected_material_img = ko.computed(function(){
			var mat = self.selected_material();
			if(mat !== null)
			return mat === null ? '' : mat.img;
		 });

		self.get_closest_thickness_params = function(){
			var selected = self.selected_material_thickness();
			if(selected === null){ return null; }
			var color_closest = self.get_closest_color_params();
			var available = color_closest.cut;
			if(available.length === 0) {
				return self.engrave_only_thickness;
			} else {
				for (var i = 0; i < available.length; i++) {
					var pset = available[i];
					if(pset.thicknessMM >= selected.thicknessMM){
						return pset;
					}
				}
			}
			return self.engrave_only_thickness;
		};
		
		self.get_closest_color_params = function(){
			var material = self.selected_material();
			var hex = self.selected_material_color();
			if(material !== null && hex !== null){
				var available_colors = Object.keys(material.colors);
				var closest = self._find_closest_color_to(hex, available_colors);
//				console.log("closest color to " + hex, closest);
				return material.colors[closest];
			} else {
				return {engrave: self.no_engraving, cut: []};
			}
		};

		self.thickness_text = function(data){
			if(data.thicknessMM < 0) return "engrave only";
			else return data.thicknessMM+' mm';
		};

		self.thickness_mount_pos = ko.computed(function(){
			var selected = self.selected_material_thickness();
			if(selected !== null){
				var d = selected.thicknessMM;
				if(d < 10) return '1';
				if(d < 20) return '2';
				if(d < 30) return '3';
				return '4';
			} else {
				return null;
			}
		 });

		// Hierarchy: Material Type -> Color -> Thickness (changing higher nodes resets lower ones.)
		// if only one option is available this one is used for the parameter suggestion.
		// Highest node in hierarchy -> resets color.
		self.selected_material.subscribe(function(material){

			if(material !== null){
				// autoselect color if only one available
				var available_colors = Object.keys(material.colors);
				self.material_colors(available_colors);
				if(available_colors.length === 1){
					self.selected_material_color(available_colors[0]);
				} else {
					self.selected_material_color(null);
				}
				self.material_description(material.description);
				self.material_hints(material.hints);
				self.material_safety_notes(material.safety_notes);

			} else {
				self.material_colors([]);
				self.material_thicknesses([]);
				self.selected_material_color(null);
				self.selected_material_thickness(null);
				self.material_description('');
				self.material_hints('');
				self.material_safety_notes('');
			}
		});

		// changes in color reset thickness settings
		self.selected_material_color.subscribe(function(color){
			var material = self.selected_material();

			if(material !== null && color !== null){

				// autoselect thickness if only one available
				var available_thickness = material.colors[color].cut;
				if(material.colors[color].engrave !== null){
					available_thickness = available_thickness.concat(self.engrave_only_thickness);
				}
				self.material_thicknesses(available_thickness);
				self.selected_material_thickness(null);
				if(available_thickness.length === 1){
					self.selected_material_thickness(available_thickness[0]);
					self.dialog_state('color_assignment');
				}
			}
			self.apply_engraving_proposal();
		});
		self.selected_material_thickness.subscribe(function(thickness){
			if(thickness !== null && self.selected_material_color() !== null && self.selected_material !== null){
				self.dialog_state('color_assignment');
				self.apply_vector_proposal();
			}
		});

		self.dialog_state.subscribe(function(new_state){
			self._update_job_summary();
		});

        self.filterQuery = ko.observable('');
		self.filteredMaterials = ko.computed(function(){
			var q = self.filterQuery();
			var out = [];
			for(var materialKey in self.material_settings2){
				var m = self.material_settings2[materialKey];
				if(m !== null){
//					m.name = materialKey; // TODO i18n
					if(m.name.toLowerCase().indexOf(q) >= 0){
						out.push(m);
					}
				}
			}
			return out;
		});


		self.color_key_update = function(){
			var cols = self.workingArea.getUsedColors();
			$('.job_row .used_color:not(#cd_engraving)').addClass('not-used');
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
			$('.job_row .not-used').remove();
		};

		self._getColorIcon = function(color){
			var i = $('<div />',{
				id: 'cd_color_'+color.hex.substr(1),
				style: "background-color: "+color.hex+";",
				draggable: "true",
				class: 'used_color'
			})
			.on({
				dragstart: function(ev){ window.mrbeam.colorDragging.colorDragStart(ev.originalEvent); },
				dragend: function(ev){ window.mrbeam.colorDragging.colorDragEnd(ev.originalEvent); }
			});

			return i;
		};

		self.set_material = function(material, ev){
			if(typeof ev !== 'undefined' && ev.type === 'click' && typeof material === 'object' ){
				var old_material = self.selected_material();
				if(old_material === null){
					self.selected_material(material);
				} else {
					self.selected_material(null);
				}
			} else {
				self.selected_material(null);
			}
			self.dialog_state('material_type');
		};
		self.set_material_color = function(color, ev){
			if(typeof ev !== 'undefined' && ev.type === 'click' ){
				var old = self.selected_material_color();
				if(old === null){
					self.selected_material_color(color);
				} else if(self.material_colors().length > 1){
					self.selected_material_color(null);
				}
			} else {
				self.selected_material_color(null);
			}
			self.dialog_state('material_type');
		};
		self.set_material_thickness = function(thickness, ev){
			if(typeof ev !== 'undefined' && ev.type === 'click' ){
				var old = self.selected_material_thickness();
				if(old === null){
					self.selected_material_thickness(thickness);
					self.dialog_state('color_assignment');
				} else if(self.material_thicknesses().length > 1){
					self.selected_material_thickness(null);
					self.dialog_state('material_type');
				}
			} else {
				self.selected_material_thickness(null);
				self.dialog_state('material_type');
			}
		};

		self.apply_vector_proposal = function(){
			var material = self.selected_material();
			var params = self.get_closest_thickness_params();
			var p = self.engrave_only_thickness;
			if(material !== null && params !== null && params.thicknessMM > 0){
				p = params;
				self.has_cutting_proposal(true);
			} else {
				self.has_cutting_proposal(false);
			}
			var vector_jobs = $('.job_row_vector');
			for (var i = 0; i < vector_jobs.length; i++) {
				var job = vector_jobs[i];
				$(job).find('.param_intensity').val(p.cut_i);
				$(job).find('.param_feedrate').val(p.cut_f);
				$(job).find('.param_passes').val(p.cut_p || 0);
				$(job).find('.param_piercetime').val(p.cut_pierce || 0);
			}
		};
		self.apply_engraving_proposal = function(){
			var material = self.selected_material();
			var param_set = self.get_closest_color_params();
			var p = self.no_engraving;
			var name = '';
			if(material !== null && param_set !== null && param_set.engrave !== null){
				p = param_set.engrave;
				name = material.name;
				self.has_engraving_proposal(true);
			} else {
				self.has_engraving_proposal(false);
				console.warn("No engraving settings available for "+ material);
			}

			var job = $('#engrave_job');
			self.imgIntensityWhite(p.eng_i[0]);
			self.imgIntensityBlack(p.eng_i[1]);
			self.imgFeedrateWhite(p.eng_f[0]);
			self.imgFeedrateBlack(p.eng_f[1]);
			self.imgDithering(p.dithering);
			self.engravingPiercetime(p.eng_pierce || 0);
		};

		self._find_closest_color_to = function(hex, available_colors){
			if(available_colors.length === 1) return available_colors[0];

			var needle = self._parseHexColor(hex);
			var distance;
			var minDistance = Infinity;
			var rgb;
			var value;

			for (var i = 0; i < available_colors.length; ++i) {
				rgb = self._parseHexColor(available_colors[i]);
				distance =
					Math.pow(needle.x - rgb.x, 2) +
					Math.pow(needle.y - rgb.y, 2) +
					Math.pow(needle.z - rgb.z, 2);

				if (distance < minDistance) {
					minDistance = distance;
					value = available_colors[i];
				}
			}
			return value;
		};

		self._parseHexColor = function(hex){
			return rgb_from_hex(hex); // from color_classifier.js
		};

		// image engraving stuff
		// preset values are a good start for wood engraving
		self.images_placed = ko.observable(false);
		self.text_placed = ko.observable(false);
		self.filled_shapes_placed = ko.observable(false);
		self.engrave_outlines = ko.observable(false);

		self.show_image_parameters = ko.computed(function(){
//			return (self.images_placed() || self.text_placed() || self.filled_shapes_placed());
			return true;
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
		self.engravingMaterial = null;

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

		self.get_dialog_state = function(){
			if(self.selected_material() === null){
				return 'material_type';
			} else if (self.selected_material_thickness() === null){
				return 'material_type';
			} else if(self.get_color_assignment_required()){
				return 'color_assignment';
			} else {
				return 'color_assignment';
			}
		};

		self.get_color_assignment_required = function(){
			var vec = self.get_current_multicolor_settings();
			var vectors_present = self.show_vector_parameters();
			var assigned_images = $('#engrave_job .assigned_colors').children().length > 0;
			var rasters_present = self.show_image_parameters();
			return (vectors_present && vec.length === 0) || (rasters_present && !assigned_images);
		};

		// shows conversion dialog and extracts svg first
		self.show_conversion_dialog = function() {
			self.workingArea.abortFreeTransforms();
			self.gcodeFilesToAppend = self.workingArea.getPlacedGcodes();
			self.show_vector_parameters(self.workingArea.hasStrokedVectors());
			self.filled_shapes_placed(self.workingArea.hasFilledVectors());
			self.images_placed(self.workingArea.getPlacedImages().length > 0);
			self.text_placed(self.workingArea.hasTextItems());
			self.color_key_update();

			self._update_job_summary();

			if(self.show_vector_parameters() || self.show_image_parameters()){
				self.dialog_state(self.get_dialog_state());

				var gcodeFile = self.create_gcode_filename(self.workingArea.placedDesigns());
				self.gcodeFilename(gcodeFile);
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
			$('.job_row_vector').each(function(i, job){
				var intensity_user = $(job).find('.param_intensity').val();
				var intensity = intensity_user * self.profile.currentProfileData().laser.intensity_factor() ;
				var feedrate = $(job).find('.param_feedrate').val();
				var piercetime = $(job).find('.param_piercetime').val();
				var material = $(job).find('.param_material').val();
				var passes = $(job).find('.param_passes').val();
				$(job).find('.used_color').each(function(j, col){
					var hex = '#' + $(col).attr('id').substr(-6);
					data.push({
						job: i,
						color: hex,
						intensity: intensity,
                        intensity_user: intensity_user,
						feedrate: feedrate,
						pierce_time: piercetime,
						passes: passes,
                        material: material
					});
				});
			});

			var intensity_black_user = self.imgIntensityBlack();
			var intensity_white_user = self.imgIntensityWhite();
			var speed_black = parseInt(self.imgFeedrateBlack());
			var speed_white = parseInt(self.imgFeedrateWhite());

			// vector icons dragged into engraving.
			$('#colored_line_mapping input').each(function(i, el){
				var hex = '#' +$(el).attr('id').substr(-6);
				var brightness = self._get_brightness(hex);
				var initial_factor = 1 - (brightness / 255);
				var intensity_user = intensity_white_user + initial_factor * (intensity_black_user - intensity_white_user);
				var intensity = Math.round(intensity_user * self.profile.currentProfileData().laser.intensity_factor());
				var feedrate = Math.round(speed_white + initial_factor * (speed_black - speed_white));

				data.push({
					job: "vector_engrave_"+i,
					color: hex,
					intensity: intensity,
					intensity_user: intensity_user,
					feedrate: feedrate,
					pierce_time: self.engravingPiercetime(),
					passes: 1,
					material: self.engravingMaterial
				});
			});

			return data;
		};

		self.get_current_engraving_settings = function () {
			var data = {
				"engrave_outlines" : self.engrave_outlines(),
				"intensity_black_user" : self.imgIntensityBlack(),
				"intensity_black" : self.imgIntensityBlack() * self.profile.currentProfileData().laser.intensity_factor(),
				"intensity_white_user" : self.imgIntensityWhite(),
				"intensity_white" : self.imgIntensityWhite() * self.profile.currentProfileData().laser.intensity_factor(),
				"speed_black" : self.imgFeedrateBlack(),
				"speed_white" : self.imgFeedrateWhite(),
				"contrast" : self.imgContrast(),
				"sharpening" : self.imgSharpening(),
				"dithering" : self.imgDithering(),
				"beam_diameter" : self.beamDiameter(),
				"pierce_time": self.engravingPiercetime(),
                "material": self.engravingMaterial
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
						self._missing_parameter_hint(intensityInput);
						allSet = false;
					}
					if(feedrate === ''){
						self._missing_parameter_hint(feedrateInput);
						allSet = false;
					}
				}
			}
			
			if($('#engrave_job .color_drop_zone').children().length > 0){
				if(self.imgIntensityWhite() === ''){
					self._missing_parameter_hint($('#svgtogcode_img_intensity_white'));
					allSet = false;
				}
				if(self.imgIntensityBlack() === ''){
					self._missing_parameter_hint($('#svgtogcode_img_intensity_black'));
					allSet = false;
				}
				if(self.imgFeedrateWhite() === ''){
					self._missing_parameter_hint($('#svgtogcode_img_feedrate_white'));
					allSet = false;
				}
				if(self.imgFeedrateBlack() === ''){
					self._missing_parameter_hint($('#svgtogcode_img_feedrate_black'));
					allSet = false;
				}
			}
			return allSet;
		};
		
		self._missing_parameter_hint = function(input){
			$(input).addClass('checkInput');
			setTimeout(
				function() { $(input).removeClass('checkInput'); },
				2000
			);
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
		
		self._get_brightness = function(hex){
			var r = parseInt(hex.substr(1,2), 16);
			var g = parseInt(hex.substr(3,2), 16);
			var b = parseInt(hex.substr(5,2), 16);
			return Math.round((r*self.BRIGHTNESS_VALUE_RED + g*self.BRIGHTNESS_VALUE_GREEN + b*self.BRIGHTNESS_VALUE_BLUE));
		};

		self.onStartup = function() {
			self.requestData();
			self.state.conversion = self; // hack! injecting method to avoid circular dependency.
			self.files.conversion = self;
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
			self._update_job_summary();
			var jobs = $('#additional_jobs .job_row_vector');
			for (var idx = 0; idx < jobs.length; idx++) {
				var j = jobs[idx];
				var colors = $(j).find('.used_color');
				if(colors.length === 0){ // remove orphaned job rows
					$(j).remove();
				}
			}
			
			// create adjusters for lines in engrave settings
			var engrave_items = $('#engrave_job .img_drop_zone .used_color');
			var show_line_mappings = false;
			var line_mapping_container = $('#colored_line_mapping');
			line_mapping_container.children().remove();
			for (var i = 0; i < engrave_items.length; i++) {
				var el = engrave_items[i];
				var id = el.id;
				if(id !== 'cd_engraving'){
					show_line_mappings = true;
					var hex = '#' + id.substr(-6);
					var val = 255 - self._get_brightness(hex);
					var icon = '<input id="adjuster_'+id+'" class="precisionslider coloradjuster" type="range" min="0" max="255" style="border-top-color:'+hex+';" value="'+val+'" />';
					line_mapping_container.append(icon);
				}
			}
			self.show_line_color_mappings(show_line_mappings);
		};

		// quick hack
		self._update_job_summary = function(){
			var jobs = self.get_current_multicolor_settings();
			self.vectorJobs(jobs);
		};

	}


    ADDITIONAL_VIEWMODELS.push([VectorConversionViewModel,
		["loginStateViewModel", "settingsViewModel", "printerStateViewModel", "workingAreaViewModel",
            "gcodeFilesViewModel", 'laserCutterProfilesViewModel'],
		document.getElementById("dialog_vector_graphics_conversion")]);

});

window.mrbeam.colorDragging = {

    // Drag functions outside the viewmodel are way less complicated
    colorAllowDrop: function(ev) {
        ev.preventDefault();
        $('.color_drop_zone, .img_drop_zone').addClass('hover');
    },

    colorDragStart: function(ev) {
        $("body").addClass("colorDragInProgress");
        if (ev.target.id === "cd_engraving") {
            $('body').addClass('engravingDrag');
        } else {
            $('body').addClass('vectorDrag');
        }
        ev.dataTransfer.setData("text", ev.target.id);
        ev.dataTransfer.effectAllowed = "move";
    },

    colorDrop: function(ev) {
        ev.preventDefault();
        $('body').removeClass('vectorDrag engravingDrag');
        setTimeout(function () {
            $("body").removeClass("colorDragInProgress");
        }, 200);
        $('.color_drop_zone, .img_drop_zone').removeClass('hover');
        var data = ev.dataTransfer.getData("text");
        var required_class = 'color_drop_zone';
        if (data === 'cd_engraving') {
            required_class = 'img_drop_zone';
        }
        var parent = $(ev.target).parents('.job_row');
        if (parent.length === 1) {
            var drop_target = $(parent[0]).find('.' + required_class);
            if (drop_target.length === 1) {
                // TODO check if parent is allowed drop zone.
                drop_target[0].appendChild(document.getElementById(data));
                ko.dataFor(document.getElementById("dialog_vector_graphics_conversion"))._update_color_assignments();
            }
        }
    },

    colorDropCreateJob: function(ev) {
        ev.preventDefault();
        setTimeout(function () {
            $("body").removeClass("colorDragInProgress");
        }, 200);
        $('.color_drop_zone, .img_drop_zone').removeClass('hover');

		var data = ev.dataTransfer.getData("text");
		if(data !== 'cd_engraving'){
			var newJob = $('#first_job').clone(true);
			newJob.attr('id', '');
			var i = $('.job_row_vector').length + 1;
			$(newJob).find('.job_title').text("Cutting Job " + i);
		
			newJob.find('.used_color').remove();
			newJob.appendTo($('#additional_jobs'));

			var color = document.getElementById(data);
			$(newJob).find('.assigned_colors').append(color);
			ko.dataFor(document.getElementById("dialog_vector_graphics_conversion"))._update_color_assignments();
		}
    },


    colorDragEnd: function(ev) {
        ev.preventDefault();
        $('#drop_overlay').removeClass('in'); // workaround
        setTimeout(function () {
            $("body").removeClass("colorDragInProgress vectorDrag engravingDrag");
        }, 200);
        $('.color_drop_zone, .img_drop_zone').removeClass('hover');
    },

	checkConversionParameters: function(){
		ko.dataFor(document.getElementById("dialog_vector_graphics_conversion"))._allParametersSet();
	}
};
