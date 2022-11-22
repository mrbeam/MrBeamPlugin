describe("Cut, cut 2, engrave, skip", function () {
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
   
    it('Cut 1, cut 2, engrave, skip', function () {
        cy.get('[id="working_area_tab_shape_btn"]').click();
        cy.get('[id="shape_tab_link_star"]').click(); 
        cy.get('[id="qs_colorPicker_stroke"]').click();
        cy.get('#qs_colorPicker_stroke > .track > canvas').realClick({ position: "top" });
        cy.get('[id="quick_shape_fill"]').click();
        cy.get('[id="qs_colorPicker_fill"]').click();
        cy.get('#qs_colorPicker_fill > .track > canvas').realClick({ position: "top" }); 
        cy.get('[id="quick_shape_shape_done_btn"]').click();
        cy.get('[id="working_area_tab_text_btn"]').click();
        cy.get('[id="quick_text_dialog_text_input"]').type("MrBeam");
        cy.get('[id="quick_text_cw"]').click();
        cy.get('[id="qt_colorPicker_fill"]').click();
        cy.get('#qt_colorPicker_fill > .track > canvas').realClick({ position: "top" });
        cy.get('[id="quick_text_stroke"]').click('center');
        cy.get('#qt_colorPicker_stroke > .track > canvas').realClick({ position: "left" });
        cy.get('[id="quick_text_text_done_btn"]').click();
        cy.get('[id="working_area_tab_shape_btn"]').click();
        cy.get('[id="shape_tab_link_heart"]').click();
        cy.get('[id="quick_shape_heart_lr"]').realClick({ position: "right" });
        cy.get('[id="qs_colorPicker_stroke"]').click();
        cy.get('#qs_colorPicker_stroke > .track > canvas').realClick({ position: "right" });
        cy.get('[id="quick_shape_fill"]').click();
        cy.get('[id="qs_colorPicker_fill"]').click();
        cy.get('#qs_colorPicker_fill > .track > canvas').realClick({ position: "top" });
        cy.get('[id="quick_shape_shape_done_btn"]').click();
        cy.get('[id="laser_button"]').click();
        cy.get(".material_entry").contains("Grey Cardboard").click();
        cy.get('[id="material_thickness_1"]').click();
        cy.get('.cutting_job_color').eq(0).trigger('dragstart', {dataTransfer});
        cy.get('#no_job > .span3 > .assigned_colors').trigger('drop', {dataTransfer});
        cy.get('.cutting_job_color').eq(2).trigger('dragstart', {dataTransfer});
        cy.get('[data-bind="visible: show_vector_parameters()"] > .assigned_colors').trigger('drop', {dataTransfer});
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
        cy.get('.param_intensity').first().clear().type("95");
        cy.get('.param_feedrate').first().clear().type("1500");
        cy.get('.param_cut_compressor').first().realClick({ position: "left" });
        cy.get('.cut_passes_input').first().clear().type("3");
        cy.get('.param_progressive').first().click();
        cy.get('.param_piercetime').eq(1).clear().type("10");
        cy.get('.param_intensity').last().clear().type("95");
        cy.get('.param_feedrate').last().clear().type("2500");
        cy.get('.param_cut_compressor').last().realClick();
        cy.get('.cut_passes_input').last().clear().type("2");
        cy.get('.param_progressive').last().click();
        cy.get('.param_piercetime').last().clear().type("15");
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
});