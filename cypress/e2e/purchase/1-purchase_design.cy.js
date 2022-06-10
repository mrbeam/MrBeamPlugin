describe("Purchase", function() {

  beforeEach(function() {
      cy.fixture('test-data').then(function(testData){
          this.testData = testData});  
  });

  beforeEach(function() {
      cy.visit(this.testData.url);
      cy.wait(15000);
      cy.switchEnv(this.testData.email, this.testData.password);
      cy.get('[id="designstore_tab_btn"]').click();
      cy.wait(10000);
  });

  it('Buy design - success', function() { 
      cy.wait(10000);        
      cy.iframe('[id="design_store_iframe"]').then(($button) => {
        cy.get($button).find('[src="static/img/beam_coin_orange.png"]').first().click({force:true});
      });
      cy.iframe('[id="design_store_iframe"]')
        .contains('Confirm').click();
      cy.iframe('[id="design_store_iframe"]')
        .find('.buy-now').first().click(); 
      cy.wait(3000);
      cy.iframe('[id="design_store_iframe"]').then(($button) => {
        cy.get($button).find('.icon-download-alt').last().click({force:true});
      });
      cy.iframe('[id="design_store_iframe"]')
        .find('.view-in-library').last().should('to.exist');
      cy.logout();
  });

  it('Buy design - failed', function() {
      cy.iframe('[id="design_store_iframe"]')
        .find('[id="price_desc"]').click();
      cy.iframe('[id="design_store_iframe"]').then(($button) => {
        cy.get($button)
          .find('[id="25_purchase_btn"]').click({force:true});
        }); 
      cy.iframe('[id="design_store_iframe"]')
        .contains('Confirm').click();
      cy.iframe('[id="design_store_iframe"]')
        .find('.buy-now').click();
      cy.get('.alert-error').should('to.exist');
      cy.logout();
  });

  it('Download design', function(){
      cy.iframe('[id="design_store_iframe"]')
        .find('.btn-go-to-purchases-page').click();
      cy.wait(2000);
      cy.iframe('[id="design_store_iframe"]').then(($button) => {
        cy.get($button).find('.icon-download-alt').click({multiple:true});
      });
      cy.wait(3000);
      cy.iframe('[id="design_store_iframe"]')
        .find('.view-in-library').first().click();
      cy.get('.file_list_entry').first().should('to.exist');
      cy.logout();
  });
});