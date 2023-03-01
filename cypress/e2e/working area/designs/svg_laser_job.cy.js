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

    it("Add svg file", function () {
        cy.get('[data-test="working-area-tab-file"]').click();
        cy.get('[data-test="tab-designlib-files-list"]').then(($elem) => {
            if (
                $elem
                    .find('[data-test="tab-designlib-svg-preview-card"]')
                    .filter(':contains("Focus_Tool_Mr_Beam_Laser_1.svg")')
                    .length
            ) {
            } else {
                const filepath = "Focus_Tool_Mr_Beam_Laser_1.svg";
                cy.get('.fileinput-button input[type="file"]').attachFile(
                    filepath
                );
                cy.wait(5000);
                cy.get('[data-test="tab-designlib-svg-preview-card"]')
                    .contains("Focus_Tool_Mr_Beam_Laser_1.svg")
                    .should("to.exist");
            }
        });
        cy.get('[data-test="tab-designlib-svg-preview-card"]')
            .filter(':contains("Focus_Tool_Mr_Beam_Laser_1.svg")')
            .click();
        cy.wait(3000);
        cy.get('[data-test="tab-workingarea-translation"]')
            .filter(":visible")
            .clear()
            .type("235.0, 238.0");
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
        cy.get('[data-test="tab-workingarea-burger-menu"]').click();
        cy.get('[data-test="tab-workingarea-by-stroke-color"]').click();
        cy.laserButtonClick();
        cy.selectMaterial();
        cy.downloadGcoFile();
        cy.compareFiles(
            "cypress/fixtures/Focus_Tool_Mr_Beam_Laser_1.svg.5x.gco",
            "cypress/downloads/Focus_Tool_Mr_Beam_Laser_1.svg.5x.gco"
        );
        cy.logout();
    });

    it("Split SVG by every option", function () {
        cy.get('[data-test="working-area-tab-file"]').click();
        cy.get('[data-test="tab-designlib-svg-preview-card"]')
            .filter(':contains("Focus_Tool_Mr_Beam_Laser_1.svg")')
            .click();
        cy.wait(3000);
        cy.get('[data-test="tab-workingarea-burger-menu"]').click();
        cy.get('[data-test="tab-workingarea-vertically"]')
            .filter(":visible")
            .click();
        cy.get('[data-test="tab-workingarea-burger-menu"]').first().click();
        cy.get('[data-test="tab-workingarea-into-shapes"]')
            .filter(":visible")
            .click();
        cy.get('[data-test="tab-workingarea-burger-menu"]').last().click();
        cy.get('[data-test="tab-workingarea-horizontally"]')
            .filter(":visible")
            .click({
                force: true,
            });
        cy.get('[data-test="tab-workingarea-burger-menu"]').eq(10).click();
        cy.get('[data-test="tab-workingarea-by-stroke-color"]')
            .filter(":visible")
            .click({
                force: true,
            });
        cy.get('[data-test="tab-workingarea-detail-information"]').should(
            ($elem) => {
                expect($elem).to.have.length(13);
            }
        );
        cy.logout();
    });
});
