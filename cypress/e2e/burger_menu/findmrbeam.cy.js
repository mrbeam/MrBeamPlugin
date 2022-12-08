describe('Find.mr.beam', () => {
  beforeEach(function () {
        cy.fixture("test-data").then(function (testData) {
            this.testData = testData;
        });
    });

    beforeEach(function () {
        cy.visit(this.testData.url_laser);
        cy.wait(10000);
        cy.loginLaser(this.testData.email, this.testData.password);
    });

    it("Find.mr.beam", function () {
        // check existence of burger menu icon
        cy.get('[id="burger_menu_link"]')
        .should("to.exist");

        // click on find.mr.beam under burger menu icon
        cy.get('[id="burger_menu_link"]')
        .click();
        cy.get('[id="burger_menu"] > .dropdown-menu > .show_only_online > a').should("to.exist");

        // test find.mr.beam website url & title
        cy.get('[id="burger_menu"] > .dropdown-menu > .show_only_online > a').invoke('removeAttr', 'target').click({force: true});
        cy.url().should('eq', 'http://find.mr-beam.org/');
        cy.title().should('eq', 'find.mr-beam.org - Easily connect to your Mr Beam laser cutter');
    });
});
