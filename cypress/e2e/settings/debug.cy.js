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

    it("Enable terminal", function () {
        cy.get('[id="settings_plugin_mrbeam_debug_link"]').click();
        cy.get('[data-test="debug-settings-enable-terminal"]')
            .if("not.checked")
            .check()
            .should("be.checked")
            .else("be.checked")
            .uncheck()
            .should("not.checked");
    });

    it("Show checksums", function () {
        cy.get('[id="settings_plugin_mrbeam_debug_link"]').click();
        cy.get('[data-test="debug-settings-show-checksums"]')
            .if("not.checked")
            .check()
            .should("be.checked")
            .else("be.checked")
            .uncheck()
            .should("not.checked");
    });
});
