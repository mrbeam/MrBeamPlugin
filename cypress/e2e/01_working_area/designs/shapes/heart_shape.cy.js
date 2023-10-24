describe("Laser Job - shapes heart", function () {
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

    it("Heart shape", function () {
        // Add heart-shaped design
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-Heart"]').click();
        cy.get('[data-test="quick-shape-heart-width"]').clear().type("60");
        cy.get('[data-test="quick-shape-heart-height"]').clear().type("80");
        cy.get('[data-test="quick-shape-heart-range"]').realClick({
            position: "right",
        });
        cy.fillAndStroke();
        cy.designSettings();

        // Start the laser job
        cy.laserButtonClick();
        cy.selectMaterial();

        // Download the GCODE file and compare it
        cy.downloadGcoFile();
        cy.compareFiles(
            "cypress/fixtures/Heart.gco",
            "cypress/downloads/Heart.gco"
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
