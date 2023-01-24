describe("Laser Job - shapes", function () {
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
/*
    it("Heart shape", function () {
        // Add heart-shaped design
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-Heart"]').click();
        cy.get('[data-test="quick-shape-heart-width"]').clear().type("60");
        cy.get('[data-test="quick-shape-heart-height"]').clear().type("80");
        cy.get('[data-test="quick-shape-heart-range"]').realClick({
            position: "right",
        });
        cy.get('[data-test="quick-shape-color-picker-stroke"]').click();
        cy.get(
            '[data-test="quick-shape-color-picker-stroke"] > .track > canvas'
        ).realClick({ position: "left" });
        cy.get('[data-test="quick-shape-fill-input"]').click();
        cy.get('[data-test="quick-shape-color-picker-fill"]').click();
        cy.get(
            '[data-test="quick-shape-color-picker-fill"] > .track > canvas'
        ).realClick({ position: "top" });
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[id="translateHandle"]').move({
            deltaX: 33.9689,
            deltaY: 120.1241,
            force: true,
        });
        cy.designSettings();

        // Start the laser job
        cy.laserButtonClick();
        cy.selectMaterial();
        cy.get('[data-test="laser-job-start-button"]').dblclick();
        cy.wait(3000);
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
                cy.readFile("cypress/fixtures/Heart.gco", {
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
                    cy.readFile("cypress/downloads/Heart.gco", {
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

    it("Circle shape", function () {
        // Add circle-shaped design
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-circle"]').click();
        cy.get('[data-test="quick-shape-circle-radius-input"]')
            .clear()
            .type("60");
        cy.get('[data-test="quick-shape-color-picker-stroke"]').click();
        cy.get(
            '[data-test="quick-shape-color-picker-stroke"] > .track > canvas'
        ).realClick({ position: "right" });
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
                cy.readFile("cypress/fixtures/Circle.gco", {
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
                    cy.readFile("cypress/downloads/Circle.gco", {
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

    it("Star shape", function () {
        // Add star-shaped design
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-star"]').click();
        cy.get('[data-test="quick-shape-star-radius-input"]')
            .clear()
            .type("60");
        cy.get('[data-test="quick-shape-star-corners-input"]')
            .clear()
            .type("8");
        cy.get('[data-test="quick-shape-star-sharpness-input"]').realClick();
        cy.get('[data-test="quick-shape-color-picker-stroke"]').click();
        cy.get(
            '[data-test="quick-shape-color-picker-stroke"] > .track > canvas'
        ).realClick({ position: "top" });
        cy.get('[data-test="quick-shape-fill-input"]').click();
        cy.get('[data-test="quick-shape-color-picker-fill"]').click();
        cy.get(
            '[data-test="quick-shape-color-picker-fill"] > .track > canvas'
        ).realClick({ position: "top" });
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
                cy.readFile("cypress/fixtures/Star.gco", {
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
                    cy.readFile("cypress/downloads/Star.gco", {
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
                    ).click( {force: true} );
                    cy.get(
                        '[data-test="tab-designlib-filter-gcode-radio"]'
                    ).click( {force: true} );
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
*/
    it("Rectangle shape", function () {
        // Add rectangle-shaped design
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-rect"]').click();
        cy.get('[data-test="quick-shape-rect-width"]').clear().type("60");
        cy.get('[data-test="quick-shape-rect-height"]').clear().type("60");
        //cy.get('[data-test="quick-shape-rect-radius-input"]').realClick();
        cy.get('[data-test="quick-shape-color-picker-stroke"]').click();
        cy.get(
            '[data-test="quick-shape-color-picker-stroke"] > .track > canvas'
        ).realClick({ position: "left" });
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
        cy.wait(7000);
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
                cy.readFile("cypress/fixtures/Rectangle.gco", {
                    timeout: 40000,
                }).then((contentTestFile) => {
                    cy.get(
                        '[data-test="mrbeam-ui-index-design-library"]'
                    ).click( {force: true} );
                    cy.get(
                        '[data-test="tab-designlib-filter-gcode-radio"]'
                    ).click( {force: true} );
                    cy.get('[data-test="tab-designlib-mechinecode-file-card"]')
                        .first()
                        .click({ force: true });
                    cy.readFile("cypress/downloads/Rectangle.gco", {
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
/*
    it("Add shapes - ok button", function () {
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-modal-window"]').should("to.visible");
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="quick-shape-modal-window"]').should("not.visible");
    });
*/
});
