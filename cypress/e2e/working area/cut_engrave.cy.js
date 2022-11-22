describe("Cut and engrave", function () {

    const dataTransfer = new DataTransfer();

    beforeEach(function () {
        cy.fixture("test-data").then(function (testData) {
            this.testData = testData;
        });
    });

    beforeEach(function () {
        cy.visit(this.testData.url_laser);
        cy.wait(10000);
        cy.loginLaser(this.testData.email, this.testData.password);
    });

    it('Cut and engrave', function () {
        cy.get('[id="working_area_tab_shape_btn"]').click();
        cy.get('[id="shape_tab_link_star"]').click();
        cy.get('[id="qs_colorPicker_stroke"]').click();
        cy.get('#qs_colorPicker_stroke > .track > canvas').realClick({ position: "top" });
        cy.get('[id="quick_shape_fill"]').click();
        cy.get('[id="qs_colorPicker_fill"]').click();
        cy.get('#qs_colorPicker_fill > .track > canvas').realClick({ position: "top" });
        cy.get('[id="quick_shape_shape_done_btn"]').click();
        cy.get('[id="working_area_tab_file_btn"]').click();
        cy.get(".files_template_model_image")
            .filter(':contains("paris2.jpg")')
            .click();
        cy.get('[id="laser_button"]').click();
        cy.get(".material_entry").contains("Finn Cardboard").click();
        cy.get('[id="material_thickness_1.5"]').click();
        cy.get('.cutting_job_color').trigger('dragstart', { dataTransfer });
        cy.get('#engrave_job_drop_zone_conversion_dialog').trigger('drop', { dataTransfer });
        cy.get('[id="svgtogcode_img_intensity_black"]').clear().type("70");
        cy.get('[id="svgtogcode_img_intensity_white"]').clear().type("25");
        cy.get('[id="svgtogcode_img_feedrate_white"]').clear().type("1500");
        cy.get('[id="svgtogcode_img_feedrate_black"]').clear().type("3000");
        cy.get('[id="parameter_assignment_show_advanced_settings_cb"]').click();
        cy.get(".passes_input").first().clear().type("1");
        cy.get('[id="parameter_assignment_pierce_time_in"]').clear().type("2");
        cy.get('[id="svgtogcode_img_line_dist"]').clear().type("1");
        cy.get('[id="parameter_assignment_engraving_mode_basic_btn"]').dblclick({ force: true });
        cy.get('.checkbox-control-and-label > .controls > .checkbox > input').click({ force: true });
        cy.get('.param_intensity').clear().type("95");
        cy.get('.param_feedrate').clear().type("1500");
        cy.get('.param_cut_compressor').realClick({ position: "left" });
        cy.get('.cut_passes_input').clear().type("3");
        cy.get('.param_progressive').click();
        cy.get('.param_piercetime').last().clear().type("10");
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

    it.only('Skip', function () {
        cy.get('[id="working_area_tab_shape_btn"]').click();
        cy.get('[id="shape_tab_link_star"]').click();
        cy.get('[id="quick_shape_shape_done_btn"]').click();
        cy.get('[id="laser_button"]').click();
        cy.get(".material_entry").contains("Finn Cardboard").click();
        cy.get('[id="material_thickness_1.5"]').click();
        cy.get('.cutting_job_color').eq(0).trigger('dragstart', {dataTransfer});
        cy.get('#no_job > .span3 > .assigned_colors').trigger('drop', {dataTransfer});
        cy.get('[id="start_job_btn"]').dblclick({force:true});
        cy.get('.modal-content').contains('Settings to be adjusted').should('to.exist');
        cy.get('.modal-content').find('.btn').contains('Ok').click({force:true});
        cy.get('#dialog_vector_graphics_conversion > :nth-child(4) > [aria-hidden="true"]').click({force:true});
        cy.logout();
    });
});