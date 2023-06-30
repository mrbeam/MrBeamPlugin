describe.skip("Laser Job", function () {
    beforeEach(function () {
        cy.fixture("test-data").then(function (testData) {
            this.testData = testData;
        });
    });

    beforeEach(function () {
        cy.visit(this.testData.url);
        cy.get('[id="loading_overlay"]', { timeout: 20000 }).should(
            "not.be.visible"
        );
        cy.loginLaser(this.testData.email, this.testData.password);
        cy.deleteDownloadsFolder();
        cy.deleteGcoFile();
    });

    it("Add design", function () {
        cy.get('[data-test="working-area-tab-file"]').click();
        cy.get('[data-test="tab-designlib-files-list"]').then(($elem) => {
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
        cy.get('[data-test="tab-workingarea-horizontal"]')
            .filter(":visible")
            .clear()
            .type("95.3 mm");
        cy.get('[data-test="tab-workingarea-vertical"]')
            .filter(":visible")
            .clear()
            .type("70.3 mm");
        cy.get(".userIMG").click({ force: true });
        cy.get('[id="translateHandle"]').move({
            deltaX: 213.9689,
            deltaY: -144.1241,
            force: true,
        });
        cy.get('[data-test="tab-workingarea-rotation"]')
            .filter(":visible")
            .clear()
            .type("200.5");
        cy.get('[data-test="tab-workingarea-multiply"]')
            .clear()
            .type("2x3{enter}");
        cy.get('[data-test="tab-workingarea-mirror-switch"]').click();
        // image preprocessing
        cy.get(
            '[data-test="tab-workingarea-image-preprocessing-collapsible"]'
        ).click();
        //preprocess img
        cy.get(
            '[data-test="tab-workingarea-img-preprocess-contrast"]'
        ).realClick({ position: "left" });
        cy.wait(1000);
        cy.get(
            '[data-test="tab-workingarea-img-preprocess-brightness"]'
        ).realClick({ position: "right" });
        cy.wait(1000);
        cy.get(
            '[data-test="tab-workingarea-img-preprocess-sharpen"]'
        ).realClick({ position: "right" });
        cy.wait(1000);
        cy.get('[data-test="tab-workingarea-img-preprocess-gamma"]').realClick({
            position: "left",
        });
        cy.wait(1000);
        //crop
        cy.get('[data-test="tab-workingarea-crop-top"]').clear().type("2");
        cy.get('[data-test="tab-workingarea-crop-left"]').clear().type("2");
        cy.get('[data-test="tab-workingarea-crop-bottom"]').clear().type("2");
        cy.get('[data-test="tab-workingarea-crop-right"]').clear().type("2");
        cy.laserButtonClick();
        cy.selectMaterial();
        cy.downloadGcoFile();
        cy.compareFiles(
            "cypress/fixtures/paris2.gco",
            "cypress/downloads/paris2.gco"
        );
        cy.logout();
    });
});
