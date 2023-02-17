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

    it("Make me fit", function () {
        cy.get('[data-test="working-area-tab-file"]').click();
        cy.get('[data-test="tab-designlib-svg-preview-card"]').then(($elem) => {
            if (
                $elem
                    .find('[data-test="tab-designlib-svg-preview-card"]')
                    .filter(':contains("black_cat.svg")').length
            ) {
            } else {
                const filepath = "black_cat.svg";
                cy.get('.fileinput-button input[type="file"]').attachFile(
                    filepath
                );
                cy.wait(5000);
                cy.get('[data-test="tab-designlib-svg-preview-card"]')
                    .contains("black_cat.svg")
                    .should("to.exist");
            }
        });
        cy.get('[data-test="tab-designlib-svg-preview-card"]')
            .filter(':contains("black_cat.svg")')
            .click();
        cy.wait(3000);
        cy.get('[data-test="tab-workingarea-make-me-fit-svg"]').realClick();
        cy.get('[data-test="tab-workingarea-make-me-fit-svg"]').realClick();
        cy.get('[data-test="tab-workingarea-make-me-fit-svg"]').should(
            "not.visible"
        );
        cy.logout();
    });

    it("Edit", function () {
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="tab-workingarea-collapse-in"]')
            .contains("Rectangle")
            .should("to.exist");
        cy.wait(2000);
        cy.get('[data-test="tab-workingarea-edit"]').click({ force: true });
        cy.get('[data-test="quick-shape-modal-window"]').should("to.visible");
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-star-radius-input"]')
            .clear()
            .type("60");
        cy.get('[data-test="quick-shape-star-corners-input"]')
            .clear()
            .type("8");
        cy.get('[data-test="quick-shape-star-sharpness-input"]').realClick();
        cy.get('[data-test="quick-shape-color-picker-stroke"]').click();
        cy.get(
            '[data-test="quick-shape-color-picker-stroke"] > .track > canvas'
        ).realClick({ position: "top" });
        cy.get('[data-test="quick-shape-fill-input"]').click();
        cy.get('[data-test="quick-shape-color-picker-fill"]').click();
        cy.get(
            '[data-test="quick-shape-color-picker-fill"] > .track > canvas'
        ).realClick({ position: "top" });
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="tab-workingarea-collapse-in"]')
            .contains("Star")
            .should("to.exist");
    });

    it("Clear all", function () {
        cy.get('[data-test="tab-workingarea-collapse-in"]')
            .contains(".file_list_entry")
            .should("not.exist");
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="tab-workingarea-collapse-in"]')
            .contains("Rectangle")
            .should("to.exist");
        cy.wait(2000);
        cy.get('[data-test="working-area-tab-file"]').click();
        cy.get('[data-test="tab-designlib-svg-preview-card"]').first().click();
        cy.get('[data-test="working-area-tab-text"]').click();
        cy.get('[data-test="quick-text-modal-text-input"]').type("MrBeam");
        cy.get('[data-test="quick-text-done-button"]').click();
        cy.get('[data-test="tab-workingarea-collapse-in"]')
            .find(".file_list_entry")
            .should("to.exist");
        cy.get('[data-test="tab-workingarea-clear-wa"]').click();
        cy.get('[data-test="tab-workingarea-collapse-in"]')
            .contains(".file_list_entry")
            .should("not.exist");
    });

    it("Reset and remove", function () {
        cy.get('[data-test="working-area-tab-file"]').click();
        cy.get('[data-test="tab-designlib-svg-preview-card"]').then(($elem) => {
            if (
                $elem
                    .find('[data-test="tab-designlib-image-preview-card"]')
                    .filter(':contains("paris2.jpg")').length
            ) {
            } else {
                const filepath = "paris2.jpg";
                cy.get('.fileinput-button input[type="file"]').attachFile(
                    filepath
                );
                cy.wait(5000);
                cy.get('[data-test="tab-designlib-image-preview-card"]')
                    .contains("paris2.jpg")
                    .should("to.exist");
            }
        });
        cy.get('[data-test="tab-designlib-image-preview-card"]')
            .filter(':contains("paris2.jpg")')
            .click();
        cy.wait(3000);
        cy.get('[data-test="tab-workingarea-multiply"]').clear().type("2x3");
        cy.get(".userIMG").click({ force: true });
        cy.get('[id="translateHandle"]').move({
            deltaX: 213.9689,
            deltaY: -144.1241,
            force: true,
        });
        cy.get('[data-test="tab-workingarea-rotation"]')
            .filter(":visible")
            .clear()
            .type("250.5");
        cy.get('[data-test="tab-workingarea-horizontal"]')
            .filter(":visible")
            .clear()
            .type("225.3 mm");
        cy.get('[data-test="tab-workingarea-vertical"]')
            .filter(":visible")
            .clear()
            .type("230.3 mm");
        cy.get('[data-test="tab-workingarea-undo"]').click({ force: true });
        cy.wait(2000);
        cy.get('[data-test="tab-workingarea-remove"]').click({ force: true });
        cy.get('[data-test="tab-workingarea-collapse-in"]')
            .contains(".file_list_entry")
            .should("not.exist");
        cy.logout();
    });
});
