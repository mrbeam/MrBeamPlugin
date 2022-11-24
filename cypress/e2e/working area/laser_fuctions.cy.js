describe("Functionalities", function () {

    beforeEach(function () {
        cy.fixture("test-data").then(function (testData) {
            this.testData = testData;
        });
    });

    beforeEach(function () {
        cy.visit(this.testData.url_laser);
        cy.wait(10000);
        cy.loginLaser(this.testData.email, this.testData.password);
        cy.visit(this.testData.url_laser);
        cy.reload();
        cy.visit(this.testData.url_laser);
        cy.get('.icon-remove').click({ force: true, multiple: true });
    });

    it('Start without set settings', function () {
        cy.get('[data-test="working-area-tab-shapes"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="working-area-laser-button"]').click();
        cy.get('[data-test="laser-job-start-button"]').filter('.disabled').should('to.exist');
        cy.get('[data-test="laser-job-start-button"]').click();
        cy.logout();
    });

    it('Back button', function () {
        cy.get('[data-test="working-area-tab-shapes"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="working-area-laser-button"]').click();
        cy.get('[id="dialog_vector_graphics_conversion"]').should('be.visible');
        cy.get('[data-test="laser-job-start-button"]').click();
        cy.get('[id="dialog_vector_graphics_conversion"]').should('not.be.visible');
        cy.get('[id="area_preview"]').should('be.visible');
        cy.logout();
    });

    it.only('Material and back', function () {
        cy.get('[data-test="working-area-tab-shapes"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="working-area-laser-button"]').click();
        cy.get(7000);
        cy.get('[data-test="conversion-dialog-material-list"]')
            .contains(/^Foam Rubber$/)
            .click();
        cy.wait(2000)
        cy.get('[data-test="conversion-dialog-material-item"] .selected').should(($elem) => {
            expect($elem).to.have.length(1);
            expect($elem).to.be.visible;
        });
        cy.get('[data-test="conversion-dialog-material-list"]')
            .contains(/^Foam Rubber$/)
            .click();
        cy.wait(2000)
        cy.get('[data-test="conversion-dialog-material-list"] > [data-test="conversion-dialog-material-item"]').should(($elem) => {
            expect($elem).to.have.length(22);
            expect($elem).to.be.visible;
        });
        cy.get('[data-test="laser-job-start-button"]').click();
        cy.logout();
    });

    it('Color and back', function () {
        cy.get('[data-test="working-area-tab-shapes"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="working-area-laser-button"]').click();
        cy.get(7000);
        cy.get('[data-test="conversion-dialog-material-item"]')
            .contains(/^Foam Rubber$/)
            .click();
        cy.get('[id="material_color_0057a8"]').click();
        cy.wait(2000)
        cy.get('[data-test="conversion-dialog-material-color"]').filter(':visible').should(($elem) => {
            expect($elem).to.have.length(1);
            expect($elem).to.be.visible;
        });
        cy.get('[id="material_color_0057a8"]').click();
        cy.wait(2000)
        cy.get('[data-test="conversion-dialog-material-color"]').filter(':visible').should(($elem) => {
            expect($elem).to.have.length(5);
            expect($elem).to.be.visible;
        });
        cy.get('[data-test="laser-job-start-button"]').click();
        cy.logout();
    });

    it('Thinknees and back', function () {
        cy.get('[data-test="working-area-tab-shapes"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="working-area-laser-button"]').click();
        cy.get(7000);
        cy.get('[data-test="conversion-dialog-material-item"]')
            .contains(/^Foam Rubber$/)
            .click();
        cy.get('[id="material_color_0057a8"]').click();
        cy.wait(1000);
        cy.get('[id="material_thickness_2"]').click();
        cy.wait(2000)
        cy.get('[data-test="conversion-dialog-thickness-sample"]').filter(':visible').should(($elem) => {
            expect($elem).to.have.length(1);
            expect($elem).to.be.visible;
        });
        cy.get('[id="material_thickness_2"]').click();
        cy.wait(2000)
        cy.get('[data-test="conversion-dialog-thickness-sample"]').filter(':visible').should(($elem) => {
            expect($elem).to.have.length(3);
            expect($elem).to.be.visible;
        });
        cy.get('[data-test="laser-job-start-button"]').click();
        cy.logout();
    });

    it('Help', function () {
        cy.get('[data-test="working-area-tab-shapes"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="working-area-laser-button"]').click();
        cy.get(7000);
        cy.get('[data-test="conversion-dialog-material-item"]')
            .contains(/^Foam Rubber$/)
            .click();
        cy.get('[id="material_color_0057a8"]').click();
        cy.get('[data-test="conversion-dialog-help"]').click();
    });

    it('Manage materials', function () {
        cy.get('[data-test="working-area-tab-shapes"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="working-area-laser-button"]').click();
        cy.get(7000);
        cy.get('[data-test="custom-material-materials-manage"]').click();
        cy.get('[data-test="custom-material-done"]').should('be.visible');
        cy.get('[data-test="custom-material-materials-manage"]').should('not.be.visible');
        cy.get('[data-test="custom-material-learn-how"]').click();
        cy.get('[data-test="custom-material-done"]').click();
        cy.get('[data-test="laser-job-start-button"]').click();
        cy.logout();
    });
});