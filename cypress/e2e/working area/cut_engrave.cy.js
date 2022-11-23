describe("Cut and engrave", function () {

    const dataTransfer = new DataTransfer();

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

    it('Cut and engrave', function () {
        cy.get('[data-test="working-area-tab-shapes"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-color-picker-stroke"]').click();
        cy.get('[data-test="quick-shape-color-picker-stroke"] > .track > canvas').realClick({ position: "top" });
        cy.get('[data-test="quick-shape-fill-input"]').click();
        cy.get('[data-test="quick-shape-color-picker-fill"]').click();
        cy.get('[data-test="quick-shape-color-picker-fill"] > .track > canvas').realClick({ position: "top" });
        cy.get('[data-test="quick-shape-done-button"ton"]').click();
        cy.get('[data-test="working-area-tab-file"]').click();
        cy.get(".files_template_model_image")
            .filter(':contains("paris2.jpg")')
            .click();
        cy.get('[data-test="working-area-laser-button"]').click();
        cy.get('[data-test="conversion-dialog-material-item"]').contains("Finn Cardboard").click();
        cy.get('[id="material_thickness_1.5"]').click();
        cy.get('.cutting_job_color').trigger('dragstart', { dataTransfer });
        cy.get('[data-test="conversion-dialog-engrave-job-zone"]').trigger('drop', { dataTransfer });
        cy.get('[data-test="conversion-dialog-intensity-black"ity-black"]').clear().type("70");
        cy.get('[data-test="conversion-dialog-intensity-white"]').clear().type("25");
        cy.get('[data-test="conversion-dialog-feedrate-white"]').clear().type("1500");
        cy.get('[data-test="conversion-dialog-feedrate-black"ate-black"]').clear().type("3000");
        cy.get('[data-test="conversion-dialog-show-advanced-settings"]').click();
        cy.get('[data-test="conversion-dialog-passes-input-engrave"]').first().clear().type("1");
        cy.get('[data-test="conversion-dialog-engraving-pierce-time"]').clear().type("2");
        cy.get('[data-test="conversion-dialog-line-distance-input"]').clear().type("1");
        cy.get('[data-test="conversion-dialog-engraving-mode-basic"]').dblclick({ force: true });
        cy.get('[data-test="conversion-dialog-line-dithering"]').click({ force: true });
        cy.get('[data-test="conversion-dialog-cut-intensity-input"]').clear().type("95");
        cy.get('[data-test="conversion-dialog-cut-feedrate-input"]').clear().type("1500");
        cy.get('[data-test="conversion-dialog-cut-compressor-input"]').realClick({ position: "left" });
        cy.get('[data-test="conversion-dialog-cut-passes-input"]').clear().type("3");
        cy.get('[data-test="conversion-dialog-progressive"]').click();
        cy.get('[data-test="conversion-dialog-cut-piercetime-input"]').last().clear().type("10");
        cy.get('[data-test="laser-job-start-button"]').dblclick();
        cy.wait(7000);
        cy.reload();
        cy.wait(10000);
        cy.get('[data-test="mrbeam-ui-index-design-library"]').click();
        cy.get('[data-test="tab-designbib-filter-gcode-radio"]').click();
        cy.get(".files_template_machinecode_gcode").first().click();
        cy.get('[data-test="working-area-laser-button"]').click();
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.logout();
    });

    it.only('Skip', function () {
        cy.get('[data-test="working-area-tab-shapes"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="working-area-laser-button"]').click();
        cy.get('[data-test="conversion-dialog-material-item"]').contains("Finn Cardboard").click();
        cy.get('[id="material_thickness_1.5"]').click();
        cy.get('.cutting_job_color').eq(0).trigger('dragstart', {dataTransfer});
        cy.get('#no_job > .span3 > .assigned_colors').trigger('drop', {dataTransfer});
        cy.get('[data-test="laser-job-start-button"]').dblclick({force:true});
        cy.get('[data-test="conversion-dialog-settings-to-be-adjusted"]').should('to.exist');
        cy.get('[data-test="conversion-dialog-settings-to-be-adjusted-btn"]').click({force:true});
        cy.get('[data-test="laser-job-start-button"]').click({force:true});
        cy.logout();
    });
});