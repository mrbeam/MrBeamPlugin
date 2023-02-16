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
    it("Here", function () {
        cy.get('[id="settings_plugin_mrbeam_camera_link"]').click();
        cy.get('[data-test="camera-settings-here"]')
            .contains("here")
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
    });
    it("Troublrshooting guide", function () {
        cy.get('[id="settings_plugin_mrbeam_camera_link"]').click();
        cy.get('[data-test="camera-settings-troubleshooting-guide"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
    });
    it("Camera Calibration", function () {
        cy.get('[id="settings_plugin_mrbeam_camera_link"]').click();
        cy.get('[data-test="camera-settings-camera-calibration"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
    });
});
