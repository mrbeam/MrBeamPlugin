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

    it("Reminder", function () {
        cy.get('[id="settings_plugin_mrbeam_reminders_link"]').click();
        cy.get('[data-test="reminder-settings-focus-reminder"]')
            .if("not.checked")
            .check()
            .should("be.checked")
            .else("be.checked")
            .uncheck()
            .should("not.checked");
    });
});
