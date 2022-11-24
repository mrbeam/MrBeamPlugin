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
    });

    it("Add design", function () {
        cy.get('[data-test="working-area-tab-file"]').click();
        cy.get('[data-test="tab-designbib-files-list"]').then(($elem) => {
            if (
                $elem
                    .find(".files_template_model_image")
                    .filter(':contains("mirror.png")').length
            ) {
            } else {
                const filepath = "mirror.png";
                cy.get('[data-test="tab-design-library-upload-file"] input[type="file"]').attachFile(
                    filepath
                );
                cy.wait(5000);
                cy.get(".files_template_model_image")
                    .contains("mirror.png")
                    .should("to.exist");
            }
        });
        cy.get(".files_template_model_image")
            .filter(':contains("mirror.png")')
            .click();
        cy.wait(3000);
        cy.get('.btn-mini').find('.icon-move').click({force:true});
        cy.get('.scale_prop_btn').click();
        cy.get(".horizontal").clear().type("125.3 mm");
        cy.get(".vertical").clear().type("130.3 mm");
        cy.get(".translation").clear().type("135.0, 138.0");
        cy.get(".rotation").clear().type("-50.5");
        cy.get('.image-preprocessing-collapsible').click();
        cy.get('[id="img-preprocess-contrast"]').realClick();
        cy.wait(1000)
        cy.get('[id="img-preprocess-brightness"]').realClick({ position: "left" });
        cy.wait(1000)
        cy.get('[id="img-preprocess-sharpen"]').realClick();
        cy.wait(1000)
        cy.get('[id="img-preprocess-gamma"]').realClick({ position: "right" });
        cy.wait(1000)
        cy.get('.crop_top').clear().type('3');
        cy.get('.crop_left').clear().type('2');
        cy.get('.crop_bottom').clear().type('3');
        cy.get('.crop_right').clear().type('2');
        cy.contains('duplicate').click({force:true});
        cy.get('[data-test="working-area-laser-button"]').click();
        cy.wait(2000);
        cy.focusReminder();
        cy.wait(2000);
        cy.get('[data-test="conversion-dialog-material-item"]')
            .contains(/^Foam Rubber$/)
            .click();
        cy.get('[id="material_color_0057a8"]').click();
        cy.wait(1000);
        cy.get('[id="material_thickness_2"]').click();
        cy.get('[data-test="conversion-dialog-intensity-black"]').clear().type("85");
        cy.get('[data-test="conversion-dialog-intensity-white"]').clear().type("25");
        cy.get('[data-test="conversion-dialog-feedrate-white"]').clear().type("700");
        cy.get('[data-test="conversion-dialog-feedrate-black"]').clear().type("1500");
        cy.get('[data-test="conversion-dialog-show-advanced-settings"]').click();
        cy.get('[data-test="conversion-dialog-passes-input-engrave"]').first().clear().type("4");
        cy.get('[data-test="conversion-dialog-engraving-pierce-time"]').clear().type("8");
        cy.get('[data-test="conversion-dialog-line-distance-input"line-distance-input"]').clear().type("1");
        cy.get('[data-test="conversion-dialog-engraving-mode-basic"]').dblclick({ force: true });
        cy.get('[data-test="laser-job-start-button"]').dblclick();
        cy.wait(2000);
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.reload();
        cy.wait(10000);
        cy.get('[data-test="mrbeam-ui-index-design-library"]').click();
        cy.get('[data-test="tab-designbib-filter-gcode-radio"]').click();
        cy.get(".files_template_machinecode_gcode").first().click();
        cy.get('[data-test="working-area-laser-button"]').click();
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.logout();
    });
});
