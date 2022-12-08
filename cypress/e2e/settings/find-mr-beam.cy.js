describe("Find Mr Beam", function () {
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
    it("find.mrbeam.org", function () {
        cy.get('[id="settings_plugin_findmymrbeam_link"]').click();
        cy.get('[data-bind="visible: settings.settings.plugins.findmymrbeam.enabled() && registered()"] > a').invoke("attr", "href")
        .then((myLink) => {
            cy.request(myLink).then((resp) => {
                expect(resp.status).to.eq(200);
            });
        });
    })
    it("Privacy policy link", function () {
        cy.get('[id="settings_plugin_findmymrbeam_link"]').click();
        cy.get('#settings_findmymrbeam > .form-horizontal > .control-group > :nth-child(1) > p > a').invoke("attr", "href")
        .then((myLink) => {
            cy.request(myLink).then((resp) => {
                expect(resp.status).to.eq(200);
            });
        });
    })
    it("Mr Beam Status Light tells you how to connect", function () {
        cy.get('[id="settings_plugin_findmymrbeam_link"]').click();
        cy.get(':nth-child(3) > :nth-child(5) > a').invoke("attr", "href")
        .then((myLink) => {
            cy.request(myLink).then((resp) => {
                expect(resp.status).to.eq(200);
            });
        });
    })
 
});