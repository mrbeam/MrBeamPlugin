describe("Navbar icons", function () {
    beforeEach(function () {
        cy.fixture("test-data").then(function (testData) {
            this.testData = testData;
        });
    });

    beforeEach(function () {
        cy.visit(this.testData.url_laser);
        cy.wait(10000);
        cy.loginLaser(this.testData.email, this.testData.password);
        cy.get('[data-test="mrbeam-ui-index-menu-burger"]').click();
        cy.get('[data-test="mrbeam-ui-index-tab-settings"]').click({
            force: true,
        });
    });
    it("DEV", function () {
        cy.get('[id="settings_plugin_mrbeam_dev_design_store_link"]').click();
        cy.get('[id="settings-mrbeam-design-store-environment"]').select("dev");
        cy.get('[data-test="mrbeam-ui-index-design-store"]').find('.red-dot').should('to.visible');
    });

    it("Stage", function () {
        cy.get('[id="settings_plugin_mrbeam_dev_design_store_link"]').click();
        cy.get('[data-test="dev-design-store-env"]').select("staging");
        cy.get('[data-test="mrbeam-ui-index-design-store"]').find('.red-dot').should('to.visible');
    });

    it("Prod", function () {
        cy.get('[id="settings_plugin_mrbeam_dev_design_store_link"]').click();
        cy.get('[data-test="dev-design-store-env"]').select("prod");
        cy.get('[data-test="mrbeam-ui-index-design-store"]').find('.red-dot').should('to.visible');

    });

    it("Localhost", function () {
        cy.get('[id="settings_plugin_mrbeam_dev_design_store_link"]').click();
        cy.get('[data-test="dev-design-store-env"]').select("localhost");
        cy.get('[data-test="mrbeam-ui-index-design-store"]').find('.red-dot').should('to.visible');
    });
    it.only("Email DS", function () {
        cy.get('[id="settings_plugin_mrbeam_dev_design_store_link"]').click();
        cy.get('[data-test="dev-design-store-email"]').clear().type("dev+1@mr-beam.org");
        cy.get('[data-test="mrbeam-ui-index-design-store"]').click();
        cy.get('[data-test="mrbeam-ui-index-menu-burger"]').click();
        cy.get('[data-test="mrbeam-ui-index-tab-settings"]').click({
            force: true,
        });
        cy.get('[id="settings_plugin_mrbeam_dev_design_store_link"]').click();
        cy.get('[data-test="dev-design-store-email"]').invoke('prop', "value").should('to.contain', "dev+1@mr-beam.org")
        cy.get('[data-test="dev-design-store-email"]').clear().type("dev@mr-beam.org");
    });
});
