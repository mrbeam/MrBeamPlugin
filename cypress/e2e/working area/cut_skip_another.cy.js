describe("Cut, cut 2, engrave, skip", function () {
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
   
    it('Cut 1, cut 2, engrave, skip', function () {
        cy.get('[data-test="working-area-tab-shapes"]').click();
        cy.get('[data-test="quick-shape-star"]').click(); 
        cy.get('[data-test="quick-shape-color-picker-stroke"]').click();
        cy.get('[data-test="quick-shape-color-picker-stroke"] > .track > canvas').realClick({ position: "top" });
        cy.get('[data-test="quick-shape-fill-input"]').click();
        cy.get('[data-test="quick-shape-color-picker-fill"]').click();
        cy.get('[data-test="quick-shape-color-picker-fill"] > .track > canvas').realClick({ position: "top" }); 
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="working-area-tab-text"]').click();
        cy.get('[data-test="quick-text-modal-text-input"]').type("MrBeam");
        cy.get('[data-test="quick-text-modal-text-cw"]').click();
        cy.get('[data-test="quick-text-color-picker-fill"]').click();
        cy.get('[data-test="quick-text-color-picker-fill"] > .track > canvas').realClick({ position: "top" });
        cy.get('[data-test="quick-text-stroke-input"]').click('center');
        cy.get('[data-test="quick-text-color-picker-stroke"] > .track > canvas').realClick({ position: "left" });
        cy.get('[data-test="quick-text-done-button"]').click();
        cy.get('[data-test="working-area-tab-shapes"]').click();
        cy.get('[data-test="quick-shape-heart"]').click();
        cy.get('[data-test="quick-shape-heart-range"]').realClick({ position: "right" });
        cy.get('[data-test="quick-shape-color-picker-stroke"]').click();
        cy.get('[data-test="quick-shape-color-picker-stroke"] > .track > canvas').realClick({ position: "right" });
        cy.get('[data-test="quick-shape-fill-input"]').click();
        cy.get('[data-test="quick-shape-color-picker-fill"]').click();
        cy.get('[data-test="quick-shape-color-picker-fill"] > .track > canvas').realClick({ position: "top" });
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="working-area-laser-button"]').click();
        cy.get('[data-test="conversion-dialog-material-item"]').contains("Grey Cardboard").click();
        cy.get('[id="material_thickness_1"]').click();
        cy.get('.cutting_job_color').eq(0).trigger('dragstart', {dataTransfer});
        cy.get('#no_job > .span3 > .assigned_colors').trigger('drop', {dataTransfer});
        cy.get('.cutting_job_color').eq(2).trigger('dragstart', {dataTransfer});
        cy.get('[data-bind="visible: show_vector_parameters()"] > .assigned_colors').trigger('drop', {dataTransfer});
        cy.get('[data-test="conversion-dialog-intensity-black"]').clear().type("70");
        cy.get('[data-test="conversion-dialog-intensity-white"]').clear().type("25");
        cy.get('[data-test="conversion-dialog-feedrate-white"]').clear().type("1500");
        cy.get('[data-test="conversion-dialog-feedrate-black"]').clear().type("3000");
        cy.get('[data-test="conversion-dialog-show-advanced-settings"]').click();
        cy.get('[data-test="conversion-dialog-passes-input-engrave"]').first().clear().type("1");
        cy.get('[data-test="conversion-dialog-engraving-pierce-time"]').clear().type("2");
        cy.get('[data-test="conversion-dialog-line-distance-input"]').clear().type("1");
        cy.get('[data-test="conversion-dialog-engraving-mode-basic"]').dblclick({ force: true });
        cy.get('[data-test="conversion-dialog-line-dithering"]').click({ force: true });
        cy.get('[data-test="conversion-dialog-cut-intensity-input"]').first().clear().type("95");
        cy.get('[data-test="conversion-dialog-cut-feedrate-input"]').first().clear().type("1500");
        cy.get('[data-test="conversion-dialog-cut-compressor-input"]').first().realClick({ position: "left" });
        cy.get('[data-test="conversion-dialog-cut-passes-input"]').first().clear().type("3");
        cy.get('[data-test="conversion-dialog-progressive"]').first().click();
        cy.get('[data-test="conversion-dialog-cut-piercetime-input"]').eq(1).clear().type("10");
        cy.get('[data-test="conversion-dialog-cut-intensity-input"]').last().clear().type("95");
        cy.get('[data-test="conversion-dialog-cut-feedrate-input"]').last().clear().type("2500");
        cy.get('[data-test="conversion-dialog-cut-compressor-input"]').last().realClick();
        cy.get('[data-test="conversion-dialog-cut-passes-input"]').last().clear().type("2");
        cy.get('[data-test="conversion-dialog-progressive"]').last().click();
        cy.get('[data-test="conversion-dialog-cut-piercetime-input"]').last().clear().type("15");
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
});