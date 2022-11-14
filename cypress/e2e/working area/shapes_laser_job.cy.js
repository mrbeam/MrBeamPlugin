describe("Laser Job - shapes", function () {
    beforeEach(function () {
        cy.fixture("test-data").then(function (testData) {
            this.testData = testData;
        });
    });

    beforeEach(function () {
        cy.visit(this.testData.url_laser);
        cy.wait(10000);
        cy.loginLaser(this.testData.email, this.testData.password);
        cy.wait(7000);
    });

    it("Add shapes - heart", function () {
        cy.get('[id="working_area_tab_shape_btn"]').click();
        cy.get('[id="shape_tab_link_heart"]').click();
        cy.get('[id="quick_shape_heart_w"]').clear().type("60");
        cy.get('[id="quick_shape_heart_h"]').clear().type("80");
        cy.get('[id="quick_shape_heart_lr"]').realClick({ position: "right" });
        cy.get('[id="qs_colorPicker_stroke"]').click();
        cy.get('#qs_colorPicker_stroke > .track > canvas').realClick({ position: "left" });
        cy.get('[id="quick_shape_fill"]').click();
        cy.get('[id="qs_colorPicker_fill"]').click();
        cy.get('#qs_colorPicker_fill > .track > canvas').realClick({ position: "top" });
        cy.get('[id="quick_shape_shape_done_btn"]').click();
        cy.get('[id="translateHandle"]').move({
            deltaX: 33.9689,
            deltaY: 120.1241,
            force: true,
        });
        cy.get(".rotation").clear().type("-50.5");
        cy.get(".horizontal").clear().type("125.3 mm");
        cy.get(".vertical").clear().type("130.3 mm");
        cy.get('[id="laser_button"]').click();
        cy.wait(2000);
        cy.focusReminder();
        cy.wait(2000);
        cy.get(".material_entry").contains("Cardboard, double wave").click();
        cy.wait(1000);
        cy.get('[id="material_thickness_4"]').click();
        cy.get('[id="svgtogcode_img_intensity_black"]').clear().type("95");
        cy.get('[id="svgtogcode_img_feedrate_black"]').clear().type("1500");
        cy.get('[id="parameter_assignment_show_advanced_settings_cb"]').click();
        cy.get(".passes_input").first().clear().type("2");
        cy.get('[id="parameter_assignment_pierce_time_in"]').clear().type("5");
        cy.get('[id="svgtogcode_img_line_dist"]').clear().type("0.5");
        cy.get(
            ".checkbox-control-and-label > .controls > .checkbox > input"
        ).click({ force: true });
        cy.get(
            '[id="parameter_assignment_engraving_mode_precise_btn"]'
        ).dblclick({ force: true });
        cy.get('[id="start_job_btn"]').dblclick();
        cy.wait(7000);
        cy.reload();
        cy.wait(10000);
        cy.get('[id="designlib_tab_btn"]').click();
        cy.get('[id="design_lib_filter_gcode_radio"]').click();
        cy.get(".files_template_machinecode_gcode").first().click();
        cy.get('[id="laser_button"]').click();
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.logout();
    });

    it("Add shapes - circle", function () {
        cy.get('[id="working_area_tab_shape_btn"]').click();
        cy.get('[id="shape_tab_link_circle"]').click();
        cy.get('[id="quick_shape_circle_radius"]').clear().type("60");
        cy.get('[id="qs_colorPicker_stroke"]').click();
        cy.get('#qs_colorPicker_stroke > .track > canvas').realClick({ position: "right" });
        cy.get('[id="quick_shape_fill"]').click();
        cy.get('[id="qs_colorPicker_fill"]').click();
        cy.get('#qs_colorPicker_fill > .track > canvas').realClick({ position: "bottom" });
        cy.get('[id="quick_shape_shape_done_btn"]').click();
        cy.get(".translation").clear().type("235.0, 138.0");
        cy.get(".rotation").clear().type("-50.5");
        cy.get(".horizontal").clear().type("125.3 mm");
        cy.get(".vertical").clear().type("130.3 mm");
        cy.get('[id="laser_button"]').click();
        cy.focusReminder();
        cy.get(".material_entry").contains("Anodized Aluminum").click();
        cy.get('[id="svgtogcode_img_intensity_black"]').clear().type("95");
        cy.get('[id="svgtogcode_img_feedrate_black"]').clear().type("900");
        cy.get('[id="parameter_assignment_show_advanced_settings_cb"]').click();
        cy.get(".passes_input").first().clear().type("2");
        cy.get('[id="parameter_assignment_pierce_time_in"]').clear().type("5");
        cy.get('[id="svgtogcode_img_line_dist"]').clear().type("0.5");
        cy.get(
            ".checkbox-control-and-label > .controls > .checkbox > input"
        ).click({ force: true });
        cy.get(
            '[id="parameter_assignment_engraving_mode_precise_btn"]'
        ).dblclick({ force: true });
        cy.get('[id="start_job_btn"]').dblclick();
        cy.wait(7000);
        cy.reload();
        cy.wait(10000);
        cy.get('[id="designlib_tab_btn"]').click();
        cy.get('[id="design_lib_filter_gcode_radio"]').click();
        cy.get(".files_template_machinecode_gcode").first().click();
        cy.get('[id="laser_button"]').click();
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.logout();
    });

    it("Add shapes - star", function () {
        cy.get('[id="working_area_tab_shape_btn"]').click();
        cy.get('[id="shape_tab_link_star"]').click();
        cy.get('[id="quick_shape_star_radius"]').clear().type("60");
        cy.get('[id="quick_shape_star_corners"]').clear().type("8");
        cy.get('[id="quick_shape_star_sharpness"]').realClick();
        cy.get('[id="qs_colorPicker_stroke"]').click();
        cy.get('#qs_colorPicker_stroke > .track > canvas').realClick({ position: "top" });
        cy.get('[id="quick_shape_fill"]').click();
        cy.get('[id="qs_colorPicker_fill"]').click();
        cy.get('#qs_colorPicker_fill > .track > canvas').realClick({ position: "top" });
        cy.get('[id="quick_shape_shape_done_btn"]').click();
        cy.get(".translation").clear().type("235.0, 238.0");
        cy.get(".rotation").clear().type("250.5");
        cy.get(".horizontal").clear().type("225.3 mm");
        cy.get(".vertical").clear().type("230.3 mm");
        cy.get('[id="laser_button"]').click();
        cy.focusReminder();
        cy.get(".material_entry").contains("Finn Cardboard").click();
        cy.wait(1000);
        cy.get('[id="material_thickness_1.5"]').click();
        cy.get('[id="svgtogcode_img_intensity_black"]').clear().type("95");
        cy.get('[id="svgtogcode_img_feedrate_black"]').clear().type("1200");
        cy.get('[id="parameter_assignment_show_advanced_settings_cb"]').click();
        cy.get(".passes_input").first().clear().type("2");
        cy.get('[id="parameter_assignment_pierce_time_in"]').clear().type("5");
        cy.get('[id="svgtogcode_img_line_dist"]').clear().type("0.5");
        cy.get(
            ".checkbox-control-and-label > .controls > .checkbox > input"
        ).click({ force: true });
        cy.get(
            '[id="parameter_assignment_engraving_mode_precise_btn"]'
        ).dblclick({ force: true });
        cy.get('[id="start_job_btn"]').dblclick();
        cy.wait(7000);
        cy.reload();
        cy.wait(10000);
        cy.get('[id="designlib_tab_btn"]').click();
        cy.get('[id="design_lib_filter_gcode_radio"]').click();
        cy.get(".files_template_machinecode_gcode").first().click();
        cy.get('[id="laser_button"]').click();
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.logout();
    });

    it("Add shapes - line", function () {
        cy.get('[id="working_area_tab_shape_btn"]').click();
        cy.get('[id="shape_tab_link_line"]').click();
        cy.get('[id="quick_shape_line_length"]').clear().type("60");
        cy.get('[id="qs_colorPicker_stroke"]').click();
        cy.get('#qs_colorPicker_stroke > .track > canvas').realClick({ position: "bottom" });
        cy.get('[id="quick_shape_fill"]').click();
        cy.get('[id="qs_colorPicker_fill"]').click();
        cy.get('#qs_colorPicker_fill > .track > canvas').realClick({ position: "bottom" });
        cy.get('[id="quick_shape_shape_done_btn"]').click();
        cy.get(".translation").clear().type("135.0, 138.0");
        cy.get(".rotation").clear().type("150.5");
        cy.get(".horizontal").clear().type("125.3 mm");
        cy.get(".vertical").clear().type("130.3 mm");
        cy.get('[id="laser_button"]').click();
        cy.focusReminder();
        cy.get(".material_entry").contains("Polypropylene").click();
        cy.get('[id="material_color_ff0000"]').click();
        cy.wait(1000);
        cy.get('[id="material_thickness_0.8"]').click();
        cy.get('[id="svgtogcode_img_intensity_black"]').clear().type("95");
        cy.get('[id="svgtogcode_img_feedrate_black"]').clear().type("1300");
        cy.get('[id="parameter_assignment_show_advanced_settings_cb"]').click();
        cy.get(".passes_input").first().clear().type("2");
        cy.get('[id="parameter_assignment_pierce_time_in"]').clear().type("5");
        cy.get('[id="svgtogcode_img_line_dist"]').clear().type("0.5");
        cy.get(
            ".checkbox-control-and-label > .controls > .checkbox > input"
        ).click({ force: true });
        cy.get(
            '[id="parameter_assignment_engraving_mode_precise_btn"]'
        ).dblclick({ force: true });
        cy.get('[id="start_job_btn"]').dblclick();
        cy.wait(7000);
        cy.reload();
        cy.wait(10000);
        cy.get('[id="designlib_tab_btn"]').click();
        cy.get('[id="design_lib_filter_gcode_radio"]').click();
        cy.get(".files_template_machinecode_gcode").first().click();
        cy.get('[id="laser_button"]').click();
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.logout();
    });

    it("Add shapes - rectangle", function () {
        cy.get('[id="working_area_tab_shape_btn"]').click();
        cy.get('[id="shape_tab_link_rect"]').click();
        cy.get('[id="quick_shape_rect_w"]').clear().type("60");
        cy.get('[id="quick_shape_rect_h"]').clear().type("60");
        cy.get('[id="quick_shape_rect_radius"]').realClick();
        cy.get('[id="qs_colorPicker_stroke"]').click();
        cy.get('#qs_colorPicker_stroke > .track > canvas').realClick({ position: "left" });
        cy.get('[id="quick_shape_fill"]').click();
        cy.get('[id="qs_colorPicker_fill"]').click();
        cy.get('#qs_colorPicker_fill > .track > canvas').realClick({ position: "bottom" });
        cy.get('[id="quick_shape_shape_done_btn"]').click();
        cy.get(".translation").clear().type("135.0, 138.0");
        cy.get(".rotation").clear().type("150.5");
        cy.get(".horizontal").clear().type("125.3 mm");
        cy.get(".vertical").clear().type("130.3 mm");
        cy.get('[id="laser_button"]').click();
        cy.focusReminder();
        cy.get(".material_entry").contains("Polypropylene").click();
        cy.get('[id="material_color_ff0000"]').click();
        cy.wait(1000);
        cy.get('[id="material_thickness_0.8"]').click();
        cy.get('[id="svgtogcode_img_intensity_black"]').clear().type("95");
        cy.get('[id="svgtogcode_img_feedrate_black"]').clear().type("1300");
        cy.get('[id="parameter_assignment_show_advanced_settings_cb"]').click();
        cy.get(".passes_input").first().clear().type("2");
        cy.get('[id="parameter_assignment_pierce_time_in"]').clear().type("5");
        cy.get('[id="svgtogcode_img_line_dist"]').clear().type("0.5");
        cy.get(
            ".checkbox-control-and-label > .controls > .checkbox > input"
        ).click({ force: true });
        cy.get(
            '[id="parameter_assignment_engraving_mode_precise_btn"]'
        ).dblclick({ force: true });
        cy.get('[id="start_job_btn"]').dblclick();
        cy.wait(7000);
        cy.reload();
        cy.wait(10000);
        cy.get('[id="designlib_tab_btn"]').click();
        cy.get('[id="design_lib_filter_gcode_radio"]').click();
        cy.get(".files_template_machinecode_gcode").first().click();
        cy.get('[id="laser_button"]').click();
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.logout();
    });

    it("Add shapes - ok button", function () {
        cy.get('[id="working_area_tab_shape_btn"]').click();
        cy.get('[id="quick_shape_dialog"]').should('to.visible');
        cy.get('[id="quick_shape_shape_done_btn"]').click();
        cy.get('[id="quick_shape_dialog"]').should('not.visible');
    });
});