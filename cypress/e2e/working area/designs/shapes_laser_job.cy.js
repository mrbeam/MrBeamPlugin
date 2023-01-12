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
        cy.deleteDownloadsFolder();
        cy.deleteGcoFile();
    });

    it("Add shapes - heart", function () {
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
        cy.get('[data-test="tab-workingarea-rotation"]')
            .filter(":visible")
            .clear()
            .type("-50.5");
        cy.get('[data-test="tab-workingarea-horizontal"]')
            .filter(":visible")
            .clear()
            .type("125.3 mm");
        cy.get('[data-test="tab-workingarea-vertical"]')
            .filter(":visible")
            .clear()
            .type("130.3 mm");
        cy.laserButtonClick();
        cy.get('[data-test="conversion-dialog-material-item"]')
            .contains("Cardboard, double wave")
            .click();
        cy.wait(1000);
        cy.get('[id="material_thickness_-1"]').click();
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
            .type("2");
        cy.get('[data-test="conversion-dialog-engraving-pierce-time"]')
            .clear()
            .type("5");
        cy.get('[data-test="conversion-dialog-line-distance-input"]')
            .clear()
            .type("0.5");
        cy.get('[data-test="conversion-dialog-line-dithering"]').click({
            force: true,
        });
        cy.get(
            '[data-test="conversion-dialog-engraving-mode-recommended"]'
        ).dblclick({ force: true });
        cy.get('[data-test="laser-job-start-button"]').dblclick();
        cy.wait(3000);
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
                cy.readFile("cypress/downloads/Heart.gco", {
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

    it("Add shapes - circle", function () {
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
        cy.get('[data-test="tab-workingarea-translation"]')
            .clear()
            .type("235.0, 138.0");
        cy.get('[data-test="tab-workingarea-rotation"]')
            .filter(":visible")
            .clear()
            .type("-50.5");
        cy.get('[data-test="tab-workingarea-horizontal"]')
            .filter(":visible")
            .clear()
            .type("125.3 mm");
        cy.get('[data-test="tab-workingarea-vertical"]')
            .filter(":visible")
            .clear()
            .type("130.3 mm");
        cy.laserButtonClick();
        cy.get('[data-test="conversion-dialog-material-item"]')
            .contains("Anodized Aluminum")
            .click();
        cy.get('[id="material_thickness_-1"]').click();
        cy.get('[data-test="conversion-dialog-intensity-black"]')
            .clear()
            .type("95");
        cy.get('[data-test="conversion-dialog-feedrate-black"]')
            .clear()
            .type("900");
        cy.get(
            '[data-test="conversion-dialog-show-advanced-settings"]'
        ).click();
        cy.get('[data-test="conversion-dialog-passes-input-engrave"]')
            .first()
            .clear()
            .type("2");
        cy.get('[data-test="conversion-dialog-engraving-pierce-time"]')
            .clear()
            .type("5");
        cy.get('[data-test="conversion-dialog-line-distance-input"]')
            .clear()
            .type("0.5");
        cy.get('[data-test="conversion-dialog-line-dithering"]').click({
            force: true,
        });
        cy.get(
            '[data-test="conversion-dialog-engraving-mode-recommended"]'
        ).dblclick({ force: true });
        cy.get('[data-test="laser-job-start-button"]').dblclick();
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
                cy.readFile("cypress/downloads/Circle.gco", {
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

    it("Add shapes - star", function () {
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
        cy.get('[data-test="tab-workingarea-translation"]')
            .filter(":visible")
            .clear()
            .type("235.0, 238.0");
        cy.get('[data-test="tab-workingarea-rotation"]')
            .filter(":visible")
            .clear()
            .type("250.5");
        cy.get('[data-test="tab-workingarea-horizontal"]')
            .filter(":visible")
            .clear()
            .type("225.3 mm");
        cy.get('[data-test="tab-workingarea-vertical"]')
            .filter(":visible")
            .clear()
            .type("230.3 mm");
        cy.laserButtonClick();
        cy.get('[data-test="conversion-dialog-material-item"]')
            .contains("Finn Cardboard")
            .click();
        cy.wait(1000);
        cy.get('[id="material_thickness_1.5"]').click();
        cy.get('[data-test="conversion-dialog-intensity-black"]')
            .clear()
            .type("95");
        cy.get('[data-test="conversion-dialog-feedrate-black"]')
            .clear()
            .type("1200");
        cy.get(
            '[data-test="conversion-dialog-show-advanced-settings"]'
        ).click();
        cy.get('[data-test="conversion-dialog-passes-input-engrave"]')
            .first()
            .clear()
            .type("2");
        cy.get('[data-test="conversion-dialog-engraving-pierce-time"]')
            .clear()
            .type("5");
        cy.get('[data-test="conversion-dialog-line-distance-input"]')
            .clear()
            .type("0.5");
        cy.get('[data-test="conversion-dialog-line-dithering"]').click({
            force: true,
        });
        cy.get(
            '[data-test="conversion-dialog-engraving-mode-recommended"]'
        ).dblclick({ force: true });
        cy.get('[data-test="laser-job-start-button"]').dblclick();
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
                cy.readFile("cypress/downloads/Star.gco", {
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

    it("Add shapes - line", function () {
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
        cy.get('[data-test="tab-workingarea-translation"]')
            .filter(":visible")
            .clear()
            .type("135.0, 138.0");
        cy.get('[data-test="tab-workingarea-rotation"]')
            .filter(":visible")
            .clear()
            .type("150.5");
        cy.get('[data-test="tab-workingarea-horizontal"]')
            .filter(":visible")
            .clear()
            .type("125.3 mm");
        cy.get('[data-test="tab-workingarea-vertical"]')
            .filter(":visible")
            .clear()
            .type("130.3 mm");
        cy.laserButtonClick();
        cy.get('[data-test="conversion-dialog-material-item"]')
            .contains("Polypropylene")
            .click();
        cy.get('[id="material_color_ff0000"]').click();
        cy.wait(1000);
        cy.get('[id="material_thickness_0.8"]').click();
        cy.get('[data-test="conversion-dialog-intensity-black"]')
            .clear()
            .type("95");
        cy.get('[data-test="conversion-dialog-intensity-white"]')
            .clear()
            .type("20");
        cy.get('[data-test="conversion-dialog-feedrate-white"]')
            .clear()
            .type("1000");
        cy.get('[data-test="conversion-dialog-feedrate-black"]')
            .clear()
            .type("1300");
        cy.get(
            '[data-test="conversion-dialog-show-advanced-settings"]'
        ).click();
        cy.get('[data-test="conversion-dialog-passes-input-engrave"]')
            .first()
            .clear()
            .type("2");
        cy.get('[data-test="conversion-dialog-engraving-pierce-time"]')
            .clear()
            .type("5");
        cy.get('[data-test="conversion-dialog-line-distance-input"]')
            .clear()
            .type("0.5");
        cy.get('[data-test="conversion-dialog-line-dithering"]').click({
            force: true,
        });
        cy.get(
            '[data-test="conversion-dialog-engraving-mode-recommended"]'
        ).dblclick({ force: true });
        cy.get('[data-test="laser-job-start-button"]').dblclick();
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
                cy.readFile("cypress/downloads/Line.gco", {
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

    it("Add shapes - rectangle", function () {
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-rect"]').click();
        cy.get('[data-test="quick-shape-rect-width"]').clear().type("60");
        cy.get('[data-test="quick-shape-rect-height"]').clear().type("60");
        cy.get('[data-test="quick-shape-rect-radius-input"]').realClick();
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
        cy.get('[data-test="tab-workingarea-translation"]')
            .filter(":visible")
            .clear()
            .type("135.0, 138.0");
        cy.get('[data-test="tab-workingarea-rotation"]')
            .filter(":visible")
            .clear()
            .type("150.5");
        cy.get('[data-test="tab-workingarea-horizontal"]')
            .filter(":visible")
            .clear()
            .type("125.3 mm");
        cy.get('[data-test="tab-workingarea-vertical"]')
            .filter(":visible")
            .clear()
            .type("130.3 mm");
        cy.laserButtonClick();
        cy.get('[data-test="conversion-dialog-material-item"]')
            .contains("Polypropylene")
            .click();
        cy.get('[id="material_color_ff0000"]').click();
        cy.wait(1000);
        cy.get('[id="material_thickness_0.8"]').click();
        cy.get('[data-test="conversion-dialog-intensity-black"]')
            .clear()
            .type("95");
        cy.get('[data-test="conversion-dialog-feedrate-black"]')
            .clear()
            .type("1300");
        cy.get(
            '[data-test="conversion-dialog-show-advanced-settings"]'
        ).click();
        cy.get('[data-test="conversion-dialog-passes-input-engrave"]')
            .first()
            .clear()
            .type("2");
        cy.get('[data-test="conversion-dialog-engraving-pierce-time"]')
            .clear()
            .type("5");
        cy.get('[data-test="conversion-dialog-line-distance-input"]')
            .clear()
            .type("0.5");
        cy.get('[data-test="conversion-dialog-line-dithering"]').click({
            force: true,
        });
        cy.get(
            '[data-test="conversion-dialog-engraving-mode-recommended"]'
        ).dblclick({ force: true });
        cy.get('[data-test="laser-job-start-button"]').dblclick();
        cy.wait(7000);
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
                cy.readFile("cypress/downloads/Rectangle.gco", {
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

    it("Add shapes - ok button", function () {
        cy.get('[data-test="working-area-tab-shape"]').click();
        cy.get('[data-test="quick-shape-modal-window"]').should("to.visible");
        cy.get('[data-test="quick-shape-done-button"]').click();
        cy.get('[data-test="quick-shape-modal-window"]').should("not.visible");
    });
});