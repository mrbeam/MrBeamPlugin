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
        cy.get('[data-test="tab-designlib-files-list"]').then(($elem) => {
            if (
                $elem
                    .find('[data-test="tab-designlib-image-preview-card"]')
                    .filter(':contains("mirror.png")').length
            ) {
            } else {
                const filepath = "mirror.png";
                cy.get('.fileinput-button input[type="file"]').attachFile(
                    filepath
                );
                cy.wait(5000);
                cy.get('[data-test="tab-designlib-image-preview-card"]')
                    .contains("mirror.png")
                    .should("to.exist");
            }
        });
        cy.get('[data-test="tab-designlib-image-preview-card"]')
            .filter(':contains("mirror.png")')
            .click();
        cy.wait(3000);
        cy.get('[data-test="tab-workingarea-move"]').click({ force: true });
        cy.get('[data-test="tab-workingarea-scale-prop-btn"]').click();
        cy.get('[data-test="tab-workingarea-horizontal"]')
            .filter(":visible")
            .clear()
            .type("125.3 mm");
        cy.get('[data-test="tab-workingarea-vertical"]')
            .filter(":visible")
            .clear()
            .type("130.3 mm");
        cy.get('[data-test="tab-workingarea-translation"]')
            .filter(":visible")
            .clear()
            .type("135.0, 138.0");
        cy.get('[data-test="tab-workingarea-rotation"]')
            .filter(":visible")
            .clear()
            .type("-50.5");
        cy.get(
            '[data-test="tab-workingarea-image-preprocessing-collapsible"]'
        ).click();
        cy.get(
            '[data-test="tab-workingarea-img-preprocess-contrast"]'
        ).realClick();
        cy.wait(1000);
        cy.get(
            '[data-test="tab-workingarea-img-preprocess-brightness"]'
        ).realClick({ position: "left" });
        cy.wait(1000);
        cy.get(
            '[data-test="tab-workingarea-img-preprocess-sharpen"]'
        ).realClick();
        cy.wait(1000);
        cy.get('[data-test="tab-workingarea-img-preprocess-gamma"]').realClick({
            position: "right",
        });
        cy.wait(1000);
        cy.get('[data-test="tab-workingarea-crop-top"]').clear().type("3");
        cy.get('[data-test="tab-workingarea-crop-left"]').clear().type("2");
        cy.get('[data-test="tab-workingarea-crop-bottom"]').clear().type("3");
        cy.get('[data-test="tab-workingarea-crop-right"]').clear().type("2");
        cy.get('[data-test="tab-workingarea-duplicate"]').click({
            force: true,
        });
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
        cy.get('[data-test="conversion-dialog-intensity-black"]')
            .clear()
            .type("85");
        cy.get('[data-test="conversion-dialog-intensity-white"]')
            .clear()
            .type("25");
        cy.get('[data-test="conversion-dialog-feedrate-white"]')
            .clear()
            .type("700");
        cy.get('[data-test="conversion-dialog-feedrate-black"]')
            .clear()
            .type("1500");
        cy.get(
            '[data-test="conversion-dialog-show-advanced-settings"]'
        ).click();
        cy.get('[data-test="conversion-dialog-passes-input-engrave"]')
            .first()
            .clear()
            .type("4");
        cy.get('[data-test="conversion-dialog-engraving-pierce-time"]')
            .clear()
            .type("8");
        cy.get('[data-test="conversion-dialog-line-distance-input"]')
            .clear()
            .type("1");
        cy.get('[data-test="conversion-dialog-engraving-mode-basic"]').dblclick(
            { force: true }
        );
        cy.get('[data-test="laser-job-start-button"]').dblclick();
        cy.wait(2000);
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.reload();
        cy.wait(10000);
        cy.get('[data-test="mrbeam-ui-index-design-library"]').click();
        cy.get('[data-test="tab-designlib-filter-gcode-radio"]').click();
        cy.get('[data-test="tab-designlib-mechinecode-file"]').first().click();
        cy.get('[data-test="working-area-laser-button"]').click();
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.logout();
    });
});
