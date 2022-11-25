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
        cy.reload();
        cy.visit(this.testData.url_laser);
    });

    it("Add design dxf", function () {
        cy.get('[data-test="working-area-tab-file"]').click();
        cy.get('[data-test="tab-design-library-dxf-preview-card"]').then(($elem) => {
            if (
                $elem
                    .find('[data-test="tab-design-library-dxf-preview-card"]')
                    .filter(':contains("paris1.dxf")').length
            ) {
            } else {
                const filepath = "paris1.dxf";
                cy.get('.fileinput-button input[type="file"]').attachFile(
                    filepath
                );
                cy.wait(5000);
                cy.get('[data-test="tab-design-library-dxf-preview-card"]')
                    .contains("paris1.dxf")
                    .should("to.exist");
            }
        });
        cy.get('[data-test="tab-design-library-dxf-preview-card"]')
            .filter(':contains("paris1.dxf")')
            .click();
        cy.wait(3000);
        cy.get('[data-test="tab-workingarea-unit-toggler" ]').click();
        cy.get('[data-test="tab-workingarea-scale-prop-btn"]').click();
        cy.get('[data-test="tab-workingarea-horizontal"]').clear().type("1266 {enter}");
        cy.get('[data-test="tab-workingarea-vertical"]').clear().type("1466 {enter}");
        cy.get('[data-test="tab-workingarea-mirror"]').click();
        cy.get('[data-test="tab-workingarea-multiply"]').clear().type('1x3{enter}');
        cy.get('[data-test="tab-workingarea-move"]').click({force:true});
        cy.get('[data-test="tab-workingarea-translation"]').clear().type("135.0, 138.0");
        cy.get('[data-test="tab-workingarea-rotation"]').clear().type("250.5");
        cy.get('[data-test="working-area-laser-button"]').click();
        cy.get('[data-test="tab-workingarea-image-preprocessing-collapsible"]').click(); 
        cy.wait(2000);
        cy.focusReminder();
        cy.wait(2000);
        cy.get('[data-test="conversion-dialog-material-item"]').contains("Mirror").click();
        cy.get('[data-test="conversion-dialog-intensity-black"]').clear().type("95");
        cy.get('[data-test="conversion-dialog-feedrate-black"ate-black"]').clear().type("1500");
        cy.get('[data-test="conversion-dialog-show-advanced-settings"]').click();
        cy.get('[data-test="conversion-dialog-passes-input-engrave"]').first().clear().type("4");
        cy.get('[data-test="conversion-dialog-engraving-pierce-time"]').clear().type("8");
        cy.get('[data-test="conversion-dialog-line-distance-input"]').clear().type("1");
        cy.get('[data-test="conversion-dialog-engraving-mode-basic"]').dblclick(
            { force: true }
        );
        cy.get('[data-test="laser-job-start-button"]').dblclick();
        cy.wait(2000);
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.reload();
        cy.wait(10000);
        cy.get('[data-test="mrbeam-ui-index-design-library"]').click();
        cy.get('[data-test="tab-designbib-filter-gcode-radio"]').click();
        cy.get('[data-test="tab-designlib-mechinecode-file"]').first().click();
        cy.get('[data-test="working-area-laser-button"]').click();
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.logout();
    });
});
