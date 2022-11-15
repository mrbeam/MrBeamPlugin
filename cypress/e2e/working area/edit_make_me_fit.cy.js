describe("Laser Job", function () {
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

    it("Make me fit", function () {
        cy.get('[id="working_area_tab_file_btn"]').click();
        cy.get('[id="files_list"]').then(($elem) => {
            if (
                $elem
                    .find(".files_template_model_svg")
                    .filter(':contains("black_cat.svg")').length
            ) {
            } else {
                const filepath = "black_cat.svg";
                cy.get('.fileinput-button input[type="file"]').attachFile(
                    filepath
                );
                cy.wait(5000);
                cy.get(".files_template_model_svg")
                    .contains("black_cat")
                    .should("to.exist");
            }
        });
        cy.get(".files_template_model_svg")
            .filter(':contains("black_cat.svg")')
            .click();
        cy.wait(3000);
        cy.get('[name="working_area_tab_make_it_fit"]').realClick();
        cy.get('[name="working_area_tab_make_it_fit"]').realClick();
        cy.get('[name="working_area_tab_make_it_fit"]').should('not.visible');
        cy.logout();
    }); 
    
    it("Edit", function () {
        cy.get('[id="working_area_tab_shape_btn"]').click();
        cy.get('[id="quick_shape_shape_done_btn"]').click();
        cy.get('[id="wa_filelist"]').contains('Rectangle').should('to.exist');
        cy.wait(2000);
        cy.get('.btn-mini').find('.icon-edit').click({force:true});
        cy.get('[id="quick_shape_dialog"]').should('to.visible');
        cy.get('[id="shape_tab_link_star"]').click();
        cy.get('[id="quick_shape_star_radius"]').clear().type("60");
        cy.get('[id="quick_shape_star_corners"]').clear().type("8");
        cy.get('[id="quick_shape_star_sharpness"]').realClick();
        cy.get('[id="qs_colorPicker_stroke"]').click();
        cy.get('#qs_colorPicker_stroke > .track > canvas').realClick({ position: "top" });
        cy.get('[id="quick_shape_fill"]').click();
        cy.get('[id="qs_colorPicker_fill"]').click();
        cy.get('#qs_colorPicker_fill > .track > canvas').realClick({ position: "top" });
        cy.get('[id="quick_shape_shape_done_btn"]').click();
        cy.get('[id="wa_filelist"]').contains('Star').should('to.exist');
    });

    it("Clear all", function () {
        cy.get('[id="wa_filelist"]').contains('.file_list_entry').should('not.exist');
        cy.get('[id="working_area_tab_shape_btn"]').click();
        cy.get('[id="quick_shape_shape_done_btn"]').click();
        cy.get('[id="wa_filelist"]').contains('Rectangle').should('to.exist');
        cy.wait(2000);
        cy.get('[id="working_area_tab_file_btn"]').click();
        cy.get(".files_template_model_svg").first().click();
        cy.get('[id="working_area_tab_text_btn"]').click();
        cy.get('[id="quick_text_dialog_text_input"]').type("MrBeam");
        cy.get('[id="quick_text_text_done_btn"]').click();
        cy.get('[id="wa_filelist"]').find('.file_list_entry').should('to.exist');
        cy.get('[id="clear_working_area_btn"]').click();
        cy.get('[id="wa_filelist"]').contains('.file_list_entry').should('not.exist'); 
    });

    it.only("reset and remove", function () {
        cy.get('[id="working_area_tab_file_btn"]').click();
        cy.get('[id="files_list"]').then(($elem) => {
            if (
                $elem
                    .find(".files_template_model_image")
                    .filter(':contains("paris2.jpg")').length
            ) {
            } else {
                const filepath = "paris2.jpg";
                cy.get('.fileinput-button input[type="file"]').attachFile(
                    filepath
                );
                cy.wait(5000);
                cy.get(".files_template_model_image")
                    .contains("paris2.jpg")
                    .should("to.exist");
            }
        });
        cy.get(".files_template_model_image")
            .filter(':contains("paris2.jpg")')
            .click();
        cy.wait(3000);
        cy.get('.multiply').clear().type('2x3');
        cy.get(".userIMG").click({ force: true });
        cy.get('[id="translateHandle"]').move({
            deltaX: 213.9689,
            deltaY: -144.1241,
            force: true,
        });
        cy.get(".rotation").clear().type("250.5");
        cy.get(".horizontal").clear().type("225.3 mm");
        cy.get(".vertical").clear().type("230.3 mm");
        cy.get('.btn-mini').find('.icon-undo').click({force:true});
        cy.wait(2000);
        cy.get('.btn-mini').find('.icon-remove').click({force:true});
        cy.get('[id="wa_filelist"]').contains('.file_list_entry').should('not.exist'); 
        cy.logout();
    });
});