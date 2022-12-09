describe('Support Portal', () => {
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
/*
        it("Support Portal  -- Youtube", function () {
        // check existence of burger menu icon
        cy.get('[id="burger_menu_link"]')
        .should("to.exist");

        // click on support portal under burger menu icon
        cy.get('[id="burger_menu_link"]')
        .click({force: true});
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Support").should("to.exist");

        // test support portal window
        cy.get('[id="support_overlay"]').should('be.not.visible');
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Support").click({force: true});
        cy.get('[id="support_overlay"]').should('be.visible');

        // test Youtube Channel
        cy.get('[data-test="Youtube"]').should("to.exist");
        cy.get('[data-test="Youtube"]').invoke('removeAttr', 'target').click({multiple: true});
        cy.url().should('eq', 'https://www.youtube.com/channel/UC8CIMavXllp6S61JgEqSm4A');

        });

        it("Support Portal -- Knowledge Base", function () {
        // check existence of burger menu icon
        cy.get('[id="burger_menu_link"]')
        .should("to.exist");

        // click on support portal under burger menu icon
        cy.get('[id="burger_menu_link"]')
        .click({force: true});
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Support").should("to.exist");

        // test support portal window
        cy.get('[id="support_overlay"]').should('be.not.visible');
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Support").click({force: true});
        cy.get('[id="support_overlay"]').should('be.visible');

        // test Knowledge Base
        cy.get('[data-test="Knowledge"]').should("to.exist");
        cy.get('[data-test="Knowledge"]').invoke('removeAttr', 'target').click({multiple: true});
        cy.url().should('eq', 'https://mr-beam.freshdesk.com/de/support/solutions?utm_source=beamos&utm_medium=beamos&utm_campaign=welcome_dialog');
        }); */

        it("Support Portal -- Guided Tour ", function () {
        // check existence of burger menu icon
        cy.get('[id="burger_menu_link"]')
        .should("to.exist");

        // click on support portal under burger menu icon
        cy.get('[id="burger_menu_link"]')
        .click({force: true});
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Support").should("to.exist");

        // test support portal window
        cy.get('[id="support_overlay"]').should('be.not.visible');
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Support").click({force: true});
        cy.get('[id="support_overlay"]').should('be.visible');

        // test Guided Tour
        cy.get('[data-test="Tour"]').should("to.exist");
        //cy.get('.hopscotch-bubble').should('be.not.visible');
        cy.get('[data-test="Tour"]').click({multiple: true});
        cy.get('.hopscotch-bubble').should('be.visible');

        // test close guided tour button
        cy.get('.hopscotch-bubble > .hopscotch-bubble-container > .hopscotch-bubble-close')
        .should("to.exist");

        cy.get('[data-test="Tour"]').should('be.not.visible');
        cy.get('.hopscotch-bubble > .hopscotch-bubble-container > .hopscotch-bubble-close')
        .click();
        cy.get('[data-test="Tour"]').should('be.visible');

        // test cancel guided tour button
        cy.get('[data-test="Tour"]').click({multiple: true});
        cy.get('.hopscotch-bubble > .hopscotch-bubble-container > .hopscotch-actions > .hopscotch-nav-button')
        .contains('button', "Maybe later").should("to.exist");
        cy.get('[data-test="Tour"]').should('be.not.visible');
        cy.get('.hopscotch-bubble > .hopscotch-bubble-container > .hopscotch-actions > .hopscotch-nav-button')
        .contains('button', "Maybe later").click();
        cy.get('[data-test="Tour"]').should('be.visible');

        // test start the guided tour button
        cy.get('[data-test="Tour"]').click({multiple: true});
        cy.get('.hopscotch-bubble > .hopscotch-bubble-container > .hopscotch-actions > .hopscotch-nav-button')
        .contains('button', "Yes, let's go!").should("to.exist");
        cy.get('[data-test="Tour"]').should('be.not.visible');
        cy.get('.hopscotch-bubble > .hopscotch-bubble-container > .hopscotch-actions > .hopscotch-nav-button')
        .contains('button', "Yes, let's go!").click();

        // next guided tour window shows up
        cy.get('.hopscotch-bubble > .hopscotch-bubble-container > .hopscotch-bubble-close')
        .should("to.exist");
        });
});
