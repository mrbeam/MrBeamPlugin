describe("Heavy Duty Prefilter", function () {
    beforeEach(function () {
        cy.fixture("test-data").then(function (testData) {
            this.testData = testData;
        });
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
    it("When checkbox is clicked then setting is saved.", function () {
        cy.get('[id="settings_plugin_mrbeam_custom_material_link"]').click();
        // cy.request('/settings').its('body').should('include', '<h1>Admin</h1>')

        cy.get(
            '[data-test="maintenance-heavy-duty-prefilter-enable-checkbox"]'
        ).check();
        cy.request("GET", this.testData.url + "api/settings").then(
            (response) => {
                // response.body is automatically serialized into JSON
                // expect(response.body).to.have.property('plugins.mrbeam.heavyDutyPrefilter', 'True') // true

                expect(
                    response.body.plugins.mrbeam.heavyDutyPrefilter
                ).to.equal(true);
            }
        );
        cy.get(
            '[data-test="maintenance-heavy-duty-prefilter-enable-checkbox"]'
        ).uncheck();
        cy.request("GET", this.testData.url + "api/settings").then(
            (response) => {
                // response.body is automatically serialized into JSON
                // expect(response.body).to.have.property('plugins.mrbeam.heavyDutyPrefilter', 'True') // true

                expect(
                    response.body.plugins.mrbeam.heavyDutyPrefilter
                ).to.equal(false);
            }
        );
    });
});
