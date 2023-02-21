describe.skip("Laser Job", function () {
    beforeEach(function () {
        cy.fixture("test-data").then(function (testData) {
            this.testData = testData;
        });
    });

    beforeEach(function () {
        cy.visit(this.testData.url_laser);
        cy.get('[id="loading_overlay"]', { timeout: 20000 }).should(
            "not.be.visible"
        );
        cy.loginLaser(this.testData.email, this.testData.password);
        cy.visit(this.testData.url_laser);
        cy.deleteGcoFile();
    });

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
        cy.get('[data-test="tab-designlib-dxf-preview-card"]').click();
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
        cy.laserButtonClick();
        cy.selectMaterial();
        cy.get('[data-test="laser-job-start-button"]').dblclick();
        cy.wait(2000);
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.get(".modal-scrollable").click({ force: true });
        cy.get('[data-test="mrbeam-ui-index-design-library"]').click();
        cy.get('[data-test="mrbeam-ui-index-design-library"]').click();
        cy.get('[data-test="tab-designlib-filter-gcode-radio"]').click();
        cy.wait(2000);
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
                cy.readFile("cypress/fixtures/paris1.gco", {
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
                            let bodyNoComments = $body
                                .replace(/^;.*$/gm, "")
                                .trimEnd();
                            let contentTestFileNoComments = contentTestFile
                                .replace(/^;.*$/gm, "")
                                .trimEnd();
                            expect(bodyNoComments).to.equal(
                                contentTestFileNoComments
                            );
                        });
                });
            });
        cy.logout();
    });
});
