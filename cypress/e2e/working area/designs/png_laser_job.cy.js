describe.skip("Laser Job", function () {
    beforeEach(function () {
        cy.fixture("test-data").then(function (testData) {
            this.testData = testData;
        });
    });

    beforeEach(function () {
        cy.visit(this.testData.url_laser);
        cy.wait(10000);
        cy.loginLaser(this.testData.email, this.testData.password);
        cy.visit(this.testData.url_laser);
        cy.deleteGcoFile();
    });

    it("Add design", function () {
        cy.get('[data-test="working-area-tab-file"]').click();
        cy.get('[data-test="tab-designlib-files-list"]').then(($elem) => {
            if (
                $elem
                    .find('[data-test="tab-designlib-image-preview-card"]')
                    .filter(':contains("mirror.png")').length
            ) {
            } else {
                const filepath = "mirror.png";
                cy.get('.fileinput-button input[type="file"]').attachFile(
                    filepath
                );
                cy.wait(5000);
                cy.get('[data-test="tab-designlib-image-preview-card"]')
                    .contains("mirror.png")
                    .should("to.exist");
            }
        });
        cy.get('[data-test="tab-designlib-image-preview-card"]')
            .filter(':contains("mirror.png")')
            .click();
        cy.wait(3000);
        cy.get('[data-test="tab-workingarea-move"]').click({ force: true });
        cy.get('[data-test="tab-workingarea-scale-prop-btn"]').click();
        cy.get('[data-test="tab-workingarea-horizontal"]')
            .filter(":visible")
            .clear()
            .type("125.3 mm");
        cy.get('[data-test="tab-workingarea-vertical"]')
            .filter(":visible")
            .clear()
            .type("130.3 mm");
        cy.get('[data-test="tab-workingarea-translation"]')
            .filter(":visible")
            .clear()
            .type("135.0, 138.0");
        cy.get('[data-test="tab-workingarea-rotation"]')
            .filter(":visible")
            .clear()
            .type("-50.5");
        // image preprocessing
        cy.get(
            '[data-test="tab-workingarea-image-preprocessing-collapsible"]'
        ).click();
        cy.get(
            '[data-test="tab-workingarea-img-preprocess-contrast"]'
        ).realClick();
        cy.wait(1000);
        cy.get(
            '[data-test="tab-workingarea-img-preprocess-brightness"]'
        ).realClick({ position: "left" });
        cy.wait(1000);
        cy.get(
            '[data-test="tab-workingarea-img-preprocess-sharpen"]'
        ).realClick();
        cy.wait(1000);
        cy.get('[data-test="tab-workingarea-img-preprocess-gamma"]').realClick({
            position: "right",
        });
        cy.wait(1000);
        // crop img
        cy.get('[data-test="tab-workingarea-crop-top"]').clear().type("3");
        cy.get('[data-test="tab-workingarea-crop-left"]').clear().type("2");
        cy.get('[data-test="tab-workingarea-crop-bottom"]').clear().type("3");
        cy.get('[data-test="tab-workingarea-crop-right"]').clear().type("2");
        cy.get('[data-test="tab-workingarea-duplicate"]').click({
            force: true,
        });
        cy.laserButtonClick();
        cy.selectMaterial();
        cy.get('[data-test="laser-job-start-button"]').dblclick();
        cy.wait(2000);
        cy.get(".alert-success").should("to.exist", "Preparation done");
        cy.wait(3000);
        cy.get(".modal-scrollable").click({ force: true });
        cy.get('[data-test="mrbeam-ui-index-design-library"]').click();
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
                cy.readFile("cypress/fixtures/mirror.2x.gco", {
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
