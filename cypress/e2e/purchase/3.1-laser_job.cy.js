describe("Laser Job", function () {

    beforeEach(function () {
        cy.fixture('test-data').then(function (testData) {
            this.testData = testData
        });
    });

    beforeEach(function () {
        cy.visit(this.testData.url_laser);
        cy.wait(10000);
        cy.loginLaser(this.testData.email, this.testData.password);
    });

    it('Add design', function () {
        cy.get('[id="working_area_tab_file_btn"]').click();
        cy.get('[id="files_list"]').then($elem => {
            if (($elem.find('.files_template_model_image').filter(':contains("mirror.png")').length)) {}
            else {
                const filepath = 'mirror.png';
                cy.get('.fileinput-button input[type="file"]').attachFile(filepath);
                cy.wait(5000)
                cy.get('.files_template_model_image').contains('mirror.png').should('to.exist');
            };
        });
        cy.get('.files_template_model_image').filter(':contains("mirror.png")').click();
        cy.wait(3000);
        cy.get('.translation').clear().type('235.0, 138.0');
        cy.get('.rotation').clear().type('-50.5');
        cy.get('.horizontal').clear().type('125.3 mm');
        cy.get('.vertical').clear().type('130.3 mm');
        cy.get('[id="laser_button"]').click();
        cy.wait(2000);
        cy.focusReminder();
        cy.wait(2000);
        cy.get('.material_entry').contains(/^Foam Rubber$/).click();
        cy.get('[id="material_color_0057a8"]').click();
        cy.wait(1000);
        cy.get('[id="material_thickness_2"]').click();
        cy.get('[id="svgtogcode_img_intensity_black"]').clear().type('95');
        cy.get('[id="svgtogcode_img_feedrate_black"]').clear().type('1500');
        cy.get('[id="parameter_assignment_show_advanced_settings_cb"]').click();
        cy.get('.passes_input').first().clear().type('4');
        cy.get('[id="parameter_assignment_pierce_time_in"]').clear().type('8');
        cy.get('[id="svgtogcode_img_line_dist"]').clear().type('1');
        cy.get('[id="parameter_assignment_engraving_mode_basic_btn"]').dblclick({ force: true });
        cy.get('[id="start_job_btn"]').dblclick();
        cy.wait(2000);
        cy.get('.alert-success').should('to.exist', 'Preparation done');
        cy.reload();
        cy.wait(10000);
        cy.get('[id="designlib_tab_btn"]').click();
        cy.get('[id="design_lib_filter_gcode_radio"]').click();
        cy.get('.files_template_machinecode_gcode').first().click();
        cy.get('[id="laser_button"]').click();
        cy.get('.alert-success').should('to.exist', 'Preparation done');
        cy.logout();
    });
});
