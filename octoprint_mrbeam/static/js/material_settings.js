/* global ADDITIONAL_VIEWMODELS */

$(function () {

    function MaterialSettingsViewModel(params) {
        let self = this;
        window.mrbeam.viewModels['materialSettingsViewModel'] = self;

        self.material_settings = {



            
        ///// EDIT MATERIAL SETTINGS BELOW THIS LINE ////////

            'Anodized Aluminum': {
                name: gettext("Anodized Aluminum"),
                img: 'anodized_aluminum.jpg',
                description: gettext("Dark anodized aluminum can be engraved. Works on iPhones."),
                hints: gettext("Requires very precise focus. Anodized aluminum turns brighter through laser engraving. Therefore we suggest to invert photos for engravings."),
                laser_type: 'MrBeamII-1.0',
                colors: {
                    '000000': {
                        engrave: {eng_i: [0, 100], eng_f: [1000, 30], eng_pierce: 0, dithering: false},
                        cut: []
                    }
                }
            },
            'Balsa Wood': {
                name: gettext("Balsa Wood"),
                img: 'balsa_wood.jpg',
                description: '',
                hints: '',
                safety_notes: gettext("Take care about ignitions. Never run a job slower than 300 mm/min!"),
                laser_type: 'MrBeamII-1.0',
                colors: {
                    'd4b26f': {
                        engrave: {eng_i: [0, 20], eng_f: [2000, 350], eng_pierce: 0, dithering: false},
                        cut: [
                            {thicknessMM: 1, cut_i: 80, cut_f: 525, cut_p: 2},
                            {thicknessMM: 2, cut_i: 100, cut_f: 525, cut_p: 1},
                            {thicknessMM: 3, cut_i: 100, cut_f: 525, cut_p: 2},
                            {thicknessMM: 4, cut_i: 100, cut_f: 450, cut_p: 3},
                            {thicknessMM: 5, cut_i: 100, cut_f: 225, cut_p: 3}
                        ]
                    }
                }
            },
            'Bamboo': {
                name: gettext("Bamboo Wood"),
                img: 'bamboo.jpg',
                description: '',
                hints: '',
                safety_notes: '',
                laser_type: 'MrBeamII-1.0',
                colors: {
                    '9c642b': {
                        engrave: {eng_i: [0, 100], eng_f: [2000, 260], eng_pierce: 0, dithering: false},
                        cut: []
                    }
                }
            },
            'Cardboard, corrugated single wave': {
                name: gettext("Cardboard, single wave"),
                img: 'cardboard_single_wave.jpg',
                description: gettext("Ordinary cardboard like most packaging is made of."),
                hints: gettext("Engraving looks great if just the first layer is lasered away, that the wave is visible underneath."),
                safety_notes: gettext("Take care about ignitions. Never run a job slower than 180 mm/min!"),
                laser_type: 'MrBeamII-1.0',
                colors: {
                    '8b624a': {
                        engrave: {eng_i: [10, 25], eng_f: [2000, 850], eng_pierce: 0, dithering: false},
                        cut: [
                            {thicknessMM: 2, cut_i: 100, cut_f: 375, cut_p: 4},
                            {thicknessMM: 3, cut_i: 100, cut_f: 375, cut_p: 4},
                            {thicknessMM: 4, cut_i: 100, cut_f: 300, cut_p: 4}
                            // {thicknessMM: 5, cut_i:100, cut_f:300, cut_p:5}
                        ]
                    }
                }
            },
            'Cardboard, corrugated double wave': {
                name: gettext("Cardboard, double wave"),
                img: 'cardboard_double_wave.jpg',
                description: gettext("Ordinary cardboard like strong packaging is made of."),
                hints: gettext("Engraving looks great if just the first layer is lasered away, that the wave is visible underneath."),
                safety_notes: gettext("Take care about ignitions. Never run a job slower than 180 mm/min!"),
                laser_type: 'MrBeamII-1.0',
                colors: {
                    '8b624a': {
                        engrave: {eng_i: [10, 25], eng_f: [2000, 850], eng_pierce: 0, dithering: false},
                        cut: [
                            {thicknessMM: 5, cut_i: 100, cut_f: 300, cut_p: 4}
                        ]
                    }
                }
            },
            'Fabric Cotton': null,
            'Fabric Polyester': null,
            'Finn Cardboard': {
                name: gettext("Finn Cardboard"),
                img: 'finn_cardboard.jpg',
                description: gettext("Made out of purely wooden fibres, often used for architectural models."),
                hints: '',
                safety_notes: '',
                laser_type: 'MrBeamII-1.0',
                colors: {
                    'c7c97c': {
                        engrave: {eng_i: [10, 25], eng_f: [2000, 1300], eng_pierce: 0, dithering: false},
                        cut: [
                            {thicknessMM: 2.5, cut_i: 100, cut_f: 330, cut_p: 3}
                        ]
                    }
                }
            },
            'Felt': { // took settings from IHM fair
                name: gettext("Felt"),
                img: 'felt.jpg',
                description: gettext("Acrylic felt like the one sold in many arts and craft stores."),
                hints: gettext("Be aware that natural felt is something else."),
                safety_notes: '',
                laser_type: 'MrBeamII-1.0',
                colors: {
                    'EB5A3E': {
                        name: 'orange',
                        engrave: {eng_i: [0, 35], eng_f: [1600, 1600], eng_pierce: 0, dithering: false},
                        cut: [
                            {thicknessMM: 3, cut_i: 100, cut_f: 550, cut_p: 2}
                        ]
                    },
                    'F49A39': {
                        name: 'yellow',
                        engrave: {eng_i: [0, 30], eng_f: [1200, 1200], eng_pierce: 0, dithering: false},
                        cut: [
                            {thicknessMM: 3, cut_i: 100, cut_f: 625, cut_p: 2}
                        ]
                    },
                    '293365': {
                        name: 'blue',
                        engrave: {eng_i: [0, 35], eng_f: [1600, 1600], eng_pierce: 0, dithering: false},
                        cut: [
                            {thicknessMM: 3, cut_i: 100, cut_f: 500, cut_p: 2}
                        ]
                    },
                    '322F33': {
                        name: 'black',
                        engrave: {eng_i: [0, 30], eng_f: [1600, 1600], eng_pierce: 0, dithering: false},
                        cut: [
                            {thicknessMM: 3, cut_i: 100, cut_f: 400, cut_p: 2}
                        ]
                    },
                    '54392E': {
                        name: 'brown',
                        engrave: {eng_i: [0, 30], eng_f: [1600, 1600], eng_pierce: 0, dithering: false},
                        cut: [
                            {thicknessMM: 3, cut_i: 100, cut_f: 500, cut_p: 2}
                        ]
                    },
                    'A21F25': {
                        name: 'dunkelrot',
                        engrave: {eng_i: [0, 30], eng_f: [1600, 1600], eng_pierce: 0, dithering: false},
                        cut: [
                            {thicknessMM: 3, cut_i: 100, cut_f: 550, cut_p: 2}
                        ]
                    },
                    '3E613E': {
                        name: 'green',
                        engrave: {eng_i: [0, 30], eng_f: [1600, 1600], eng_pierce: 0, dithering: false},
                        cut: [
                            {thicknessMM: 3, cut_i: 100, cut_f: 500, cut_p: 2}
                        ]
                    },
                    'D91F48': {
                        name: 'pink',
                        engrave: {eng_i: [0, 40], eng_f: [1600, 1600], eng_pierce: 0, dithering: false},
                        cut: [
                            {thicknessMM: 3, cut_i: 100, cut_f: 600, cut_p: 2}
                        ]
                    },
                }
            },
            'Foam Rubber': {
                name: gettext("Foam Rubber"),
                img: 'foam_rubber.jpg',
                description: gettext("Consists of poly urethane foam."),
                hints: gettext("Laser parameters are highly color dependant, bright colors might need pierce time."),
                safety_notes: '',
                laser_type: 'MrBeamII-1.0',
                colors: {
                    '0057a8': {
                        engrave: null,
                        cut: [{thicknessMM: 2, cut_i: 100, cut_f: 480, cut_p: 1},
                            {thicknessMM: 3, cut_i: 100, cut_f: 450, cut_p: 1}]
                    },
                    'ee6d2c': {
                        engrave: null,
                        cut: [{thicknessMM: 2, cut_i: 75, cut_f: 140, cut_p: 1}]
                    },
                    'e6e6e6': {
                        engrave: null,
                        cut: [{thicknessMM: 2, cut_i: 100, cut_f: 140, cut_p: 1}]
                    },
                    '000000': {
                        engrave: null,
                        cut: [{thicknessMM: 2, cut_i: 100, cut_f: 600, cut_p: 1}]
                    },
                    '41c500': {
                        engrave: null,
                        cut: [{thicknessMM: 2, cut_i: 100, cut_f: 600, cut_p: 1}]
                    },
                }
            },
            'Kraftplex': {
                name: gettext("Kraftplex"),
                img: 'kraftplex.jpg',
                description: gettext("100% natural fibers compressed under high temperature. Strong and bendable like metal."),
                hints: '',
                safety_notes: '',
                laser_type: 'MrBeamII-1.0',
                colors: {
                    '795f39': {
                        engrave: {eng_i: [0, 35], eng_f: [2000, 850], eng_pierce: 0, dithering: false},
                        cut: [
                            {thicknessMM: 0.8, cut_i: 100, cut_f: 225, cut_p: 2},
                            {thicknessMM: 1.5, cut_i: 100, cut_f: 110, cut_p: 2},
                            {thicknessMM: 3, cut_i: 100, cut_f: 100, cut_p: 5}
                        ]
                    }
                }
            },
            'Latex': null,
            'Paper': {
                name: gettext("Paper"),
                img: 'paper.jpg',
                description: gettext("Ordinary paper like from an office printer."),
                hints: '',
                safety_notes: gettext("Very fine structures may be subject of ignition."),
                laser_type: 'MrBeamII-1.0',
                colors: {
                    'e7d27f': {
                        engrave: null,
                        cut: [
                            {thicknessMM: 0.1, cut_i: 75, cut_f: 600, cut_p: 1},
                            {thicknessMM: 0.2, cut_i: 85, cut_f: 600, cut_p: 2} //  >300g is what we said in the old system
                        ]
                    }
                }
            },
            'Plywood Poplar': {
                name: gettext("Plywood Poplar"),
                img: 'plywood.jpg',
                description: gettext("Plywood from an ordinary hardware store or arts and craft supply."),
                hints: gettext("Watch out for dedicated laser plywood - it has better surface quality and only natural glue."),
                safety_notes: gettext("Very fine structures may be subject of ignition."),
                laser_type: 'MrBeamII-1.0',
                colors: {
                    'e7d27f': {
                        engrave: {eng_i: [18, 35], eng_f: [2000, 750], eng_pierce: 0, dithering: false},
                        cut: [
                            {thicknessMM: 3, cut_i: 100, cut_f: 110, cut_p: 3},
                            {thicknessMM: 4, cut_i: 100, cut_f: 100, cut_p: 3},
                        ]
                    }
                }
            },
            'Wellboard': {
                name: gettext("Wellboard"),
                img: 'wellboard.jpg',
                description: gettext("100% natural fibers similar to Kraftplex, but wavy."),
                hints: gettext("Thickness is measured over the whole wave."),
                safety_notes: '',
                laser_type: 'MrBeamII-1.0',
                colors: {
                    'e7d27f': {
                        engrave: {eng_i: [10, 35], eng_f: [2000, 850], eng_pierce: 0, dithering: false},
                        cut: [
                            {thicknessMM: 6, cut_i: 100, cut_f: 160, cut_p: 2},
                            {thicknessMM: 10, cut_i: 100, cut_f: 100, cut_p: 3},
                        ]
                    }
                }
            },
        };

        ///// EDIT MATERIAL SETTINGS ABOVE THIS LINE ////////





    };


    ADDITIONAL_VIEWMODELS.push(
        [MaterialSettingsViewModel,
            [],
            [ /* ... */]
        ]);

})
