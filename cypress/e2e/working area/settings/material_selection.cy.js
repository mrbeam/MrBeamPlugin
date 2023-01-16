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
    });

    it.skip("Start without set settings", function () {
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.laserButtonClick();
        cy.get('[data-test="laser-job-start-button"]')
            .filter(".disabled")
            .should("to.exist");
        cy.get('[data-test="laser-job-back-button"]').click();
        cy.logout();
    });

    it.skip("Back button", function () {
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.laserButtonClick();
        cy.get('[data-test="conversion-dialog-vector-graphics"]').should(
            "be.visible"
        );
        cy.get('[data-test="laser-job-back-button"]').click();
        cy.get('[data-test="conversion-dialog-vector-graphics"]').should(
            "not.be.visible"
        );
        cy.get('[id="area_preview"]').should("be.visible");
        cy.logout();
    });

    it.skip("Material and back", function () {
        cy.get('[data-test="working-area-tab-shape"]').click({ force: true });
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.laserButtonClick();
        cy.get(7000);
        cy.get('[data-test="conversion-dialog-material-list"]')
            .contains(/^Foam Rubber$/)
            .click();
        cy.wait(2000);
        cy.get(".selected").should(($elem) => {
            expect($elem).to.have.length(1);
            expect($elem).to.be.visible;
        });
        cy.get('[data-test="conversion-dialog-material-list"]')
            .contains(/^Foam Rubber$/)
            .click();
        cy.wait(2000);
        cy.get(
            '[data-test="conversion-dialog-material-list"] > [data-test="conversion-dialog-material-item"]'
        ).should(($elem) => {
            expect($elem).to.have.length.greaterThan(1);
            expect($elem).to.be.visible;
        });
        cy.get('[data-test="laser-job-back-button"]').click();
        cy.logout();
    });

    it.skip("Color and back", function () {
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.laserButtonClick();
        cy.get(7000);
        cy.get('[data-test="conversion-dialog-material-item"]')
            .contains(/^Foam Rubber$/)
            .click();
        cy.get('[id="material_color_0057a8"]').click();
        cy.wait(2000);
        cy.get('[data-test="conversion-dialog-material-color"]')
            .filter(":visible")
            .should(($elem) => {
                expect($elem).to.have.length(1);
                expect($elem).to.be.visible;
            });
        cy.get('[id="material_color_0057a8"]').click();
        cy.wait(2000);
        cy.get('[data-test="conversion-dialog-material-color"]')
            .filter(":visible")
            .should(($elem) => {
                expect($elem).to.have.length.greaterThan(1);
                expect($elem).to.be.visible;
            });
        cy.get('[data-test="laser-job-back-button"]').click();
        cy.logout();
    });

    it.skip("Thickness and back", function () {
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.laserButtonClick();
        cy.get(7000);
        cy.get('[data-test="conversion-dialog-material-item"]')
            .contains(/^Foam Rubber$/)
            .click();
        cy.get('[id="material_color_0057a8"]').click();
        cy.wait(1000);
        cy.get('[id="material_thickness_2"]').click();
        cy.wait(2000);
        cy.get('[data-test="conversion-dialog-thickness-sample"]')
            .filter(":visible")
            .should(($elem) => {
                expect($elem).to.have.length(1);
                expect($elem).to.be.visible;
            });
        cy.get('[id="material_thickness_2"]').click();
        cy.wait(2000);
        cy.get('[data-test="conversion-dialog-thickness-sample"]')
            .filter(":visible")
            .should(($elem) => {
                expect($elem).to.have.length.greaterThan(1);
                expect($elem).to.be.visible;
            });
        cy.get('[data-test="laser-job-back-button"]').click();
        cy.logout();
    });

    it.skip("Help", function () {
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.laserButtonClick();
        cy.get(7000);
        cy.get('[data-test="conversion-dialog-material-item"]')
            .contains(/^Foam Rubber$/)
            .click();
        cy.get('[id="material_color_0057a8"]').click({ force: true });
        cy.get("#material_thickness_2").click({ force: true });
        cy.get('[data-test="conversion-dialog-help"]')
            .click({ force: true })
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.get('[data-test="laser-job-back-button"]').click();
        cy.logout();
    });

    it.skip("Manage materials", function () {
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.laserButtonClick();
        cy.get(7000);
        cy.get('[data-test="custom-material-materials-manage"]').click();
        cy.get('[data-test="custom-material-done"]').should("be.visible");
        cy.get('[data-test="custom-material-materials-manage"]').should(
            "not.be.visible"
        );
        cy.get('[data-test="custom-material-learn-how"]')
            .filter(":visible")
            .click({ force: true })
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.get('[data-test="custom-material-done"]').click();
        cy.get('[data-test="laser-job-back-button"]').click();
        cy.logout();
    });
});
