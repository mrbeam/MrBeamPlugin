describe("Maintenance", function () {
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

    afterEach(function () {
        cy.logout();
    });
    //status code no exist
    it("Air Filter: Pre-filter", function () {
        cy.get('[id="settings_plugin_mrbeam_maintenance_link"]').click();
        cy.get('[data-test="maintenance-links-buy-now-pre-filter"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
    });
    // status code no exist
    it("Air Filter: Main-filter", function () {
        cy.get('[id="settings_plugin_mrbeam_maintenance_link"]').click();
        cy.get('[data-test="maintenance-links-buy-now-main-filter"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
    });
    // status code no exist
    it("Laser head cleaning", function () {
        cy.get('[id="settings_plugin_mrbeam_maintenance_link"]').click();
        cy.get('[data-test="maintenance-links-buy-now-laser-head"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
    });
    it("How to clean a laser head", function () {
        cy.get('[id="settings_plugin_mrbeam_maintenance_link"]').click();
        cy.get('[data-test="maintenance-links-how-laser-head"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
    });
    it("Reset Air Filter: Pre-filter", function () {
        cy.get('[id="settings_plugin_mrbeam_maintenance_link"]').click();
        cy.get('[data-test="maintenance-reset-button-pre-filter"]').click();
        cy.get("#reset_counter_are_you_sure > .modal-header").should(
            "to.visible"
        );
        cy.get('[data-test="maintenance-yes-button"]').click();
        cy.get("#reset_counter_are_you_sure > .modal-header").should(
            "not.visible"
        );
    });
    it("Reset Air Filter: Main filter", function () {
        cy.get('[id="settings_plugin_mrbeam_maintenance_link"]').click();
        cy.get('[data-test="maintenance-reset-button-carbon-filter"]').click();
        cy.get("#reset_counter_are_you_sure > .modal-header").should(
            "to.visible"
        );
        cy.get('[data-test="maintenance-yes-button"]').click();
        cy.get("#reset_counter_are_you_sure > .modal-header").should(
            "not.visible"
        );
    });
    it("Reset Laser head cleaning", function () {
        cy.get('[id="settings_plugin_mrbeam_maintenance_link"]').click();
        cy.get('[data-test="maintenance-reset-button-laser-head"]').click();
        cy.get("#reset_counter_are_you_sure > .modal-header").should(
            "to.visible"
        );
        cy.get('[data-test="maintenance-yes-button"]').click();
        cy.get("#reset_counter_are_you_sure > .modal-header").should(
            "not.visible"
        );
    });

    it("When checkbox is clicked then setting is saved.", function () {
        cy.get('[id="settings_plugin_mrbeam_maintenance_link"]').click();
        // cy.request('/settings').its('body').should('include', '<h1>Admin</h1>')

        cy.get(
            '[data-test="maintenance-heavy-duty-prefilter-enable-checkbox"]'
        ).check();

        cy.intercept("GET", this.testData.url + "api/settings").as("getData");

        // Send the request to the server
        cy.visit(this.testData.url);

        // Wait for the response and check its body
        cy.wait("@getData").then((interception) => {
            expect(
                interception.response.body.plugins.mrbeam.heavyDutyPrefilter
            ).to.equal(true);
        });
        // cy.request('GET', this.testData.url+'api/settings').then(
        //   (response) => {
        //     // response.body is automatically serialized into JSON
        //     // expect(response.body).to.have.property('plugins.mrbeam.heavyDutyPrefilter', 'True') // true
        //
        //       expect(response.body.plugins.mrbeam.heavyDutyPrefilter).to.equal(true);
        //   }
        // )
        cy.get(
            '[data-test="maintenance-heavy-duty-prefilter-enable-checkbox"]'
        ).uncheck();
        // cy.request('GET', this.testData.url+'api/settings').then(
        //   (response) => {
        //     // response.body is automatically serialized into JSON
        //     // expect(response.body).to.have.property('plugins.mrbeam.heavyDutyPrefilter', 'True') // true
        //
        //       expect(response.body.plugins.mrbeam.heavyDutyPrefilter).to.equal(false);
        //   }
        // )
        // cy.intercept('GET', this.testData.url+'api/settings').as('getData');

        // Send the request to the server
        cy.visit(this.testData.url);

        // Wait for the response and check its body
        cy.wait("@getData").then((interception) => {
            expect(
                interception.response.body.plugins.mrbeam.heavyDutyPrefilter
            ).to.equal(false);
        });
    });
});
