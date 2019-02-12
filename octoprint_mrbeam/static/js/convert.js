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

		// flag to disable this feature.
		self.user_materials_enabled = true;

		// expert settings
		self.showHints = ko.observable(false);
		self.showExpertSettings = ko.observable(false);
		self.gcodeFilename = ko.observable();
		// self.pierceTime = ko.observable(0);

		// vector settings
		self.show_vector_parameters = ko.observable(true);
		self.maxSpeed = ko.observable(3000);
		self.minSpeed = ko.observable(20);

		self.vectorJobs = ko.observableArray([]);
		self.show_line_color_mappings = ko.observable(false);

		self.engraveOnlyForced = false;

		// material menu
		self.material_settings2 = {
			'Anodized Aluminum': {
				name: 'Anodized Aluminum',
				img: 'anodized_aluminum.jpg',
				description: 'Dark anodized aluminum can be engraved. Works on iPhones.',
				hints: 'Requires very precise focus. Anodized aluminum turns brighter through laser engraving. Therefor we suggest to invert photos for engravings.',
				laser_type: 'MrBeamII-1.0',
				colors: {
					'000000': {
						engrave: {eng_i:[0,100], eng_f:[1000, 30], eng_pierce: 0, dithering: false },
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
						engrave: {eng_i:[0,20], eng_f:[2000,350], eng_pierce: 0, dithering: false },
						cut: [
							{thicknessMM: 1, cut_i:80, cut_f:525, cut_p:2},
							{thicknessMM: 2, cut_i:100, cut_f:525, cut_p:1},
							{thicknessMM: 3, cut_i:100, cut_f:525, cut_p:2},
							{thicknessMM: 4, cut_i:100, cut_f:450, cut_p:3},
							{thicknessMM: 5, cut_i:100, cut_f:225, cut_p:3}
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
						engrave: {eng_i:[0,100], eng_f:[2000,260], eng_pierce: 0, dithering: false },
						cut: []
					}
				}
			},
			'Cardboard, corrugated single wave': {
				name: 'Cardboard, single wave',
				img: 'cardboard_single_wave.jpg',
				description: 'Ordinary cardboard like most packaging is made of.',
				hints: 'Engraving looks great if just the first layer is lasered away, that the wave is visible underneath.',
				safety_notes: 'Take care about ignitions. Never run a job slower than 180 mm/min!',
				laser_type: 'MrBeamII-1.0',
				colors: {
					'8b624a': {
						engrave: {eng_i:[10,25], eng_f:[2000,850], eng_pierce: 0, dithering: false },
						cut: [
							{thicknessMM: 2, cut_i:100, cut_f:375, cut_p:4},
							{thicknessMM: 3, cut_i:100, cut_f:375, cut_p:4},
							{thicknessMM: 4, cut_i:100, cut_f:300, cut_p:4}
							// {thicknessMM: 5, cut_i:100, cut_f:300, cut_p:5}
						]
					}
				}
			},
			'Cardboard, corrugated double wave': {
				name: 'Cardboard, double wave',
				img: 'cardboard_double_wave.jpg',
				description: 'Ordinary cardboard like strong packaging is made of.',
				hints: 'Engraving looks great if just the first layer is lasered away, that the wave is visible underneath.',
				safety_notes: 'Take care about ignitions. Never run a job slower than 180 mm/min!',
				laser_type: 'MrBeamII-1.0',
				colors: {
					'8b624a': {
						engrave: {eng_i:[10,25], eng_f:[2000,850], eng_pierce: 0, dithering: false },
						cut: [
							{thicknessMM: 5, cut_i:100, cut_f:300, cut_p:4}
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
						engrave: {eng_i:[10,25], eng_f:[2000,1300], eng_pierce: 0, dithering: false },
						cut: [
							{thicknessMM: 2.5, cut_i:100, cut_f:330, cut_p:3}
						]
					}
				}
			},
			'Felt': { // took settings from IHM fair
				name: 'Felt',
				img: 'felt.jpg',
				description: 'Acrylic felt like the one sold in many arts and craft stores.',
				hints: 'Be aware that natural felt is something else.',
				safety_notes: '',
				laser_type: 'MrBeamII-1.0',
				colors: {
					'EB5A3E': {
						name: 'orange',
						engrave: {eng_i:[0,35], eng_f:[1600,1600], eng_pierce: 0, dithering: false },
						cut: [
							{thicknessMM: 3, cut_i:100, cut_f:550, cut_p:2}
						]
					},
					'F49A39': {
						name: 'yellow',
						engrave: {eng_i:[0,30], eng_f:[1200,1200], eng_pierce: 0, dithering: false },
						cut: [
							{thicknessMM: 3, cut_i:100, cut_f:625, cut_p:2}
						]
					},
					'293365': {
						name: 'blue',
						engrave: {eng_i:[0,35], eng_f:[1600,1600], eng_pierce: 0, dithering: false },
						cut: [
							{thicknessMM: 3, cut_i:100, cut_f:500, cut_p:2}
						]
					},
					'322F33': {
						name: 'black',
						engrave: {eng_i:[0,30], eng_f:[1600,1600], eng_pierce: 0, dithering: false },
						cut: [
							{thicknessMM: 3, cut_i:100, cut_f:400, cut_p:2}
						]
					},
					'54392E': {
						name: 'brown',
						engrave: {eng_i:[0,30], eng_f:[1600,1600], eng_pierce: 0, dithering: false },
						cut: [
							{thicknessMM: 3, cut_i:100, cut_f:500, cut_p:2}
						]
					},
					'A21F25': {
						name: 'dunkelrot',
						engrave: {eng_i:[0,30], eng_f:[1600,1600], eng_pierce: 0, dithering: false },
						cut: [
							{thicknessMM: 3, cut_i:100, cut_f:550, cut_p:2}
						]
					},
					'3E613E': {
						name: 'green',
						engrave: {eng_i:[0,30], eng_f:[1600,1600], eng_pierce: 0, dithering: false },
						cut: [
							{thicknessMM: 3, cut_i:100, cut_f:500, cut_p:2}
						]
					},
					'D91F48': {
						name: 'pink',
						engrave: {eng_i:[0,40], eng_f:[1600,1600], eng_pierce: 0, dithering: false },
						cut: [
							{thicknessMM: 3, cut_i:100, cut_f:600, cut_p:2}
						]
					},
				}
			},
//			'Felt': { // old settings we had before IHM fair
//				name: 'Felt',
//				img: 'felt.jpg',
//				description: 'Acrylic felt like the one sold in many arts and craft stores.',
//				hints: 'Be aware, natural felt is something different.',
//				safety_notes: '',
//				laser_type: 'MrBeamII-1.0',
//				colors: {
//					'00b000': {
//						name: 'green',
//						engrave: null, // not tested yet
//						cut: [
//							{thicknessMM: 4, cut_i:100, cut_f:225, cut_p:1}
//						]
//					},
//					'4dcaca': {
//						name: 'baby blue',
//						engrave: null, // not tested yet
//						cut: [
//							{thicknessMM: 4, cut_i:100, cut_f:100, cut_p:5}
//						]
//					},
//					'181866': {
//						name: 'royal blue',
//						engrave: null, // not tested yet
//						cut: [
//							{thicknessMM: 4, cut_i:100, cut_f:260, cut_p:2}
//						]
//					},
//					'c98600': {
//						name: 'yellow',
//						engrave: null, // not tested yet
//						cut: [
//							{thicknessMM: 4, cut_i:100, cut_f:260, cut_p:2}
//						]
//					},
//					'eca100': {
//						name: 'sunny yellow',
//						engrave: null, // not tested yet
//						cut: [
//							{thicknessMM: 4, cut_i:100, cut_f:225, cut_p:2}
//						]
//					},
//					'550024': {
//						name: 'purple',
//						engrave: null, // not tested yet
//						cut: [
//							{thicknessMM: 4, cut_i:100, cut_f:375, cut_p:2}
//						]
//					},
//					'393939': {
//						name: 'gray',
//						engrave: null, // not tested yet
//						cut: [
//							{thicknessMM: 4, cut_i:100, cut_f:300, cut_p:2}
//						]
//					},
//					'000000': {
//						name: 'black',
//						engrave: null, // not tested yet
//						cut: [
//							{thicknessMM: 4, cut_i:100, cut_f:300, cut_p:2}
//						]
//					},
//					'e03800': {
//						name: 'orange',
//						engrave: null, // not tested yet
//						cut: [
//							{thicknessMM: 4, cut_i:100, cut_f:375, cut_p:2}
//						]
//					},
//				}
//			},
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
						cut: [{thicknessMM: 2, cut_i:100, cut_f:480, cut_p:1},
                              {thicknessMM: 3, cut_i:100, cut_f:450, cut_p:1}]
					},
					'ee6d2c': {
						engrave: null,
						cut: [{thicknessMM: 2, cut_i:75, cut_f:140, cut_p:1}]
					},
					'e6e6e6': {
						engrave: null,
						cut: [{thicknessMM: 2, cut_i:100, cut_f:140, cut_p:1}]
					},
					'000000': {
						engrave: null,
						cut: [{thicknessMM: 2, cut_i:100, cut_f:600, cut_p:1}]
					},
					'41c500': {
						engrave: null,
						cut: [{thicknessMM: 2, cut_i:100, cut_f:600, cut_p:1}]
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
						engrave: {eng_i:[0,35], eng_f:[2000,850], eng_pierce: 0, dithering: false },
						cut: [
							{thicknessMM: 0.8, cut_i:100, cut_f:225, cut_p:2},
							{thicknessMM: 1.5, cut_i:100, cut_f:110, cut_p:2},
							{thicknessMM: 3,   cut_i:100, cut_f:100, cut_p:5}
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
							{thicknessMM: 0.1, cut_i:75, cut_f:600, cut_p:1},
							{thicknessMM: 0.2, cut_i:85, cut_f:600, cut_p:2} //  >300g is what we said in the old system
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
						engrave: {eng_i:[18,35], eng_f:[2000,750], eng_pierce: 0, dithering: false },
						cut: [
							{thicknessMM: 3, cut_i:100, cut_f:110, cut_p:3},
							{thicknessMM: 4, cut_i:100, cut_f:100, cut_p:3},
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
						engrave: {eng_i:[10,35], eng_f:[2000,850], eng_pierce: 0, dithering: false },
						cut: [
							{thicknessMM: 6,  cut_i:100, cut_f:160, cut_p:2},
							{thicknessMM: 10, cut_i:100, cut_f:100, cut_p:3},
						]
					}
				}
			},

//			custom_material: {
//				name: 'Custom',
//				img: 'custom.jpg',
//				description: 'Just a Dummy material',
//				hints: 'Figuring out material settings works best from low to high intensity and fast to slow movement.',
//				safety_notes: 'Experimenting with custom material settings is your responsibility.',
//				laser_type: 'MrBeamII-1.0',
//				colors: {
//					'd4b26f': {
//						engrave: {eng_i:[0,20], eng_f:[2000,350], eng_pierce: 0, dithering: false },
//						cut: [
//							{thicknessMM: 1, cut_i:80, cut_f:700, cut_p:2},
//							{thicknessMM: 2, cut_i:100, cut_f:700, cut_p:1},
//							{thicknessMM: 3, cut_i:100, cut_f:700, cut_p:2},
//							{thicknessMM: 4, cut_i:100, cut_f:600, cut_p:3},
//							{thicknessMM: 5, cut_i:100, cut_f:300, cut_p:3}
//						]
//					}
//				}
//			}
		};
		self.engrave_only_thickness = {thicknessMM: -1, cut_i:'', cut_f:'', cut_p: 1, cut_pierce: 0};
		self.no_engraving = {eng_i:['',''], eng_f:['',''], eng_pierce: 0, dithering: false };

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
		self.custom_materials = ko.observable({});

		self.customized_material = ko.observable(false);
		self.save_custom_material_name = ko.observable("");
		self.save_custom_material_thickness = ko.observable(1);
		self.save_custom_material_color = ko.observable("#000000");


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

        self.load_custom_materials = function(){
			// fill custom materials
			if (self.user_materials_enabled){
			    console.log("Loading custom materials");
                OctoPrint.simpleApiCommand("mrbeam", "custom_materials", {})
                    .done(function(response){
                        self._update_custom_materials(response.custom_materials);
                    })
                    .fail(function(){
                        console.error("Unable to load custom materials.");
                    });
            } else {
                $('#material_burger_menu').hide()
            }
		};

		self.flag_customized_material = function(){
		    if (self.user_materials_enabled){
                var custom_prefix = 'My ';
                var suggested_name = self.selected_material().name;
                if(!suggested_name.startsWith(custom_prefix)){
                    suggested_name = custom_prefix + suggested_name;
                }
                self.save_custom_material_name(suggested_name);
                self.save_custom_material_color('#'+self.selected_material_color());
                var t = self.selected_material_thickness();
                var tmp = t !== null ? t.thicknessMM : 1;
                self.save_custom_material_thickness(tmp);
                self.customized_material(true);
			}
		};

		self.reset_material_settings = function(){
            if (self.user_materials_enabled){
                self.apply_engraving_proposal();
                self.apply_vector_proposal();
                self.customized_material(false);
            }
		};

		self.delete_material = function(m, event){
			$(event.target).parents('li').remove();
			event.preventDefault();
			event.stopPropagation();
			var postData = {
                put: {},
				delete: [m.key]
            };
            OctoPrint.simpleApiCommand("mrbeam", "custom_materials", postData)
                .done(function(response){
					console.log("deleted custom material:");
					// remove from custom materials and deselect
					self._update_custom_materials(response.custom_materials);

					self.selected_material(null);
				})
                .fail(function(){
					console.error("unable to delete custom material:", postData);
				});
		};

		self.save_material_settings = function(){
			var name = self.save_custom_material_name();
			var key = self._replace_non_ascii(name).toLowerCase();
			var thickness = parseFloat(self.save_custom_material_thickness());
			var color = self.save_custom_material_color().substr(1,6);
			var vectors = self.get_current_multicolor_settings();
			var strength = 0;
			var strongest = null;
			for (var i = 0; i < vectors.length; i++) { // heuristics: assuming that the strongest of all vector jobs is the cutting one.
				var v = vectors[i];
				var s = v.intensity_user * v.passes / v.feedrate;
				if(s > strength) strongest = v;
			}
			var cut_setting = null;
			// if thickness is 0, we assume engrave only
			if(strongest !== null && thickness > 0){
				cut_setting = {thicknessMM: thickness,
                    cut_i: parseFloat(strongest.intensity_user),
                    cut_f: parseFloat(strongest.feedrate),
                    cut_p: parseInt(strongest.passes),
                    cut_pierce: parseInt(strongest.pierce_time)};
			} else {
				thickness = -1; // engrave only
			}

			var e = self.get_current_engraving_settings();
			var engrave_setting = {eng_i: [e.intensity_white_user, e.intensity_black_user],
                                    eng_f: [e.speed_white, e.speed_black],
                                    eng_pierce: e.pierce_time,
                                    dithering: e.dithering};

			var new_material;

			if(self.custom_materials()[key]){
				new_material = self.custom_materials()[key];
			}else {

				new_material = {
				name: name,
					img: 'custom.jpg',
					description: 'custom material',
					hints: 'Figuring out material settings works best from low to high intensity and fast to slow movement.',
					safety_notes: 'Experimenting with custom material settings is at your own risk.',
					laser_type: 'MrBeamII-1.0',
					colors: {}
				};
			}

			var tmp = [];
			if(cut_setting !== null){
				tmp.push(cut_setting);
			}
			if(new_material.colors[color]){
				for (var t = 0; t < new_material.colors[color].cut.length; t++) {
					var item = new_material.colors[color].cut[t];
					if(item !== null && item.thicknessMM > 0 && (cut_setting == null || item.thicknessMM !== cut_setting.thicknessMM)) {
						tmp.push(item);
					}
				}
			}
            // sort before we store it.
			tmp.sort(self._thickness_sort_function);
			new_material.colors[color] = {cut: tmp, engrave: engrave_setting};

			var data = {};
			data[key] = new_material;

			// save it locally
			// push it to our backend
            var postData = {
                'put':    data,   // optional
                'delete': []                // optional
            };
            OctoPrint.simpleApiCommand("mrbeam", "custom_materials", postData)
                .done(function(response){
					console.log("simpleApiCall response: ", response);
					// $('#save_material_form.dropdown').dropdown('toggle'); // buggy
					$('#save_material_form').removeClass('open'); // workaround

                    // add to custom materials and select
					self._update_custom_materials(response.custom_materials);
					var fm = self.filteredMaterials();
						for (var i = 0; i < fm.length; i++) {
							var my_material = fm[i];
							if(my_material.name === new_material.name){
								self.selected_material(my_material);
								self.selected_material_color(color);
								self._set_available_material_thicknesses(my_material, color);
								self.selected_material_thickness(cut_setting);
								self.reset_material_settings();
								break;
							}
						}
				})
                .fail(function(){
					console.error("Unable to save custom material: ", postData);
					new PNotify({
                        title: "Error while saving settings!",
                        text: "Unable to save your custom material settings at the moment.<br/>Check connection to Mr Beam II and try again.",
                        type: "error",
                        hide: true
                    });
				});
		};

		self._update_custom_materials = function(list){
			var tmp = {};
			for(var k in list) {
				var cm = list[k];
				tmp[k] = cm;
			}
			console.log("Loaded custom material settings: ", Object.keys(tmp).length);
			self.custom_materials(tmp);
		};

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
                self._set_available_material_thicknesses(material, color);

				self.selected_material_thickness(null);
				if(self.material_thicknesses().length === 1){
					if(self.material_thicknesses()[0] !== null){
						self.selected_material_thickness(self.material_thicknesses()[0]);
						self.dialog_state('color_assignment');
					} else {
						self.selected_material_thickness(null);
					}
				}
			}
			self.apply_engraving_proposal();
		});
		self.selected_material_thickness.subscribe(function(thickness){
			if(thickness !== null && self.selected_material_color() !== null && self.selected_material() !== null){
				self.dialog_state('color_assignment');
				self.apply_vector_proposal();
			}
		});

		self._set_available_material_thicknesses = function(material, color) {
		    if(material !== null && color !== null){
				// autoselect thickness if only one available
				var available_thickness = material.colors[color].cut;
				if(material.colors[color].engrave !== null){
					available_thickness = available_thickness.concat(self.engrave_only_thickness);
				}
				available_thickness.sort(self._thickness_sort_function);

                console.log("available_thickness: ", available_thickness);
				self.material_thicknesses(available_thickness);
			}
        };

		self.dialog_state.subscribe(function(new_state){
			self._update_job_summary();
		});

        self.filterQuery = ko.observable('');
		self.filteredMaterials = ko.computed(function(){
			// TODO this method is called 3 times on startup: 1 time should be enough.
			var q = self.filterQuery();
			var out = [];
			// List custom materials first
			// filter custom materials
			var customs = self.custom_materials();
			for(var materialKey in customs){
				var m = customs[materialKey];
				if(m !== null){
//					m.name = materialKey; // TODO i18n
					if(m.name.toLowerCase().indexOf(q) >= 0){
						m.key = materialKey;
						m.custom = true;
						out.push(m);
					}
				}

			}
			// filter predefined materials
			for(var materialKey in self.material_settings2){
				var m = self.material_settings2[materialKey];
				if(m !== null){
					m.key = materialKey;
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
				var selection = $('#cd_color_'+c.hex.substr(1)); // crashes on color definitions like 'rgb(0,0,0)'
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
			if( $('#material_type').hasClass('manage') ){
				$('#materials_manage_done').addClass('flash');
				setTimeout(function(){
					$('#materials_manage_done').removeClass('flash');
				}, 300);
			} else {
				if(typeof ev !== 'undefined' && ev.type === 'click' && typeof material === 'object' ){
					var old_material = self.selected_material();
					if(old_material === null){
						self.selected_material(material);
					} else {
						self.selected_material(null);
						self.reset_material_settings();
					}
				} else {
					self.selected_material(null);
				}
				self.dialog_state('material_type');
			}
		};
		self.set_material_color = function(color, ev){
			if(typeof ev !== 'undefined' && ev.type === 'click' ){
				var old = self.selected_material_color();
				if(old === null){
					self.selected_material_color(color);
				} else if(self.material_colors().length > 1){
					self.selected_material_color(null);
					self.reset_material_settings();
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
					self.reset_material_settings();
				}
			} else {
				self.selected_material_thickness(null);
				self.dialog_state('material_type');
			}
		};

        /**
         * Used by knockout / jinja to determine of two cut-objects are equal
         * @returns {boolean|*}
         */
        self.isThicknessObjEqual = function(a,b) {
		    var result = null;
		    if (a == b ) {
		        result = true;
            } else if (!a || !b) {
		        result = false;
            } else {
		        result = a.thicknessMM == b.thicknessMM;
            }
		    return result;
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
			if(material !== null && param_set !== null && param_set.engrave !== null){
				p = param_set.engrave;
				self.has_engraving_proposal(true);
			} else {
				self.has_engraving_proposal(false);
				console.warn("No engraving settings available for "+ material);
			}

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
				if(self._isValidVectorSetting(intensity_user, feedrate, passes, piercetime)){
					$(job).find('.used_color').each(function(j, col){
						var hex = '#' + $(col).attr('id').substr(-6);
						data.push({
							// job: i,
							color: hex,
							intensity: intensity,
							intensity_user: intensity_user,
							feedrate: feedrate,
							pierce_time: piercetime,
							passes: passes,
							material: material
						});
					});
				} else {
					console.log("Skipping vector job ("+1+"), invalid parameters.");
				}
			});

			var intensity_black_user = self.imgIntensityBlack();
			var intensity_white_user = self.imgIntensityWhite();
			var speed_black = parseInt(self.imgFeedrateBlack());
			var speed_white = parseInt(self.imgFeedrateWhite());

			// vector icons dragged into engraving.
			$('#colored_line_mapping input').each(function(i, el){
				var colorkey = $(el).attr('id').substr(-6);
				var hex = '#' + colorkey;
				var slider_id = '#adjuster_cd_color_' + colorkey;
				var brightness = $(slider_id).val();
				var initial_factor = brightness / 255;
				var intensity_user = intensity_white_user + initial_factor * (intensity_black_user - intensity_white_user);
				var intensity = Math.round(intensity_user * self.profile.currentProfileData().laser.intensity_factor());
				var feedrate = Math.round(speed_white + initial_factor * (speed_black - speed_white));

				if(self._isValidVectorSetting(intensity_user, feedrate, 1, self.engravingPiercetime())){
					data.push({
						// job: "vector_engrave_"+i,
						color: hex,
						intensity: intensity,
						intensity_user: intensity_user,
						feedrate: feedrate,
						pierce_time: self.engravingPiercetime(),
						passes: 1,
						material: self.engravingMaterial
					});
				} else {
					console.log("Skipping line engrave job ("+hex+"), invalid parameters.");
				}
			});

			return data;
		};

		self._isValidVectorSetting = function(intensity, feedrate, passes, pierce_time){
			if(intensity === '' || intensity > 100 || intensity < 0) return false;
			if(feedrate === '' || feedrate > self.maxSpeed() || feedrate < self.minSpeed()) return false;
			if(passes === '' || passes <= 0) return false;
			if(pierce_time === '' || pierce_time < 0) return false;
			return true;
		};

		self.get_current_engraving_settings = function () {
			var data = {
				// "engrave_outlines" : self.engrave_outlines(),
				"intensity_black_user" : parseInt(self.imgIntensityBlack()),
				"intensity_black" : self.imgIntensityBlack() * self.profile.currentProfileData().laser.intensity_factor(),
				"intensity_white_user" : parseInt(self.imgIntensityWhite()),
				"intensity_white" : self.imgIntensityWhite() * self.profile.currentProfileData().laser.intensity_factor(),
				"speed_black" : parseInt(self.imgFeedrateBlack()),
				"speed_white" : parseInt(self.imgFeedrateWhite()),
				"contrast" : self.imgContrast(),
				"sharpening" : self.imgSharpening(),
				"dithering" : self.imgDithering(),
				"beam_diameter" : parseFloat(self.beamDiameter()),
				"pierce_time": parseInt(self.engravingPiercetime()),
				"engraving_mode": $('#svgtogcode_img_engraving_mode > .btn.active').attr('value'),
                "line_distance": $('#svgtogcode_img_line_dist').val()
			};
			return data;
		};

		self.get_current_material_settings = function () {
			var data = {
				"material_name": self.selected_material_name(),
				"color": self.selected_material_color(),
				"thickness_mm": self.selected_material_thickness()['thicknessMM'],
                "material_key": self.selected_material()['key']
			};
			return data;
		};

		self.get_design_files_info = function () {
		    /**
             * Get information about the design files that are going to be lasered.
             * @return {Object} The information about the design files.
             */
		    let data = [];
		    let placedDesigns = self.workingArea.placedDesigns();
            for (let i = 0; i < placedDesigns.length; i++) {
                let currentDesign = placedDesigns[i];

                let dim_x = $('#' + currentDesign.id).find('.horizontal').val();
                let dim_y = $('#' + currentDesign.id).find('.vertical').val();

                let typePath = currentDesign.typePath;
                let format = typePath[typePath.length - 1];

                let sub_format;
                if (format === "image") {
                    let file_name = $('#' + currentDesign.id).find('.title').text();
                    sub_format = file_name.split('.').pop(-1).toLowerCase();
                }

                let size = currentDesign.size;

                data.push({
                    dim_x: dim_x,
                    dim_y: dim_y,
                    format: format,
                    sub_format: sub_format,
                    size: size
                });
            }
			return data;
        };

		self.is_advanced_settings_checked = function () {
            const advancedSettingsCb = $('#parameter_assignment_show_advanced_settings_cb');
            let isChecked = advancedSettingsCb.is(':checked')
            return isChecked
        }

		self.enableConvertButton = ko.computed(function() {
			if (self.slicing_in_progress() 
					|| self.workingArea.placedDesigns().length === 0
					|| self.selected_material() == null
					|| self.selected_material_color() == null
					|| self.selected_material_thickness() == null
				) {
				return false;
			} else {
				return true;
			}
		});


		self._allJobsSkipped = function(){
		    /**
             * Check if all the jobs (engraving+cutting) were set to be skipped.
             * @return {boolean} Indicator of all jobs having been moved to the "Skip" area.
             */
		    let allSkipped;

		    // Check if there is a job to be skipped
            if ($('#no_job .color_drop_zone').children().length > 0) {
                allSkipped = true;

                //Check if there is also an engraving or cutting job
                if ($('#engrave_job .color_drop_zone').children(':visible').length > 0) {
                    allSkipped = false;
                } else {
                    let vector_jobs = $('.job_row_vector');
                    for (let i = 0; i < vector_jobs.length; i++) {
                        const vjob = vector_jobs[i];
                        const colorDrops = $(vjob).find('.color_drop_zone');

                        if (colorDrops.children().length > 0) {
                            allSkipped = false;
                        }
                    }
                }
            } else {
                allSkipped = false;
            }

            return allSkipped
        };

		self._validJobForMaterial = function() {
            /**
             * Check if the selected designs can be engraved/cut in the selected material.
             * @return {boolean} The validity of the designs for the material.
             */
		    let validCut = false;
		    let validEng = false;
		    let vector_jobs = $('.job_row_vector');
			for (let i = 0; i < vector_jobs.length; i++) {
				const vjob = vector_jobs[i];

				const colorDrops = $(vjob).find('.color_drop_zone');
				// If there is a cutting job and a cutting proposal --> valid
				if (self.has_cutting_proposal() && colorDrops.children().length > 0) {
				    validCut = true;
				}
            }
			// If there is an engraving job and an engraving proposal --> valid
			if (self.has_engraving_proposal() && $('#engrave_job .color_drop_zone').children(':visible').length > 0) {
			    validEng = true;
            }

			let validJob = validCut || validEng;

            return validJob
        };

		self.moveJobsToEngravingEngraveModeSelected = function(thickness) {
            /**
             * Move all cutting jobs to engraving when the user selects "Engrave only"
             * @param thickness The object with the user selected thickness
             */
            if (thickness.thicknessMM === -1) {
                self.forceEngraveOnly();
            } else {
                if (self.engraveOnlyForced) {
                    self.undoForceEngraveOnly();
                }
            }

        };

		self.moveJobsToEngravingColorDefaultOption = function(color) {
            /**
             * Move all cutting jobs to engraving when the selected color in a material does not have cutting parameters
             * @param color The object with the user selected color
             */
            if (!self.engraveOnlyForced) {
                let hasCut = false;
                let material = self.selected_material();

                if (color in material .colors && material.colors[color].cut.length > 0) {
                    hasCut = true;
                }

                if (!hasCut) {
                    self.forceEngraveOnly();
                }
            } else {
                self.undoForceEngraveOnly();
            }
        };

        self.moveJobsToEngravingDefaultOption = function(material) {
            /**
             * Move all cutting jobs to engraving when the material does not have cutting parameters
             * @param material The object with the user selected material
             */
            if (!self.engraveOnlyForced) {
                let colors = material.colors;
                let hasCut = false;

                for (let i = 0; i < Object.keys(colors).length; i++) {
                    let color = Object.keys(colors)[i];
                    if (colors[color].cut.length > 0) {
                        hasCut = true;
                    }
                }

                if (!hasCut) {
                    self.forceEngraveOnly();
                }
            } else {
                self.undoForceEngraveOnly();
            }
        };

		self.forceEngraveOnly = function() {
		    /**
             * Move all the jobs from cutting to engraving
             */
		    console.log('Force engrave only');
		    self.engraveOnlyForced = true;

            let vector_jobs = $('.job_row_vector');
            for (let i = 0; i < vector_jobs.length; i++) {
                let vjob = vector_jobs[i];
                let colorDrops = $(vjob).find('.color_drop_zone');

                let jobs = colorDrops.children();
                let numJobs = jobs.length;
                for (let j = 0; j < numJobs; j++) {
                    let cuttingJob = jobs[j];
                    let moveCut = ($(cuttingJob)).detach();
                    ($('#engrave_job > .span3 > .color_drop_zone')).append(moveCut);
                    console.log('Cutting job: ' + cuttingJob.id);
                }
            }

            ko.dataFor(document.getElementById("dialog_vector_graphics_conversion"))._update_color_assignments();
        };

		self.undoForceEngraveOnly = function() {
		    /**
             * Move all the jobs from engraving to cutting (except '#cd_engraving')
             */
		    console.log('Undo force engrave only');
            self.engraveOnlyForced = false;

		    let engraving_jobs = $('#engrave_job .color_drop_zone').children(':visible');

		    let numJobs = engraving_jobs.length;
            for (let j = 0; j < numJobs; j++) {
                let engravingJob = engraving_jobs[j];
                if (engravingJob.id !== 'cd_engraving') {
                    let moveEng = ($(engravingJob)).detach();
                    ($('#first_job > .span3 > .color_drop_zone')).append(moveEng);
                }
            }

            ko.dataFor(document.getElementById("dialog_vector_graphics_conversion"))._update_color_assignments();
        };

		self._allParametersSet = function(){
			var allSet = true;
			var vector_jobs = $('.job_row_vector');
			for (var i = 0; i < vector_jobs.length; i++) {
				var vjob = vector_jobs[i];

				var colorDrops = $(vjob).find('.color_drop_zone');
				if (self.has_cutting_proposal() && colorDrops.children().length > 0){
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

			if(self.has_engraving_proposal() && $('#engrave_job .color_drop_zone').children().length > 0){
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
			if(self.gcodeFilesToAppend.length === 1 && self.svg === undefined) {
                self.files.startGcodeWithSafetyWarning(self.gcodeFilesToAppend[0]);
            } else if (self._allJobsSkipped()) {
			    const message = "There is nothing to laser, all jobs are set to be skipped.";

			    $('#empty_job_support_link').hide();
			    $('#empty_job_modal').find('.modal-body p').text(message);
                $('#empty_job_modal').modal('show');

            } else if (!self._validJobForMaterial()) {
			    let valid;
			    if (self.has_cutting_proposal()) {
			        valid = "engraved";
                } else {
			        valid = "cut";
                }
			    let designType;
			    if (self.workingArea.hasTextItems()) {
			        designType = 'Quick Text'
                } else {
			        designType = 'selected design';
			        $('#empty_job_support_link').hide();
                }

                const message = "Sorry but the " + designType + " can only be " + valid +
                    ", which is not supported for this material.";

			    $('#empty_job_support_link').show();
			    $('#empty_job_modal').find('.modal-body p').text(message);
                $('#empty_job_modal').modal('show');
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
						var advancedSettings = self.is_advanced_settings_checked();
						var colorStr = '<!--COLOR_PARAMS_START' +JSON.stringify(multicolor_data) + 'COLOR_PARAMS_END-->';
						var material = self.get_current_material_settings();
						var design_files = self.get_design_files_info();
						var data = {
							command: "convert",
							engrave: self.do_engrave(),
							vector : multicolor_data,
							raster : engraving_data,
							slicer: "svgtogcode",
							gcode: gcodeFilename,
                            material: material,
                            design_files: design_files,
                            advanced_settings: advancedSettings
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
						var json = JSON.stringify(data);
						var length = json.length;
						console.log("Conversion: " + length + " bytes have to be converted.");
						$.ajax({
							url: "plugin/mrbeam/convert",
							type: "POST",
							dataType: "json",
							contentType: "application/json; charset=UTF-8",
							data: json,
							success: function (response) {
								console.log("Conversion started.", response);
							},
							error: function ( jqXHR, textStatus, errorThrown) {
								console.error("Conversion failed with status " + jqXHR.status, textStatus, errorThrown);
								if(length > 10000000){
									console.error("JSON size " + length + "Bytes may be over the request maximum.");
								}
								self.slicing_in_progress(false);
								new PNotify({
								    title: gettext("Conversion failed"),
									text: gettext("Unable to start the conversion in the backend. Content length was " + length + " bytes."),
									type: "error",
									tag: "conversion_error",
									hide: false
								});
							}
						});

					});
				} else {
					console.log('Conversion parameter missing');
					new PNotify({
                        title: gettext("Parameter missing"),
                        text: gettext("Unable to start conversion because a parameter is missing."),
                        type: "warn",
                        hide: true
                    });
				}
			}
		};

		self.do_engrave = function(){
			const assigned_images = $('#engrave_job .assigned_colors').children().length;
			return (assigned_images > 0 && self.show_image_parameters() && self.has_engraving_proposal());
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

		self._replace_non_ascii = function(str){
			let only_ascii = str.replace(/[\u{0080}-\u{FFFF}]/gu, "*").trim(); // remove spaces,non-Ascii chars
			return only_ascii;
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

            $('[data-toggle="tooltip"]').tooltip({
                html:true
            });
		};

		self.onUserLoggedIn = function(user){
			self.load_custom_materials();
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

			if ('reason' in payload && typeof payload['reason'] === 'string' && payload['reason'].startsWith('OutOfSpaceException')) {
			    var html = "<ul>";
			    html += "<lh>To free up some disk space you may want to perform one or all of the following suggestions:</lh>";
			    html += "<li>Delete CGODE files: Go to design library and click 'Only show GCode files' on the left. Here you can delete files from the according context menu.</li>";
			    html += "<li>Delete design files: Go to design library and click 'Only show design files' on the left. Here you can delete files from the according context menu.</li>";
			    html += "<li>Delete log files: Go to Settings -> logs and delete old log files per click on the trash bin icon.</li>";
			    html += "</ul>";
			    html += 'Find more details <a href="https://mr-beam.freshdesk.com/en/support/solutions/articles/43000068441-free-up-disk-space" target="_blank">online</a>.';
                new PNotify({title: gettext("Get more free disk space"), text: html, type: "info", hide: false});
			}
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
            var classFlag = 'removeme';
			var show_line_mappings = false;
			var engrave_items = $('#engrave_job .img_drop_zone .used_color');
			var line_mapping_container = $('#colored_line_mapping');
			line_mapping_container.children().addClass(classFlag);
			for (var i = 0; i < engrave_items.length; i++) {
				var el = engrave_items[i];
				var id = el.id;
				if(id !== 'cd_engraving'){
					show_line_mappings = true;
					var hex = '#' + id.substr(-6);
					var slider_id = "adjuster_"+id;
					if ($('#'+slider_id).length > 0) {
					    // slider element exists, just leave it as it is
					    $('#'+slider_id).removeClass(classFlag);
                    } else {
					    // create slider element
                        var val = 255 - self._get_brightness(hex);
                        var icon = '<input id="'+slider_id+'" class="precisionslider coloradjuster" type="range" min="0" max="255" style="border-top-color:'+hex+';" value="'+val+'" />';
                        line_mapping_container.append(icon);
                    }
				}
			}
			// remove all slider still flagged
            $('#colored_line_mapping >.'+classFlag).remove();
			self.show_line_color_mappings(show_line_mappings);
		};

		// quick hack
		self._update_job_summary = function(){
			var jobs = self.get_current_multicolor_settings();
			self.vectorJobs(jobs);
		};

		self._thickness_sort_function = function(a,b){
		    t_a = a.thicknessMM < 0 ? 99999 : a.thicknessMM;
		    t_b = b.thicknessMM < 0 ? 99999 : b.thicknessMM;
            return t_a - t_b;
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
			var newJob = $('#first_job').clone(); //clone(true) --> https://github.com/twbs/bootstrap/issues/18326
			newJob.attr('id', '');
			var i = $('.job_row_vector').length + 1;
			$(newJob).find('.job_title').text("Cutting Job " + i);

			newJob.find('.used_color').remove();
			newJob.appendTo($('#additional_jobs'));

			var color = document.getElementById(data);
			$(newJob).find('.assigned_colors').append(color);
			ko.dataFor(document.getElementById("dialog_vector_graphics_conversion"))._update_color_assignments();
		}

        $('[data-toggle="tooltip"]').tooltip({
            html:true
        });

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
