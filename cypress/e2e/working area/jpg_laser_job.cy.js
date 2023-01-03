describe("Laser Job", function () {
    beforeEach(function () {
        cy.fixture("test-data").then(function (testData) {
            this.testData = testData;
        });
    });

    beforeEach(function () {
        cy.visit(this.testData.url_laser);
        cy.wait(20000);
        cy.loginLaser(this.testData.email, this.testData.password);
        cy.visit(this.testData.url_laser);
        cy.deleteDownloadsFolder();
        cy.deleteGcoFile();
    });

    it("Add design", function () {
        cy.get('[data-test="working-area-tab-file"]').click();
        cy.get('[data-test="tab-designlib-files-list"]').then(($elem) => {
            if (
                $elem
                    .find('[data-test="tab-designlib-image-preview-card"]')
                    .filter(':contains("paris2.jpg")').length
            ) {
            } else {
                const filepath = "paris2.jpg";
                cy.get('.fileinput-button input[type="file"]').attachFile(
                    filepath
                );
                cy.wait(5000);
                cy.get('[data-test="tab-designlib-image-preview-card"]')
                    .contains("paris2.jpg")
                    .should("to.exist");
            }
        });
        cy.get('[data-test="tab-designlib-image-preview-card"]')
            .filter(':contains("paris2.jpg")')
            .click();
        cy.wait(3000);
        cy.get('[data-test="tab-workingarea-horizontal"]')
            .filter(":visible")
            .clear()
            .type("95.3 mm");
        cy.get('[data-test="tab-workingarea-vertical"]')
            .filter(":visible")
            .clear()
            .type("70.3 mm");
        cy.get(".userIMG").click({ force: true });
        cy.get('[id="translateHandle"]').move({
            deltaX: 213.9689,
            deltaY: -144.1241,
            force: true,
        });
        cy.get('[data-test="tab-workingarea-rotation"]')
            .filter(":visible")
            .clear()
            .type("200.5");
        cy.get('[data-test="tab-workingarea-multiply"]')
            .clear()
            .type("2x3{enter}");
        cy.get('[data-test="tab-workingarea-mirror-switch"]').click();
        // image preprocessing
        cy.get(
            '[data-test="tab-workingarea-image-preprocessing-collapsible"]'
        ).click();
        //preprocess img
        cy.get(
            '[data-test="tab-workingarea-img-preprocess-contrast"]'
        ).realClick({ position: "left" });
        cy.wait(1000);
        cy.get(
            '[data-test="tab-workingarea-img-preprocess-brightness"]'
        ).realClick({ position: "right" });
        cy.wait(1000);
        cy.get(
            '[data-test="tab-workingarea-img-preprocess-sharpen"]'
        ).realClick({ position: "right" });
        cy.wait(1000);
        cy.get('[data-test="tab-workingarea-img-preprocess-gamma"]').realClick({
            position: "left",
        });
        cy.wait(1000);
        //crop
        cy.get('[data-test="tab-workingarea-crop-top"]').clear().type("2");
        cy.get('[data-test="tab-workingarea-crop-left"]').clear().type("2");
        cy.get('[data-test="tab-workingarea-crop-bottom"]').clear().type("2");
        cy.get('[data-test="tab-workingarea-crop-right"]').clear().type("2");
        cy.get('[data-test="working-area-laser-button"]').click();
        cy.wait(2000);
        cy.focusReminder();
        cy.wait(2000);
        cy.get('[data-test="conversion-dialog-material-item"]')
            .contains("Paper")
            .click();
        cy.get('[id="material_color_1155cc"]').click();
        cy.wait(1000);
        cy.get('[id="material_thickness_0.4"]').click();
        // engrave parameters
        cy.get(
            '[data-test="conversion-dialog-show-advanced-settings"]'
        ).click();
        cy.get('[data-test="conversion-dialog-intensity-black"]')
            .clear()
            .type("95");
        cy.get('[data-test="conversion-dialog-intensity-white"]')
            .clear()
            .type("30");
        cy.get('[data-test="conversion-dialog-feedrate-white"]')
            .clear()
            .type("900");
        cy.get('[data-test="conversion-dialog-feedrate-black"]')
            .clear()
            .type("1500");
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
        cy.get(
            '[data-test="conversion-dialog-engraving-mode-recommended"]'
        ).dblclick({ force: true });
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
                cy.readFile("cypress/downloads/paris2.gco", {
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