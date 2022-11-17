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

    it("Add texts", function () {
        cy.wait(3000);
        cy.get('[id="working_area_tab_text_btn"]').click();
        cy.get('[id="quick_text_dialog_text_input"]').type("MrBeam");
        cy.get('[id="quick_text_cw"]').click();
        cy.get('[id="quick_text_fill"]').click();
        cy.get('[id="quick_text_dialog_circle"]').trigger("right");
        cy.get(".quicktext-font-button").last().click();
        cy.get('[id="quick_text_stroke"]').click();
        cy.get('[id="quick_text_text_done_btn"]').click();
        cy.get('[id="translateHandle"]').move({
            deltaX: 433.9689,
            deltaY: 220.1241,
            force: true,
        });
        cy.get(".rotation").clear().type("-50.5");
        cy.get(".horizontal").clear().type("116.3 mm");
        cy.get(".vertical").clear().type("132.3 mm");
        cy.get('[id="laser_button"]').click();
        cy.wait(2000);
        cy.focusReminder();
        cy.wait(2000);
        cy.get(".material_entry")
            .contains(/^Leather$/)
            .click({ force: true });
        cy.get('[id="material_color_b45f06"]').click();
        cy.wait(1000);
        cy.get('[id="material_thickness_0.8"]').click();
        cy.get('[id="svgtogcode_img_intensity_black"]').clear().type("70");
        cy.get('[id="svgtogcode_img_feedrate_black"]').clear().type("3000");
        cy.get('[id="parameter_assignment_show_advanced_settings_cb"]').click();
        cy.get(".passes_input").first().clear().type("1");
        cy.get('[id="parameter_assignment_pierce_time_in"]').clear().type("2");
        cy.get('[id="svgtogcode_img_line_dist"]').clear().type("1");
        cy.get('[id="parameter_assignment_engraving_mode_basic_btn"]').dblclick(
            { force: true }
        );
        cy.get('[id="start_job_btn"]').dblclick();
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.reload();
        cy.wait(10000);
        cy.get('[id="designlib_tab_btn"]').click();
        cy.get('[id="design_lib_filter_gcode_radio"]').click();
        cy.get(".files_template_machinecode_gcode").first().click();
        cy.get('[id="laser_button"]').click();
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.logout();
    });

    xit("Add texts 2", function () {
        cy.wait(3000);
        cy.get('[id="working_area_tab_text_btn"]').click();
        cy.get('[id="quick_text_dialog_text_input"]').type("Lasers");
        cy.get('[id="quick_text_ccw"]').click();
        cy.get('[id="quick_text_dialog_circle"]').trigger("right");
        cy.get(".quicktext-font-button").last().click();
        cy.get('[id="quick_text_text_done_btn"]').click();
        cy.get(".translation").clear().type("235.0, 238.0");
        cy.get(".rotation").clear().type("250.5");
        cy.get(".horizontal").clear().type("225.3 mm");
        cy.get(".vertical").clear().type("230.3 mm");
        cy.get('[id="laser_button"]').click();
        cy.focusReminder();
        cy.get(".material_entry").contains("Cork").click({ force: true });
        cy.wait(1000);
        cy.get('[id="svgtogcode_img_intensity_black"]').clear().type("70");
        cy.get('[id="svgtogcode_img_feedrate_black"]').clear().type("3000");
        cy.get('[id="parameter_assignment_show_advanced_settings_cb"]').click();
        cy.get(".passes_input").first().clear().type("1");
        cy.get('[id="parameter_assignment_pierce_time_in"]').clear().type("2");
        cy.get('[id="svgtogcode_img_line_dist"]').clear().type("1");
        cy.get('[id="parameter_assignment_engraving_mode_basic_btn"]').dblclick(
            { force: true }
        );
        cy.get('[id="start_job_btn"]').dblclick();
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.reload();
        cy.wait(10000);
        cy.get('[id="designlib_tab_btn"]').click();
        cy.get('[id="design_lib_filter_gcode_radio"]').click();
        cy.get(".files_template_machinecode_gcode").first().click();
        cy.get('[id="laser_button"]').click();
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.logout();
    });

    xit("Add texts 3", function () {
        cy.wait(3000);
        cy.get('[id="working_area_tab_text_btn"]').click();
        cy.get('[id="quick_text_dialog_text_input"]').type("MrBeam Lasers");
        cy.get(".quicktext-font-button").last().dblclick();
        cy.get('[id="quick_text_straight"]').click();
        cy.get('[id="quick_text_stroke"]').click();
        cy.get('[id="quick_text_text_done_btn"]').click();
        cy.get(".translation").clear().type("235.0, 138.0");
        cy.get(".rotation").clear().type("-50.5");
        cy.get(".horizontal").clear().type("125.3 mm");
        cy.get(".vertical").clear().type("130.3 mm");
        cy.get('[id="laser_button"]').click();
        cy.focusReminder();
        cy.get(".material_entry").contains("Foam").click({ force: true });
        cy.wait(1000);
        cy.get('[id="material_thickness_10"]').click();
        cy.get('[id="svgtogcode_img_intensity_black"]').clear().type("70");
        cy.get('[id="svgtogcode_img_feedrate_black"]').clear().type("3000");
        cy.get('[id="parameter_assignment_show_advanced_settings_cb"]').click();
        cy.get(".passes_input").first().clear().type("1");
        cy.get('[id="parameter_assignment_pierce_time_in"]').clear().type("2");
        cy.get('[id="svgtogcode_img_line_dist"]').clear().type("1");
        cy.get('[id="parameter_assignment_engraving_mode_basic_btn"]').dblclick(
            { force: true }
        );
        cy.get('[id="start_job_btn"]').dblclick();
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.reload();
        cy.wait(10000);
        cy.get('[id="designlib_tab_btn"]').click();
        cy.get('[id="design_lib_filter_gcode_radio"]').click();
        cy.get(".files_template_machinecode_gcode").first().click();
        cy.get('[id="laser_button"]').click();
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.logout();
    });
});
