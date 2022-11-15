describe("Laser Job", function () {
    beforeEach(function () {
        cy.fixture("test-data").then(function (testData) {
            this.testData = testData;
        });
    });

    beforeEach(function () {
        cy.visit(this.testData.url_laser);
        cy.wait(10000);
        cy.loginLaser(this.testData.email, this.testData.password);
        cy.wait(5000);
    });

    it("Add svg file", function () {
        cy.get('[id="working_area_tab_file_btn"]').click();
        cy.get('[id="files_list"]').then(($elem) => {
            if (
                $elem
                    .find(".files_template_model_svg")
                    .filter(':contains("Focus_Tool_Mr_Beam_Laser_1.svg")').length
            ) {
            } else {
                const filepath = "Focus_Tool_Mr_Beam_Laser_1";
                cy.get('.fileinput-button input[type="file"]').attachFile(
                    filepath
                );
                cy.wait(5000);
                cy.get(".files_template_model_svg")
                    .contains("Focus_Tool_Mr_Beam_Laser_1.svg")
                    .should("to.exist");
            }
        });
        cy.get(".files_template_model_svg")
            .filter(':contains("Focus_Tool_Mr_Beam_Laser_1.svg")')
            .click();
        cy.wait(3000);
        cy.get(".translation").clear().type("235.0, 238.0");
        cy.get(".rotation").clear().type("250.5");
        cy.get(".horizontal").clear().type("225.3 mm");
        cy.get(".vertical").clear().type("230.3 mm");
        cy.get('.wa_list_item_burger_menu').click();
        cy.contains('by stroke color').click();
        cy.get('[id="laser_button"]').click();
        cy.wait(2000);
        cy.focusReminder();
        cy.wait(2000);
        cy.get(".material_entry").contains("Cardboard, single wave").click();
        cy.wait(1000);
        cy.get('[id="material_thickness_1.5"]').click();
        cy.get('[id="svgtogcode_img_intensity_black"]').clear().type("95");
        cy.get('[id="svgtogcode_img_feedrate_black"]').clear().type("1500");
        cy.get('[id="parameter_assignment_show_advanced_settings_cb"]').click();
        cy.get(".passes_input").first().clear().type("4");
        cy.get('[id="parameter_assignment_pierce_time_in"]').clear().type("8");
        cy.get('[id="svgtogcode_img_line_dist"]').clear().type("1");
        cy.get('[id="parameter_assignment_engraving_mode_basic_btn"]').dblclick({ force: true });
        cy.get('[id="start_job_btn"]').dblclick();
        cy.wait(2000);
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.reload();
        cy.wait(10000);
        cy.get('[id="designlib_tab_btn"]').click();
        cy.get('[id="design_lib_filter_gcode_radio"]').click();
        cy.get(".files_template_machinecode_gcode").first().click();
        cy.get('[id="laser_button"]').click();
        cy.wait(5000);
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.logout();
    });

    it("Add svg file", function () {
        cy.get('[id="working_area_tab_file_btn"]').click();
        cy.get(".files_template_model_svg")
            .filter(':contains("Focus_Tool_Mr_Beam_Laser_1.svg")')
            .click();
        cy.wait(3000);
        cy.get(".translation").clear().type("235.0, 238.0");
        cy.get(".rotation").clear().type("250.5");
        cy.get(".horizontal").clear().type("225.3 mm");
        cy.get(".vertical").clear().type("230.3 mm");
        cy.get('.wa_list_item_burger_menu').click();
        cy.contains('horizontally').click();
        cy.logout();
    });

    it("Add svg file", function () {
        cy.get('[id="working_area_tab_file_btn"]').click();
        cy.get(".files_template_model_svg")
            .filter(':contains("Focus_Tool_Mr_Beam_Laser_1.svg")')
            .click();
        cy.wait(3000);
        cy.get('.btn-mini').find('.icon-move').click({force:true});
        cy.get(".translation").clear().type("235.0, 238.0");
        cy.get(".rotation").clear().type("250.5");
        cy.get(".horizontal").clear().type("225.3 mm");
        cy.get(".vertical").clear().type("230.3 mm");
        cy.get('.wa_list_item_burger_menu').click();
        cy.contains('vertically').click();
        cy.get('.wa_list_item_burger_menu').first().click();
        cy.get('.wa_list_item_burger_menu').first().click();
        cy.contains('into shapes').click();
        cy.get('.detail_information').should(($elem) => {
            expect($elem).to.have.length(13)
        });
        cy.logout();
    });

    it("Add svg file - ", function () {
        cy.get('[id="working_area_tab_file_btn"]').click();
        cy.get(".files_template_model_svg")
            .filter(':contains("Focus_Tool_Mr_Beam_Laser_1.svg")')
            .click();
        cy.wait(3000);
        cy.get(".translation").clear().type("235.0, 238.0");
        cy.get(".rotation").clear().type("250.5");
        cy.get(".horizontal").clear().type("225.3 mm");
        cy.get(".vertical").clear().type("230.3 mm");
        cy.get('.wa_list_item_burger_menu').click();
        cy.contains('vertically').click();
        cy.get('.wa_list_item_burger_menu').first().click();
        cy.contains('into shapes').click();
        cy.get('.wa_list_item_burger_menu').last().click();
        cy.contains('horizontally').click({force:true});
        cy.get('.wa_list_item_burger_menu').eq(10).click();
        cy.contains('by stroke color').click({force:true});
        cy.get('.detail_information').should(($elem) => {
            expect($elem).to.have.length(13)
        });
        cy.logout();
    });
});
