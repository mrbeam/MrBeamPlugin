describe("Functionalities", function () {

    beforeEach(function () {
        cy.fixture("test-data").then(function (testData) {
            this.testData = testData;
        });
    });

    beforeEach(function () {
        cy.visit(this.testData.url_laser);
        cy.wait(10000);
        cy.loginLaser(this.testData.email, this.testData.password);
        cy.reload();
        cy.visit(this.testData.url_laser);
        cy.get('.icon-remove').click({ force: true, multiple: true });
    });

    it('Start without set settings', function () {
        cy.get('[id="working_area_tab_shape_btn"]').click();
        cy.get('[id="shape_tab_link_star"]').click();
        cy.get('[id="quick_shape_shape_done_btn"]').click();
        cy.get('[id="laser_button"]').click();
        cy.get('[data-cy="”laser-job-start-button”"]').filter('.disabled').should('to.exist');
        cy.get('#dialog_vector_graphics_conversion > :nth-child(4) > [aria-hidden="true"]').click();
        cy.logout();
    });

    it('Back button', function () {
        cy.get('[id="working_area_tab_shape_btn"]').click();
        cy.get('[id="shape_tab_link_star"]').click();
        cy.get('[id="quick_shape_shape_done_btn"]').click();
        cy.get('[id="laser_button"]').click();
        cy.get('[id="dialog_vector_graphics_conversion"]').should('be.visible');
        cy.get('#dialog_vector_graphics_conversion > :nth-child(4) > [aria-hidden="true"]').click();
        cy.get('[id="dialog_vector_graphics_conversion"]').should('not.be.visible');
        cy.get('[id="area_preview"]').should('be.visible');
        cy.logout();
    });

    it('Material and back', function () {
        cy.get('[id="working_area_tab_shape_btn"]').click();
        cy.get('[id="shape_tab_link_star"]').click();
        cy.get('[id="quick_shape_shape_done_btn"]').click();
        cy.get('[id="laser_button"]').click();
        cy.get(7000);
        cy.get('[id="material_list"]')
            .contains(/^Foam Rubber$/)
            .click();
        cy.wait(2000)
        cy.get(".selected").should(($elem) => {
            expect($elem).to.have.length(1);
            expect($elem).to.be.visible;
        });
        cy.get('[id="material_list"]')
            .contains(/^Foam Rubber$/)
            .click();
        cy.wait(2000)
        cy.get('[id="material_list"] > li').should(($elem) => {
            expect($elem).to.have.length(22);
            expect($elem).to.be.visible;
        });
        cy.get('#dialog_vector_graphics_conversion > :nth-child(4) > [aria-hidden="true"]').click();
        cy.logout();
    });

    it('Color and back', function () {
        cy.get('[id="working_area_tab_shape_btn"]').click();
        cy.get('[id="shape_tab_link_star"]').click();
        cy.get('[id="quick_shape_shape_done_btn"]').click();
        cy.get('[id="laser_button"]').click();
        cy.get(7000);
        cy.get(".material_entry")
            .contains(/^Foam Rubber$/)
            .click();
        cy.get('[id="material_color_0057a8"]').click();
        cy.wait(2000)
        cy.get('.material_color_entry').filter(':visible').should(($elem) => {
            expect($elem).to.have.length(1);
            expect($elem).to.be.visible;
        });
        cy.get('[id="material_color_0057a8"]').click();
        cy.wait(2000)
        cy.get('.material_color_entry').filter(':visible').should(($elem) => {
            expect($elem).to.have.length(5);
            expect($elem).to.be.visible;
        });
        cy.get('#dialog_vector_graphics_conversion > :nth-child(4) > [aria-hidden="true"]').click();
        cy.logout();
    });

    it('Thinknees and back', function () {
        cy.get('[id="working_area_tab_shape_btn"]').click();
        cy.get('[id="shape_tab_link_star"]').click();
        cy.get('[id="quick_shape_shape_done_btn"]').click();
        cy.get('[id="laser_button"]').click();
        cy.get(7000);
        cy.get(".material_entry")
            .contains(/^Foam Rubber$/)
            .click();
        cy.get('[id="material_color_0057a8"]').click();
        cy.wait(1000);
        cy.get('[id="material_thickness_2"]').click();
        cy.wait(2000)
        cy.get('.thickness_sample').filter(':visible').should(($elem) => {
            expect($elem).to.have.length(1);
            expect($elem).to.be.visible;
        });
        cy.get('[id="material_thickness_2"]').click();
        cy.wait(2000)
        cy.get('.thickness_sample').filter(':visible').should(($elem) => {
            expect($elem).to.have.length(3);
            expect($elem).to.be.visible;
        });
        cy.get('#dialog_vector_graphics_conversion > :nth-child(4) > [aria-hidden="true"]').click();
        cy.logout();
    });

    it('Help', function () {
        cy.get('[id="working_area_tab_shape_btn"]').click();
        cy.get('[id="shape_tab_link_star"]').click();
        cy.get('[id="quick_shape_shape_done_btn"]').click();
        cy.get('[id="laser_button"]').click();
        cy.get(7000);
        cy.get(".material_entry")
            .contains(/^Foam Rubber$/)
            .click();
        cy.get('[id="material_color_0057a8"]').click();
        cy.get('.modal_dialog_headline > div > .show_only_online').click();
    });

    it('Manage materials', function () {
        cy.get('[id="working_area_tab_shape_btn"]').click();
        cy.get('[id="shape_tab_link_star"]').click();
        cy.get('[id="quick_shape_shape_done_btn"]').click();
        cy.get('[id="laser_button"]').click();
        cy.get(7000);
        cy.get('[id="materials_manage"]').click();
        cy.get('[id="materials_manage_done"]').should('be.visible');
        cy.get('[id="materials_manage"]').should('not.be.visible');
        cy.get('#material_burger_menu > div > .show_only_online').click();
        cy.get('[id="materials_manage_done"]').click();
        cy.get('#dialog_vector_graphics_conversion > :nth-child(4) > [aria-hidden="true"]').click();
        cy.logout();
    });
});