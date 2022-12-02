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
        cy.get('[data-test="mrbeam-ui-index-tab-settings"]').click({ force: true });
    });

    afterEach(function () {
        cy.logout();
    })
    it("Access control", function () {
        cy.get('[id="settings_plugin_mrbeam_maintenance_link"]').click();
        cy.get('[data-test="maintenance-links-buy-now-pre-filter"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
    });
    it("Access control", function () {
        cy.get('[id="settings_plugin_mrbeam_maintenance_link"]').click();
        cy.get('[data-test="maintenance-links-buy-now-main-filter"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
    });
    it("Access control", function () {
        cy.get('[id="settings_plugin_mrbeam_maintenance_link"]').click();
        cy.get('[data-test="maintenance-links-buy-now-laser-head"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
    });
    it("Access control", function () {
        cy.get('[id="settings_plugin_mrbeam_maintenance_link"]').click();
        cy.get('[data-test="maintenance-links-how-laser-head"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
    });
    it("Reset", function () {
        cy.get('[id="settings_plugin_mrbeam_maintenance_link"]').click();
        cy.get('[data-test="maintenance-reset-button"]').click();
        cy.get('[data-test="maintenance-yes-button"]').click();
        cy.get(":nth-child(1) > .maintenance-reset-column > .btn").click();
        cy.get("#reset_counter_btn").click();
    });
    it("Reset", function () {
        cy.get('[id="settings_plugin_mrbeam_maintenance_link"]').click();
        cy.get('[data-test="maintenance-reset-button"]').click();
        cy.get('[data-test="maintenance-yes-button"]').click();
        cy.get(":nth-child(2) > .maintenance-reset-column > .btn").click();
        cy.get("#reset_counter_btn").click();
    });
    it("Reset", function () {
        cy.get('[id="settings_plugin_mrbeam_maintenance_link"]').click();
        cy.get('[data-test="maintenance-reset-button"]').click();
        cy.get('[data-test="maintenance-yes-button"]').click();
        cy.get(":nth-child(3) > .maintenance-reset-column > .btn").click();
        cy.get("#reset_counter_btn").click();
    });
});
