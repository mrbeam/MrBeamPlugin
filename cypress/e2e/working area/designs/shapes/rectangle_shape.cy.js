describe("Laser Job - shapes rectangle", function () {
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

    it("Rectangle shape", function () {
        // Add rectangle-shaped design
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-rect"]').click();
        cy.get('[data-test="quick-shape-rect-width"]').clear().type("60");
        cy.get('[data-test="quick-shape-rect-height"]').clear().type("60");
        //cy.get('[data-test="quick-shape-rect-radius-input"]').realClick();
        cy.fillAndStroke();
        cy.designSettings();
        // Start the laser job
        cy.laserButtonClick();
        cy.selectMaterial();
        // Download the GCODE file and compare it
        cy.downloadGcoFile();
        cy.compareFiles(
            "cypress/fixtures/Rectangle.gco",
            "cypress/downloads/Rectangle.gco"
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
