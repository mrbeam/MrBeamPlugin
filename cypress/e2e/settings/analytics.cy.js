describe("Navbar icons", function () {
    beforeEach(function () {
        cy.fixture("test-data").then(function (testData) {
            this.testData = testData;
        });
    });

    beforeEach(function () {
        cy.visit(this.testData.url_laser);
        cy.wait(20000);
        cy.loginLaser(this.testData.email, this.testData.password);
        cy.get('[data-test="mrbeam-ui-index-menu-burger"]').click();
        cy.get('[data-test="mrbeam-ui-index-tab-settings"]').click({
            force: true,
        });
    });
    it("More information about what data we use", function () {
        cy.get('[id="settings_plugin_mrbeam_analytics_link"]').click();
        cy.get(".mb-0 > .btn-link").click();
        cy.get(".card-body").should("to.visible");
        cy.wait(3000);
        cy.get(".analytics-collapsible").click();
        cy.get(".card-body").should("not.visible");
    });
    it("Privacy policy", function () {
        cy.get('[id="settings_plugin_mrbeam_analytics_link"]').click();
        cy.get('[style="color: darkgray;font-size: 0.9em"] > a')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
    });
});
