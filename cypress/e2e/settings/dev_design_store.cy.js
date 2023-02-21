describe("Navbar icons", function () {
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
        cy.get('[data-test="mrbeam-ui-index-menu-burger"]').click();
        cy.get('[data-test="mrbeam-ui-index-tab-settings"]').click({
            force: true,
        });
    });
    it("DEV", function () {
        cy.get('[id="settings_plugin_mrbeam_dev_design_store_link"]').click();
        cy.get('[id="settings-mrbeam-design-store-environment"]').select("dev");
        cy.get('[data-test="mrbeam-ui-index-design-store"]').click();
        cy.get('[id="design_store_iframe"]')
            .invoke("prop", "src")
            .should(
                "include",
                "https://1-1-0-dev-dot-design-store-269610.appspot.com"
            );
    });
    it("Prod", function () {
        cy.get('[id="settings_plugin_mrbeam_dev_design_store_link"]').click();
        cy.get('[data-test="dev-design-store-env"]').select("prod");
        cy.get('[data-test="mrbeam-ui-index-design-store"]').click();
        cy.get('[id="design_store_iframe"]')
            .invoke("prop", "src")
            .should("include", "https://designs.cloud.mr-beam.org");
    });

    it("Localhost", function () {
        cy.get('[id="settings_plugin_mrbeam_dev_design_store_link"]').click();
        cy.get('[data-test="dev-design-store-env"]').select("localhost");
        cy.get('[data-test="mrbeam-ui-index-design-store"]').click();
        cy.get('[id="design_store_iframe"]')
            .invoke("prop", "src")
            .should("include", "http://localhost:8080/");
    });
    it("Stage", function () {
        cy.get('[id="settings_plugin_mrbeam_dev_design_store_link"]').click();
        cy.get('[data-test="dev-design-store-env"]').select("staging");
        cy.get('[data-test="mrbeam-ui-index-design-store"]').click();
        cy.get('[id="design_store_iframe"]')
            .invoke("prop", "src")
            .should(
                "include",
                "https://1-1-0-staging-dot-design-store-269610.appspot.com"
            );
    });
    it("Email DS", function () {
        cy.get('[id="settings_plugin_mrbeam_dev_design_store_link"]').click();
        cy.get('[data-test="dev-design-store-email"]')
            .clear()
            .type("dev+1@mr-beam.org");
        cy.get('[data-test="mrbeam-ui-index-design-store"]').click();
        cy.get('[data-test="mrbeam-ui-index-menu-burger"]').click();
        cy.get('[data-test="mrbeam-ui-index-tab-settings"]').click({
            force: true,
        });
        cy.get('[id="settings_plugin_mrbeam_dev_design_store_link"]').click();
        cy.get('[data-test="dev-design-store-email"]')
            .invoke("prop", "value")
            .should("to.contain", "dev+1@mr-beam.org");
        cy.get('[data-test="dev-design-store-email"]')
            .clear()
            .type("dev@mr-beam.org");
    });
});
