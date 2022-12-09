describe("Maintenance", function () {
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
    it("Air Filter: Pre-filter", function () {
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
    it("Air Filter: Pre-filter", function () {
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
        cy.get('#reset_counter_are_you_sure > .modal-header').should('to.visible')
        cy.get('[data-test="maintenance-yes-button"]').click();
        cy.get('#reset_counter_are_you_sure > .modal-header').should('not.visible')
    });
    it("Reset Air Filter: Main filter", function () {
        cy.get('[id="settings_plugin_mrbeam_maintenance_link"]').click();
        cy.get('[data-test="maintenance-reset-button-carbon-filter"]').eq(1).click();
        cy.get('#reset_counter_are_you_sure > .modal-header').should('to.visible')
        cy.get('[data-test="maintenance-yes-button"]').click();
        cy.get('#reset_counter_are_you_sure > .modal-header').should('not.visible')
    });
    it("Reset Laser head cleaning", function () {
        cy.get('[id="settings_plugin_mrbeam_maintenance_link"]').click();
        cy.get('[data-test="maintenance-reset-button-laser-head"]').click();
        cy.get('#reset_counter_are_you_sure > .modal-header').should('to.visible')
        cy.get('[data-test="maintenance-yes-button"]').click();
        cy.get('#reset_counter_are_you_sure > .modal-header').should('not.visible')
    });
});
