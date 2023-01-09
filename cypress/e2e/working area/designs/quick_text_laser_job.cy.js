describe("Laser Job - quick text", function () {
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

    it("Add texts", function () {
        cy.wait(3000);
        cy.get('[data-test="working-area-tab-text"]').click();
        cy.get('[data-test="quick-text-modal-text-input"]').type("MrBeam");
        cy.get('[data-test="quick-text-modal-text-cw"]').click();
        cy.get('[data-test="quick-text-color-picker-fill"]').click();
        cy.get(
            '[data-test="quick-text-color-picker-fill"] > .track > canvas'
        ).realClick({ position: "top" });
        cy.get('[data-test="quick-text-stroke-input"]').click("center");
        cy.get(
            '[data-test="quick-text-color-picker-stroke"] > .track > canvas'
        ).realClick({ position: "left" });
        cy.get('[data-test="quick-text-circle-input"]').trigger("right");
        cy.get('[data-test="quick-text-font-button-left"]').last().click();
        cy.get('[data-test="quick-text-done-button"]').click();
        cy.get('[id="translateHandle"]').move({
            deltaX: 433.9689,
            deltaY: 220.1241,
            force: true,
        });
        cy.get('[data-test="tab-workingarea-rotation"]')
            .filter(":visible")
            .clear()
            .type("-50.5");
        cy.get('[data-test="tab-workingarea-horizontal"]')
            .filter(":visible")
            .clear()
            .type("116.3 mm");
        cy.get('[data-test="tab-workingarea-vertical"]')
            .filter(":visible")
            .clear()
            .type("132.3 mm");
        cy.laserButtonClick();
        cy.wait(2000);
        cy.focusReminder();
        cy.wait(2000);
        cy.get('[data-test="conversion-dialog-material-item"]')
            .contains(/^Leather$/)
            .click({ force: true });
        cy.get('[id="material_color_b45f06"]').click();
        cy.wait(1000);
        cy.get('[id="material_thickness_0.8"]').click();
        cy.get('[data-test="conversion-dialog-intensity-black"]')
            .clear()
            .type("70");
        cy.get('[data-test="conversion-dialog-intensity-white"]')
            .clear()
            .type("25");
        cy.get('[data-test="conversion-dialog-feedrate-white"]')
            .clear()
            .type("1500");
        cy.get('[data-test="conversion-dialog-feedrate-black"]')
            .clear()
            .type("3000");
        cy.get(
            '[data-test="conversion-dialog-show-advanced-settings"]'
        ).click();
        cy.get('[data-test="conversion-dialog-passes-input-engrave"]')
            .first()
            .clear()
            .type("1");
        cy.get('[data-test="conversion-dialog-engraving-pierce-time"]')
            .clear()
            .type("2");
        cy.get('[data-test="conversion-dialog-line-distance-input"]')
            .clear()
            .type("1");
        cy.get('[data-test="conversion-dialog-engraving-mode-basic"]').dblclick(
            { force: true }
        );
        cy.get('[data-test="laser-job-start-button"]').dblclick();
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
                cy.readFile("cypress/downloads/MrBeam.gco", {
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

    it("Add texts 2", function () {
        cy.wait(3000);
        cy.get('[data-test="working-area-tab-text"]').click();
        cy.get('[data-test="quick-text-modal-text-input"]').type("Lasers");
        cy.get('[data-test="quick-text-modal-text-ccw"]').click();
        cy.get('[data-test="quick-text-color-picker-fill"]').click();
        cy.get(
            '[data-test="quick-text-color-picker-fill"] > .track > canvas'
        ).realClick({ position: "bottom" });
        cy.get('[data-test="quick-text-stroke-input"]').click("center");
        cy.get(
            '[data-test="quick-text-color-picker-stroke"] > .track > canvas'
        ).realClick({ position: "right" });
        cy.get('[data-test="quick-text-circle-input"]').trigger("right");
        cy.get('[data-test="quick-text-font-button-left"]').last().click();
        cy.get('[data-test="quick-text-done-button"]').click();
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
        cy.focusReminder();
        cy.get('[data-test="conversion-dialog-material-item"]')
            .contains("Cork")
            .click({ force: true });
        cy.wait(1000);
        cy.get('[data-test="conversion-dialog-intensity-black"]')
            .clear()
            .type("70");
        cy.get('[data-test="conversion-dialog-feedrate-black"]')
            .clear()
            .type("3000");
        cy.get(
            '[data-test="conversion-dialog-show-advanced-settings"]'
        ).click();
        cy.get('[data-test="conversion-dialog-passes-input-engrave"]')
            .first()
            .clear()
            .type("1");
        cy.get('[data-test="conversion-dialog-engraving-pierce-time"]')
            .clear()
            .type("2");
        cy.get('[data-test="conversion-dialog-line-distance-input"]')
            .clear()
            .type("1");
        cy.get('[data-test="conversion-dialog-engraving-mode-basic"]').dblclick(
            { force: true }
        );
        cy.get('[data-test="laser-job-start-button"]').dblclick();
        cy.wait(3000);
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
                cy.readFile("cypress/downloads/Lasers.gco", {
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

    it("Add texts 3", function () {
        cy.wait(3000);
        cy.get('[data-test="working-area-tab-text"]').click();
        cy.get('[data-test="quick-text-modal-text-input"]').type(
            "MrBeam Lasers"
        );
        cy.get('[data-test="quick-text-font-button-left"]').last().dblclick();
        cy.get('[data-test="quick-text-modal-text-straight"]').click();
        cy.get('[data-test="quick-text-color-picker-fill"]').click();
        cy.get(
            '[data-test="quick-text-color-picker-fill"] > .track > canvas'
        ).realClick({ position: "top" });
        cy.get('[data-test="quick-text-stroke-input"]').click("center");
        cy.get(
            '[data-test="quick-text-color-picker-stroke"] > .track > canvas'
        ).realClick({ position: "bottom" });
        cy.get('[data-test="quick-text-done-button"]').click();
        cy.get('[data-test="tab-workingarea-translation"]')
            .filter(":visible")
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
        cy.focusReminder();
        cy.get('[data-test="conversion-dialog-material-item"]')
            .contains("Foam")
            .click({ force: true });
        cy.wait(1000);
        cy.get('[id="material_thickness_10"]').click();
        cy.get('[data-test="conversion-dialog-intensity-black"]')
            .clear()
            .type("70");
        cy.get('[data-test="conversion-dialog-feedrate-black"]')
            .clear()
            .type("3000");
        cy.get(
            '[data-test="conversion-dialog-show-advanced-settings"]'
        ).click();
        cy.get('[data-test="conversion-dialog-passes-input-engrave"]')
            .first()
            .clear()
            .type("1");
        cy.get('[data-test="conversion-dialog-engraving-pierce-time"]')
            .clear()
            .type("2");
        cy.get('[data-test="conversion-dialog-line-distance-input"]')
            .clear()
            .type("1");
        cy.get(
            '[data-test="conversion-dialog-engraving-mode-recommended"]'
        ).dblclick({ force: true });
        cy.get('[data-test="laser-job-start-button"]').dblclick();
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
                cy.readFile("cypress/downloads/MrBeam_Lasers.gco", {
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

    it("Add text - ok button", function () {
        cy.get('[data-test="working-area-tab-text"]').click();
        cy.get('[data-test="quick-text-modal-window"]').should("to.visible");
        cy.get('[data-test="quick-text-done-button"]').click();
        cy.get('[data-test="quick-text-modal-window"]').should("not.visible");
        cy.logout();
    });
});
