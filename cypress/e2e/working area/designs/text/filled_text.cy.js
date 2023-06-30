describe.skip("Laser Job - quick text", function () {
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

    // Test quick text filled straight, concave down and concave up
    it("Quick text filled", function () {
        cy.wait(3000);

        // Add 1st design fill text straight
        cy.get('[data-test="working-area-tab-text"]').click();
        cy.get('[data-test="quick-text-modal-text-input"]').type(
            "FilledTextStraight"
        );
        cy.get('[data-test="quick-text-color-picker-fill"]').click();
        cy.get('[data-test="quick-text-modal-text-straight"]').click();
        cy.get('[id="qt_colorPicker_fill"]').click();
        cy.get('[id="qt_colorPicker_fill"] > .track > canvas').realClick({
            position: "top",
        });
        cy.get('[data-test="quick-text-font-button-left"]').last().click();
        cy.get('[data-test="quick-text-done-button"]').click();
        cy.get('[id="translateHandle"]').move({
            deltaX: 433.9689,
            deltaY: 220.1241,
            force: true,
        });
        cy.designSettings();

        // Add 2nd design fill text concave down
        cy.get('[data-test="working-area-tab-text"]').click();
        cy.get('[data-test="quick-text-modal-text-input"]').type(
            "FilledTextConcaveDown"
        );
        cy.get('[data-test="quick-text-modal-text-cw"]').click();
        cy.get('[data-test="quick-text-color-picker-fill"]').click();
        cy.get('[id="qt_colorPicker_fill"]').click();
        cy.get('[id="qt_colorPicker_fill"] > .track > canvas').realClick({
            position: "top",
        });
        cy.get('[data-test="quick-text-circle-input"]').trigger("right");
        cy.get('[data-test="quick-text-font-button-left"]').last().click();
        cy.get('[data-test="quick-text-done-button"]').click();
        cy.get('[id="translateHandle"]').move({
            deltaX: 50.9689,
            deltaY: 220.1241,
            force: true,
        });
        cy.designSettings();

        // Add 3rd design fill text concave up
        cy.get('[data-test="working-area-tab-text"]').click();
        cy.get('[data-test="quick-text-modal-text-input"]').type(
            "FilledTextConcaveUp"
        );
        cy.get('[data-test="quick-text-modal-text-ccw"]').click();
        cy.get('[data-test="quick-text-color-picker-fill"]').click();
        cy.get('[id="qt_colorPicker_fill"]').click();
        cy.get('[id="qt_colorPicker_fill"] > .track > canvas').realClick({
            position: "top",
        });
        cy.get('[data-test="quick-text-circle-input"]').trigger("left");
        cy.get('[data-test="quick-text-font-button-left"]').last().click();
        cy.get('[data-test="quick-text-done-button"]').click();
        cy.get('[id="translateHandle"]').move({
            deltaX: 70.9689,
            deltaY: 80.1241,
            force: true,
        });
        cy.designSettings();

        // Start the laser job
        cy.laserButtonClick();
        cy.selectMaterial();

        // Download the GCODE file and compare it
        cy.downloadGcoFile();
        cy.compareFiles(
            "cypress/fixtures/FilledTextStraight_2more.gco",
            "cypress/downloads/FilledTextStraight_2more.gco"
        );
        cy.logout();
    });

    it("Add text - ok button", function () {
        cy.get('[data-test="working-area-tab-text"]').click();
        cy.get('[data-test="quick-text-modal-window"]').should("to.visible");
        cy.get('[data-test="quick-text-done-button"]').click();
        cy.get('[data-test="quick-text-modal-window"]').should("not.visible");
        cy.logout();
    });
});
