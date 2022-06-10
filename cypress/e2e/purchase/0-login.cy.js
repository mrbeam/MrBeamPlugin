describe("Login", function() {

  beforeEach(function() {
      cy.fixture('test-data').then(function(testData){
          this.testData = testData});  
  });

  beforeEach(function() {
      cy.visit(this.testData.url);
      cy.wait(15000);
      cy.switchEnv(this.testData.email, this.testData.password)
  });

  it('Login', function() {
      cy.get('[id="designstore_tab_btn"]').click();
      cy.wait(7000);
      cy.iframe('[id="design_store_iframe"]')
        .find('.btn').contains('Login').click();
      cy.iframe('[id="design_store_iframe"]')
        .contains('Enter your existing code').click();
      cy.iframe('[id="design_store_iframe"]')
        .find('[placeholder="XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"]').first().type(this.testData.verify_code);
      cy.iframe('[id="design_store_iframe"]')
        .contains('Verify').click();
  });
});