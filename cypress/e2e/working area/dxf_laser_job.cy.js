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
    // to fix... wip
    it("Add design dxf", function () {
        cy.get('[data-test="working-area-tab-file"]').click();
        cy.get('[data-test="tab-designlib-files-list"]').then(($elem) => {
            if (
                $elem
                    .find('[data-test="tab-designlib-files-list"]')
                    .filter(':contains("paris1.dxf")').length
            ) {
            } else {
                const filepath = "paris1.dxf";
                cy.get('.fileinput-button input[type="file"]').attachFile(
                    filepath
                );
                cy.wait(5000);
                cy.get('[data-test="tab-designlib-files-list"]')
                    .contains("paris1.dxf")
                    .should("to.exist");
            }
        });
        cy.get('[data-test="tab-designlib-dxf-preview-card"]')
            // .filter(':contains("paris1.dxf")')
            .click();
        cy.wait(3000);
        cy.get('[data-test="tab-workingarea-unit-toggler"]').click();
        cy.get('[data-test="tab-workingarea-scale-prop-btn"]').click();
        cy.get('[data-test="tab-workingarea-horizontal"]')
            .filter(":visible")
            .clear()
            .type("1266 {enter}");
        cy.get('[data-test="tab-workingarea-vertical"]')
            .filter(":visible")
            .clear()
            .type("1466 {enter}");
        cy.get('[data-test="tab-workingarea-mirror-switch"]').click();
        cy.get('[data-test="tab-workingarea-multiply"]')
            .clear()
            .type("1x3{enter}");
        cy.get('[data-test="tab-workingarea-move"]').click({ force: true });
        cy.get('[data-test="tab-workingarea-translation"]')
            .filter(":visible")
            .clear()
            .type("135.0, 138.0");
        cy.get('[data-test="tab-workingarea-rotation"]')
            .filter(":visible")
            .clear()
            .type("250.5");

        // cy.get(
        //     '[data-test="tab-workingarea-image-preprocessing-collapsible"]'
        // ).click();
        cy.get('[data-test="working-area-laser-button"]').click();
        cy.wait(2000);
        cy.focusReminder();
        cy.wait(2000);
        cy.get('[data-test="conversion-dialog-material-item"]')
            .contains("Mirror")
            .click();
        cy.get('[data-test="conversion-dialog-intensity-black"]')
            .clear()
            .type("95");
        cy.get('[data-test="conversion-dialog-feedrate-black"]')
            .clear()
            .type("1500");
        cy.get(
            '[data-test="conversion-dialog-show-advanced-settings"]'
        ).click();
        cy.get('[data-test="conversion-dialog-passes-input-engrave"]')
            .first()
            .clear()
            .type("4");
        cy.get('[data-test="conversion-dialog-engraving-pierce-time"]')
            .clear()
            .type("8");
        cy.get('[data-test="conversion-dialog-line-distance-input"]')
            .clear()
            .type("1");
        cy.get('[data-test="conversion-dialog-engraving-mode-basic"]').dblclick(
            { force: true }
        );
        cy.get('[data-test="laser-job-start-button"]').dblclick();
        cy.wait(2000);
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.get(".modal-scrollable").click({ force: true });
        cy.get('[data-test="mrbeam-ui-index-design-library"]').click();
        cy.get('[data-test="tab-designlib-filter-gcode-radio"]').click();
        cy.wait(3000);
        cy.get('[data-test="tab-designlib-mechinecode-file-card"]')
            .first()
            .find('[data-test="tab-designlib-mechinecode-file-icon-reorder"]')
            .click({ force: true })
            .invoke("prop", "innerText")
            .then((downloadFile) => {
                cy.intercept(
                    "GET",
                    `http://localhost:5002/downloads/files/local/${downloadFile}*`
                ).as("file");
                cy.window()
                    .document()
                    .then(function (doc) {
                        doc.addEventListener("click", () => {
                            setTimeout(function () {
                                doc.location.reload();
                            }, 5000);
                        });
                        cy.get(
                            '[data-test="tab-designlib-mechinecode-file-card"]'
                        )
                            .filter(`:contains(${downloadFile})`)
                            .find(
                                '[data-test="tab-designlib-mechinecode-file-icon-reorder"]'
                            );
                        cy.wait(1000);
                        cy.get(
                            '[data-test="tab-designlib-mechinecode-file-download"]'
                        )
                            .filter(":visible")
                            .click();
                    });
                    cy.readFile("cypress/downloads/paris1.gco", {
                        timeout: 40000,
                    }).then((contentTestFile) => {
                       
                        cy.get(
                            '[data-test="mrbeam-ui-index-design-library"]'
                        ).click();
                        cy.get(
                            '[data-test="tab-designlib-filter-gcode-radio"]'
                        ).click();
                        cy.get('[data-test="tab-designlib-mechinecode-file-card"]')
                            .first()
                            .click({ force: true });
                        cy.wait("@file")
                            .its("response.body")
                            .should(($body) => {
                                expect($body).to.equal(contentTestFile);
                            });
            });
            });
        cy.logout();
    });
});
