describe.skip("Cut and engrave", function () {
    const dataTransfer = new DataTransfer();

    beforeEach(function () {
        cy.fixture("test-data").then(function (testData) {
            this.testData = testData;
        });
    });

    beforeEach(function () {
        cy.visit(this.testData.url_laser);
        cy.get('[id="loading_overlay"]', { timeout: 20000 }).should(
            "not.be.visible"
        );
        cy.loginLaser(this.testData.email, this.testData.password);
        cy.visit(this.testData.url_laser);
        cy.deleteDownloadsFolder();
        cy.deleteGcoFile();
    });

    it.skip("Cut and engrave", function () {
        //Adding star
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
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
        //Adding file jpg
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
        cy.get('[data-test="working-area-tab-file"]').click();
        cy.get('[data-test="tab-designlib-image-preview-card"]')
            .filter(':contains("paris2.jpg")')
            .click();
        cy.laserButtonClick();
        //adding select material
        cy.get('[data-test="conversion-dialog-material-item"]')
            .contains("Finn Cardboard")
            .click();
        cy.get('[id="material_thickness_1.5"]').click();
        cy.get('[data-test="conversion-dialog-intensity-black"]')
            .clear()
            .type("70");
        cy.get('[data-test="conversion-dialog-intensity-white"]')
            .clear()
            .type("25");
        cy.get('[data-test="conversion-dialog-feedrate-white"]')
            .clear()
            .type("1500");
        cy.get('[data-test="conversion-dialog-feedrate-black"]')
            .clear()
            .type("3000");
        cy.get(
            '[data-test="conversion-dialog-show-advanced-settings"]'
        ).click();
        cy.get('[data-test="conversion-dialog-passes-input-engrave"]')
            .first()
            .clear()
            .type("1");
        cy.get('[data-test="conversion-dialog-engraving-pierce-time"]')
            .clear()
            .type("2");
        cy.get('[data-test="conversion-dialog-line-distance-input"]')
            .clear()
            .type("1");
        cy.get('[data-test="conversion-dialog-engraving-mode-basic"]').dblclick(
            { force: true }
        );
        cy.get('[data-test="conversion-dialog-line-dithering"]').click({
            force: true,
        });
        cy.get('[data-test="conversion-dialog-cut-intensity-input"]')
            .clear()
            .type("95");
        cy.get('[data-test="conversion-dialog-cut-feedrate-input"]')
            .clear()
            .type("1500");
        cy.get(
            '[data-test="conversion-dialog-cut-compressor-input"]'
        ).realClick({ position: "left" });
        cy.get('[data-test="conversion-dialog-cut-passes-input"]')
            .clear()
            .type("3");
        cy.get('[data-test="conversion-dialog-progressive"]').click();
        cy.get('[data-test="conversion-dialog-cut-piercetime-input"]')
            .last()
            .clear()
            .type("10");
        cy.downloadGcoFile();
        cy.compareFiles(
            "cypress/fixtures/Star_1more.gco",
            "cypress/downloads/Star_1more.gco"
        );
        cy.logout();
    });

    it.skip("Skip", function () {
        //Adding star
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.laserButtonClick();
        cy.get('[data-test="conversion-dialog-material-item"]')
            .contains("Finn Cardboard")
            .click();
        cy.get('[id="material_thickness_1.5"]').click();
        cy.get(".cutting_job_color")
            .eq(0)
            .trigger("dragstart", { dataTransfer });
        cy.get('[data-test="conversion-dialog-no-job"]').trigger("drop", {
            dataTransfer,
        });
        cy.get('[data-test="laser-job-start-button"]').dblclick({
            force: true,
        });
        cy.get(
            '[data-test="conversion-dialog-settings-to-be-adjusted"]'
        ).should("to.exist");
        cy.get(
            '[data-test="conversion-dialog-settings-to-be-adjusted-btn"]'
        ).dblclick({ force: true });
        cy.get(
            '[data-test="conversion-dialog-settings-to-be-adjusted"]'
        ).should("not.visible");
        cy.get('[data-test="conversion-dialog-vector-graphics"]').should(
            "to.exist"
        );
        cy.get('[data-test="laser-job-back-button"]').click({ force: true });
        cy.logout();
    });

    it.skip("Engrave move to cut", function () {
        //Adding text
        cy.get('[data-test="working-area-tab-text"]').click();
        cy.get('[data-test="quick-text-modal-text-input"]').type("MrBeam");
        cy.get('[data-test="quick-text-done-button"]').click();
        //Adding text
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.laserButtonClick();
        cy.get('[data-test="conversion-dialog-material-item"]')
            .contains("Finn Cardboard")
            .click();
        cy.get('[id="material_thickness_1.5"]').click();
        cy.get('[id="cd_engraving"]')
            .eq(0)
            .trigger("dragstart", { dataTransfer });
        cy.get("#first_job > .span3 > .assigned_colors").trigger("drop", {
            dataTransfer,
        });
        cy.get("#first_job > .span3 > .assigned_colors")
            .find('[id="cd_engraving"]')
            .should("not.exist");
        cy.get('[data-test="conversion-dialog-engrave-job-zone"]')
            .find('[id="cd_engraving"]')
            .should("to.exist");
        cy.get('[data-test="laser-job-back-button"]').click({ force: true });
        cy.logout();
    });
});
