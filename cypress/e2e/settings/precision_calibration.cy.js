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

    it("Manual user", function () {
        cy.get('[id="settings_plugin_mrbeam_backlash_link"]').click();
        cy.get('[href="https://www.mr-beam.org/downloads/"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
    });

    it("Knowlage base", function () {
        cy.get('[id="settings_plugin_mrbeam_backlash_link"]').click();
        cy.get('small > [href="https://support.mr-beam.org"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
    });

    it("Channel Youtube", function () {
        cy.get('[id="settings_plugin_mrbeam_backlash_link"]').click();
        cy.get('[href="https://www.youtube.com/c/mrbeamlasers"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
    });

    it("Find the most precise line", function () {
        cy.get('[id="settings_plugin_mrbeam_backlash_link"]').click();
        cy.get('.btn-default').contains('Next').click()
        cy.get('[id="settings_backlash_compensation_x"]').clear().type('01')
        cy.get('.btn-default').contains('OK').click()
        cy.get('.btn-default').contains('Next').click()
        cy.get('[id="settings_backlash_compensation_x"]').invoke('prop', "value").should('to.contain', "01")
    
    });
});
