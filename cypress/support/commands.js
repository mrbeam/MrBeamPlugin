require('cypress-iframe');
// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add('login', (email, password) => { ... })
Cypress.Commands.add("switchEnv", (email, password) => {
  
    cy.get('[id="login_screen_email_address_in"]').clear().type(email);
    cy.get('[id="login_screen_password_in"]').clear().type(password);
    cy.get('[id="login_screen_login_btn"]').click();
    cy.wait(3000)
    cy.get('.modal-footer').find('.btn-danger').last().click({force:true});;
    cy.get('[id="workingarea"]').should('to.exist'); 
    cy.get('[id="burger_menu_link"]').click();
    cy.get('[id="settings_tab_btn"]').click({force:true});
    cy.get('[id="settings_plugin_mrbeam_dev_design_store_link"]').click();
    cy.get('[id="settings-mrbeam-design-store-environment"]').select('dev'); 
  });

Cypress.Commands.add('loginStore', (code) => {
    
    cy.iframe('[id="design_store_iframe"]')
      .contains('Enter your existing code').click();
    cy.iframe('[id="design_store_iframe"]')
      .find('[placeholder="XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"]').first().type(code);
    cy.iframe('[id="design_store_iframe"]')
      .contains('Verify').click();
  });

  Cypress.Commands.add("loginLibrary", (email, password) => {
  
    cy.get('[id="login_screen_email_address_in"]').clear().type(email);
    cy.get('[id="login_screen_password_in"]').clear().type(password);
    cy.get('[id="login_screen_login_btn"]').click();
    cy.wait(3000);
    cy.get('.modal-footer').find('.btn-danger').last().click({force:true});
    cy.get('[id="designlib_tab_btn"]').click();
    cy.get('[id="workingarea"]').should('to.exist'); 
});

Cypress.Commands.add("loginLaser", (email, password) => {
  
  cy.get('[id="login_screen_email_address_in"]').clear().type(email);
  cy.get('[id="login_screen_password_in"]').clear().type(password);
  cy.get('[id="login_screen_login_btn"]').click();
  cy.wait(3000);
  cy.get('.modal-footer').find('.btn-danger').last().click({force:true});
  cy.get('[id="workingarea"]').should('to.exist'); 
});

Cypress.Commands.add("logout", () => {
  
    cy.get('[id="navbar_login"]').click();
    cy.get('[id="logout_button"]').click({force:true});
});

import 'cypress-file-upload';
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })