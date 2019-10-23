/* global ADDITIONAL_VIEWMODELS */

$(function () {

    function MaterialSettingsViewModel(params) {
        let self = this;
        window.mrbeam.viewModels['materialSettingsViewModel'] = self;
        self.default_laser_type = 'MrBeamII-1.0';

        self.materialSettingsDatabase = {};

        self.loadMaterialSettings = function (callback) {
            console.log("Loading standard materials");
            OctoPrint.simpleApiCommand("mrbeam", "material_settings", {})
                .done(function (response) {
                    self.materialImportedSettings = response;
                    for (let materialKey in self.materialSettingsDatabase) {
                        if (materialKey in self.materialImportedSettings) {
                            self.materialSettingsDatabase[materialKey].colors = self.materialImportedSettings[materialKey].colors;
                        } else {
                            delete self.materialSettingsDatabase[materialKey]
                        }
                    }
                    if (callback) {
                        callback(self.materialSettingsDatabase);
                    }
                })
                .fail(function (response) {
                    console.error("Unable to parse the laser settings correctly: ", response);
                });
        };

        self.materialSettingsDatabase = {


            ///// EDIT MATERIAL SETTINGS BELOW THIS LINE ////////

            'Anodized Aluminum': {
                name: gettext("Anodized Aluminum"),
                img: 'anodized_aluminum.jpg',
                description: gettext("Dark anodized aluminum can be engraved. Works on iPhones."),
                hints: gettext("Requires very precise focus. Anodized aluminum turns brighter through laser engraving. Therefore we suggest to invert photos for engravings."),
                // colors: {
                //     '000000': {
                //             engrave: {eng_i: [0, 100], eng_f: [1000, 30], engrave_compressor_lvl: 0, eng_pierce: 0, dithering: false},
                //             cut: []
                //         }
                //     }
            },
            'Balsa Wood': {
                name: gettext("Balsa Wood"),
                img: 'balsa_wood.jpg',
                description: '',
                hints: '',
                safety_notes: gettext("Take care about ignitions. Never run a job slower than 300 mm/min!"),
                // colors: {
                //     'd4b26f': {
                //         engrave: {eng_i: [0, 20], eng_f: [2000, 350], engrave_compressor_lvl: 0, eng_pierce: 0, dithering: false},
                //         cut: [
                //             {thicknessMM: 1, cut_i: 80, cut_f: 525, cut_p: 2},
                //             {thicknessMM: 2, cut_i: 100, cut_f: 525, cut_p: 2},
                //             {thicknessMM: 3, cut_i: 100, cut_f: 525, cut_p: 2},
                //             {thicknessMM: 4, cut_i: 100, cut_f: 450, cut_p: 3},
                //             {thicknessMM: 5, cut_i: 100, cut_f: 225, cut_p: 3}
                //         ]
                //     }
                // }
            },
            'Bamboo': {
                name: gettext("Bamboo Wood"),
                img: 'bamboo.jpg',
                description: '',
                hints: '',
                safety_notes: '',
            },
            'Cardboard, corrugated single wave': {
                name: gettext("Cardboard, single wave"),
                img: 'cardboard_single_wave.jpg',
                description: gettext("Ordinary cardboard like most packaging is made of."),
                hints: gettext("Engraving looks great if just the first layer is lasered away, that the wave is visible underneath."),
                safety_notes: gettext("Take care about ignitions. Never run a job slower than 180 mm/min!"),
            },
            'Cardboard, corrugated double wave': {
                name: gettext("Cardboard, double wave"),
                img: 'cardboard_double_wave.jpg',
                description: gettext("Ordinary cardboard like strong packaging is made of."),
                hints: gettext("Engraving looks great if just the first layer is lasered away, that the wave is visible underneath."),
                safety_notes: gettext("Take care about ignitions. Never run a job slower than 180 mm/min!"),
            },
            'Fabric Cotton': null,
            'Fabric Polyester': null,
            'Finn Cardboard': {
                name: gettext("Finn Cardboard"),
                img: 'finn_cardboard.jpg',
                description: gettext("Made out of purely wooden fibres, often used for architectural models."),
                hints: '',
                safety_notes: '',
            },
            'Felt': { // took settings from IHM fair
                name: gettext("Felt"),
                img: 'felt.jpg',
                description: gettext("Acrylic felt like the one sold in many arts and craft stores."),
                hints: gettext("Be aware that natural felt is something else."),
                safety_notes: '',
            },
            'Foam Rubber': {
                name: gettext("Foam Rubber"),
                img: 'foam_rubber.jpg',
                description: gettext("Consists of poly urethane foam."),
                hints: gettext("Laser parameters are highly color dependant, bright colors might need pierce time."),
                safety_notes: '',
            },
            'Kraftplex': {
                name: gettext("Kraftplex"),
                img: 'kraftplex.jpg',
                description: gettext("100% natural fibers compressed under high temperature. Strong and bendable like metal."),
                hints: '',
                safety_notes: '',
            },
            'Latex': null,
            'Paper': {
                name: gettext("Paper"),
                img: 'paper.jpg',
                description: gettext("Ordinary paper like from an office printer."),
                hints: '',
                safety_notes: gettext("Very fine structures may be subject of ignition."),
            },
            'Plywood Poplar': {
                name: gettext("Plywood Poplar"),
                img: 'plywood.jpg',
                description: gettext("Plywood from an ordinary hardware store or arts and craft supply."),
                hints: gettext("Watch out for dedicated laser plywood - it has better surface quality and only natural glue."),
                safety_notes: gettext("Very fine structures may be subject of ignition."),
            },
            'Wellboard': {
                name: gettext("Wellboard"),
                img: 'wellboard.jpg',
                description: gettext("100% natural fibers similar to Kraftplex, but wavy."),
                hints: gettext("Thickness is measured over the whole wave."),
                safety_notes: '',
            },
        };

        ///// EDIT MATERIAL SETTINGS ABOVE THIS LINE ////////`


    }


    ADDITIONAL_VIEWMODELS.push(
        [MaterialSettingsViewModel,
            [],
            [ /* ... */]
        ]);

});
