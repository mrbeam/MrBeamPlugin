describe('Messages', () => {
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

    it("Messages", function () {
        //check existence of the User Settings under profile icon
        cy.get('[id="messages_nav_tab"]')
        .should("to.exist");

        cy.get('.mrb-messages-container').should('be.not.visible');
        // test clicking on messages icon
        cy.get('[id="messages_nav_tab"]').click();
        cy.get('.mrb-messages-container').should('be.visible');

        // test messages container to have at least one message
        cy.get('.mrb-messages-container')
        .get('.mrb-message-list')
        .get('.mrb-message-element').should('have.length.least', 1)

        // test clicking on a message
        cy.get('[id="no-mrb-messages-selected"]').should('be.visible');
        cy.get('.mrb-message-element').click();
        cy.get('[id="mrb-message-view"]')
        .get('.mrb-message-content')
        .get('.mrb-message-content-title').should('be.visible');
    });
});
