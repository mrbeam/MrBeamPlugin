describe("Functionalities", function () {
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
    it.skip("Scroll to zoom", function () {
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
});
