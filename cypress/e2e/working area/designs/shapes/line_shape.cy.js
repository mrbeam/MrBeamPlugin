describe.skip("Laser Job - shapes", function () {
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

    it("Line shape", function () {
        // Add line-shaped design
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-line"]').click();
        cy.get('[data-test="quick-shape-line-length-input"]')
            .clear()
            .type("60");
        cy.get('[data-test="quick-shape-color-picker-stroke"]').click();
        cy.get(
            '[data-test="quick-shape-color-picker-stroke"] > .track > canvas'
        ).realClick({ position: "bottom" });
        cy.get('[data-test="quick-shape-fill-input"]').click();
        cy.get('[data-test="quick-shape-color-picker-fill"]').click();
        cy.get(
            '[data-test="quick-shape-color-picker-fill"] > .track > canvas'
        ).realClick({ position: "bottom" });
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.designSettings();

        // Start the laser job
        cy.laserButtonClick();
        cy.selectMaterial();
        cy.get('[data-test="laser-job-start-button"]').dblclick();
        cy.get(".modal-scrollable").click({ force: true });
        cy.get('[data-test="mrbeam-ui-index-design-library"]').click();
        cy.get('[data-test="mrbeam-ui-index-design-library"]').click();
        cy.get('[data-test="tab-designlib-filter-gcode-radio"]').click();
        cy.wait(3000);

        // Download the GCODE file and compare it
        cy.get('[data-test="tab-designlib-mechinecode-file-card"]')
            .first()
            .find('[data-test="tab-designlib-mechinecode-file-icon-reorder"]')
            .click({ force: true })
            .invoke("prop", "innerText")
            .then((downloadFile) => {
                //cy.intercept(
                //  "GET",
                //`http://localhost:5002/downloads/files/local/${downloadFile}*`
                //).as("file");
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
                cy.readFile("cypress/fixtures/Line.gco", {
                    timeout: 40000,
                }).then((contentTestFile) => {
                    cy.get(
                        '[data-test="mrbeam-ui-index-design-library"]'
                    ).click({ force: true });
                    cy.get(
                        '[data-test="tab-designlib-filter-gcode-radio"]'
                    ).click({ force: true });
                    cy.get('[data-test="tab-designlib-mechinecode-file-card"]')
                        .first()
                        .click({ force: true });
                    cy.readFile("cypress/downloads/Line.gco", {
                        timeout: 40000,
                    }).then((contentDownloadFile) => {
                        let contentTestDownloadNoComments = contentDownloadFile
                            .replace(/^;.*$/gm, "")
                            .trimEnd();
                        let contentTestFileNoComments = contentTestFile
                            .replace(/^;.*$/gm, "")
                            .trimEnd();
                        expect(contentTestDownloadNoComments).to.equal(
                            contentTestFileNoComments
                        );
                    });
                });
            });
        cy.logout();
    });

    it("Add shapes - ok button", function () {
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-modal-window"]').should("to.visible");
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="quick-shape-modal-window"]').should("not.visible");
    });
});
