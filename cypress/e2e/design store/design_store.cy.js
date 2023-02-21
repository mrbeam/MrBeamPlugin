// skip all design store tests as the store is showing incompatible version screen in docker image
describe.skip("Purchase", function () {
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
        cy.loginDesignStore(
            this.testData.email,
            this.testData.password,
            this.testData.verify_code
        );
    });

    it("Buy design - success", function () {
        cy.wait(3000);
        cy.iframe('[id="design_store_iframe"]').then(($button) => {
            cy.get($button)
                .find('[src="static/img/beam_coin_orange.png"]')
                .first()
                .click({ force: true });
        });
        cy.iframe('[id="design_store_iframe"]').contains("Confirm").click();
        cy.iframe('[id="design_store_iframe"]')
            .find(".buy-now")
            .first()
            .click();
        cy.wait(3000);
        cy.iframe('[id="design_store_iframe"]').then(($button) => {
            cy.get($button)
                .find(".icon-download-alt")
                .last()
                .click({ force: true });
        });
        cy.iframe('[id="design_store_iframe"]')
            .find(".view-in-library")
            .last()
            .should("to.exist");
        cy.logout();
    });

    it("Buy design - failed", function () {
        cy.iframe('[id="design_store_iframe"]')
            .find('[id="price_desc"]')
            .click();
        cy.iframe('[id="design_store_iframe"]').then(($button) => {
            cy.get($button)
                .find('[id="25_purchase_btn"]')
                .click({ force: true });
        });
        cy.iframe('[id="design_store_iframe"]').contains("Confirm").click();
        cy.iframe('[id="design_store_iframe"]').find(".buy-now").click();
        cy.get(".alert-error").should("to.exist");
        cy.logout();
    });

    it("Download design", function () {
        cy.iframe('[id="design_store_iframe"]')
            .find(".btn-go-to-purchases-page")
            .click();
        cy.wait(2000);
        cy.iframe('[id="design_store_iframe"]').then(($button) => {
            cy.get($button)
                .find(".icon-download-alt")
                .each(($elem) => {
                    const item = cy.wrap($elem);
                    item.click({ force: true });
                });
        });
        cy.wait(3000);
        cy.iframe('[id="design_store_iframe"]')
            .find(".view-in-library")
            .should("to.exist");
        cy.logout();
    });
});
