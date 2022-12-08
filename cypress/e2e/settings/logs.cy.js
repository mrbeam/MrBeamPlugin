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
    it("Enable terminal", function () {
        cy.get('[id="settings_logs_link"]').click();
        cy.get('.fa-download').first().click()
            
    });
    it("Enable terminal", function () {
        cy.get('[id="settings_logs_link"]').click();
        cy.get('.fa-download').eq(1).click()
            
    });
    it("Enable terminal", function () {
        cy.get('[id="settings_logs_link"]').click();
        cy.get('.fa-download').last().click()
            
    });
    it("Enable terminal", function () {
        cy.get('[id="settings_logs_link"]').click();
        cy.contains('Name (ascending)').last().click()
            
    });
    it("Enable terminal", function () {
        cy.get('[id="settings_logs_link"]').click();
        cy.contains('Modification date (descending)').last().click()
            
    });
    it("Enable terminal", function () {
        cy.get('[id="settings_logs_link"]').click();
        cy.contains('Size (descending)').last().click()
            
    });
});
