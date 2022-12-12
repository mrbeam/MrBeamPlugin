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

    it("Object height - slidebar", function () {
        cy.get('[data-test="tab-workingarea-object-height-input"]')
            .invoke("prop", "value")
            .should("eq", "0");
        cy.get('[data-test="tab-workingarea-object-height-input"]').type(
            "30{enter}"
        );
        cy.get('[data-test="tab-workingarea-object-height-input"]')
            .invoke("prop", "value")
            .should("not.eq", "0");
        cy.logout();
    });

    it("Object height - input", function () {
        cy.get('[data-test="tab-workingarea-object-height-input"]')
            .invoke("prop", "value")
            .should("eq", "0");
        cy.get('[data-test="tab-workingarea-object-height-slider"]').realClick({
            position: "right",
        });
        cy.get('[data-test="tab-workingarea-object-height-input"]')
            .invoke("prop", "value")
            .should("not.eq", "0");
        cy.logout();
    });

    it("Preview - brightness", function () {
        cy.get('[data-test="tab-workingarea-preview-settings"]').click();
        cy.wait(2000);
        cy.get('[data-test="tab-workingarea-preview-brightness"]').realClick({
            position: "left",
        });
        cy.logout();
    });
    // to fix scroll to zoom
    it("Scroll to zoom", function () {
        cy.get('[data-test="tab-workingarea-preview-settings"]').click();
        cy.get('[data-test="tab-workingarea-preview-zoom"]')
            .invoke("prop", "textContent")
            .should("eq", "");
        cy.get('[data-test="tab-workingarea-preview-scroll-to-zoom"]')
            .trigger("mousemove")
            .trigger("wheel", {
                deltaY: -66.666666,
                wheelDelta: 120,
                wheelDeltaX: 0,
                wheelDeltaY: 120,
                bubbles: true,
            });
        cy.get('[data-test="tab-workingarea-preview-zoom"]')
            .invoke("prop", "textContent")
            .should("not.eq", "");
        cy.logout();
    });

    it("Start without set settings", function () {
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="working-area-laser-button"]').click();
        cy.get('[data-test="laser-job-start-button"]')
            .filter(".disabled")
            .should("to.exist");
        cy.get('[data-test="laser-job-back-button"]').click();
        cy.logout();
    });

    it("Back button", function () {
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="working-area-laser-button"]').click();
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

    it("Material and back", function () {
        cy.get('[data-test="working-area-tab-shape"]').click({ force: true });
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="working-area-laser-button"]').click();
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
            expect($elem).to.have.length(22);
            expect($elem).to.be.visible;
        });
        cy.get('[data-test="laser-job-back-button"]').click();
        cy.logout();
    });

    it("Color and back", function () {
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="working-area-laser-button"]').click();
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
                expect($elem).to.have.length(5);
                expect($elem).to.be.visible;
            });
        cy.get('[data-test="laser-job-back-button"]').click();
        cy.logout();
    });

    it("Thinknees and back", function () {
        cy.get('[data-test="working-area-tab-shape"]').click();
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
                expect($elem).to.have.length(3);
                expect($elem).to.be.visible;
            });
        cy.get('[data-test="laser-job-back-button"]').click();
        cy.logout();
    });

    it("Help", function () {
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="working-area-laser-button"]').click();
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

    it("Manage materials", function () {
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="working-area-laser-button"]').click();
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
