describe("Laser Job", function () {
    beforeEach(function () {
        cy.fixture("test-data").then(function (testData) {
            this.testData = testData;
        });
    });

    beforeEach(function () {
        cy.visit(this.testData.url_laser);
        cy.wait(20000);
        cy.loginLaser(this.testData.email, this.testData.password);
    });

    it("Add design", function () {
        cy.get('[id="working_area_tab_file_btn"]').click();
        cy.get('[id="files_list"]').then(($elem) => {
            if (
                $elem
                    .find(".files_template_model_image")
                    .filter(':contains("paris2.jpg")').length
            ) {
            } else {
                const filepath = "paris2.jpg";
                cy.get('.fileinput-button input[type="file"]').attachFile(
                    filepath
                );
                cy.wait(5000);
                cy.get(".files_template_model_image")
                    .contains("paris2.jpg")
                    .should("to.exist");
            }
        });
        cy.get(".files_template_model_image")
            .filter(':contains("paris2.jpg")')
            .click();
        cy.wait(3000);
        cy.get(".horizontal").clear().type("95.3 mm");
        cy.get(".vertical").clear().type("70.3 mm");
        cy.get(".userIMG").click({ force: true });
        cy.get('[id="translateHandle"]').move({
            deltaX: 213.9689,
            deltaY: -144.1241,
            force: true,
        });
        cy.get(".rotation").clear().type("200.5");
        cy.get('.multiply').clear().type('2x3');
        cy.get('.mirror_toggler').click();
        cy.get('.image-preprocessing-collapsible').click();
        cy.get('[id="img-preprocess-contrast"]').realClick({ position: "left" });
        cy.wait(1000)
        cy.get('[id="img-preprocess-brightness"]').realClick({ position: "right" });
        cy.wait(1000)
        cy.get('[id="img-preprocess-sharpen"]').realClick({ position: "right" });
        cy.wait(1000)
        cy.get('[id="img-preprocess-gamma"]').realClick({ position: "left" });
        cy.wait(1000)
        cy.get('.crop_top').clear().type('2')
        cy.get('.crop_left').clear().type('2')
        cy.get('.crop_bottom').clear().type('2')
        cy.get('.crop_right').clear().type('2')
        cy.get('[id="laser_button"]').click();
        cy.wait(2000);
        cy.focusReminder();
        cy.wait(2000);
        cy.get(".material_entry").contains("Paper").click();
        cy.get('[id="material_color_1155cc"]').click();
        cy.wait(1000);
        cy.get('[id="material_thickness_0.4"]').click();
        cy.get('[id="svgtogcode_img_intensity_black"]').clear().type("95");
        cy.get('[id="svgtogcode_img_intensity_white"]').clear().type("30");
        cy.get('[id="svgtogcode_img_feedrate_white"]').clear().type("900");
        cy.get('[id="svgtogcode_img_feedrate_black"]').clear().type("1500");
        cy.get('[id="parameter_assignment_show_advanced_settings_cb"]').click();
        cy.get(".passes_input").first().clear().type("4");
        cy.get('[id="parameter_assignment_pierce_time_in"]').clear().type("8");
        cy.get('[id="svgtogcode_img_line_dist"]').clear().type("1");
        cy.get('[id="parameter_assignment_engraving_mode_precise_btn"]').dblclick(
            { force: true }
        );
        cy.get('[id="start_job_btn"]').dblclick();
        cy.wait(2000);
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
