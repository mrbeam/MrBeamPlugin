describe("Laser Job - shapes star", function () {
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

    it("Star shape", function () {
        // Add star-shaped design
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-star-radius-input"]')
            .clear()
            .type("60");
        cy.get('[data-test="quick-shape-star-corners-input"]')
            .clear()
            .type("8");
        cy.get('[data-test="quick-shape-star-sharpness-input"]').realClick();
        cy.fillAndStroke();
        cy.designSettings();

        // Start the laser job
        cy.laserButtonClick();
        cy.selectMaterial();

        // Download the GCODE file and compare it
        cy.downloadGcoFile();
        cy.compareFiles(
            "cypress/fixtures/Star.gco",
            "cypress/downloads/Star.gco"
        );
        cy.logout();
    });

    it("Add shapes - ok button", function () {
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-modal-window"]').should("to.visible");
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="quick-shape-modal-window"]').should("not.visible");
    });
});
