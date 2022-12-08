describe("Files", function () {
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
    it("SVG dpi", function () {
        cy.get('[id="settings_plugin_mrbeam_conversion_link"]').click();
        cy.get('#settings-svgtogcode-svgDPI').clear().type('100');
        cy.get('[id="settings_plugin_mrbeam_maintenance_link"]').click();
        cy.get('[id="settings_plugin_mrbeam_conversion_link"]').click();
        cy.get('#settings-svgtogcode-svgDPI').invoke('prop', "value").should('to.contain', "100")
    })
    it("DXF default scale factor", function () {
        cy.get('[id="settings_plugin_mrbeam_conversion_link"]').click();
        cy.get('#settings-svgtogcode-dxfScale').clear().type('100');
        cy.get('[id="settings_plugin_mrbeam_maintenance_link"]').click();
        cy.get('[id="settings_plugin_mrbeam_conversion_link"]').click();
        cy.get('#settings-svgtogcode-dxfScale').invoke('prop', "value").should('to.contain', "100")
        
    })
    it("Delete GCode files automatically", function () {
        cy.get('[id="settings_plugin_mrbeam_conversion_link"]').click();
        cy.get(':nth-child(4) > .control-group > div > .checkbox > input').if('not.checked')
        .check().should("be.checked")
        .else('be.checked')
        .uncheck()
        .should('not.checked')     
    })
});
