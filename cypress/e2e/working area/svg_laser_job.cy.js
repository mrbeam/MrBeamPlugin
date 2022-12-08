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
        cy.wait(5000);
    });

    it.only("Add svg file", function () {
        cy.get('[data-test="working-area-tab-file"]').click();
        cy.get('[data-test="tab-designlib-svg-preview-card"]').then(($elem) => {
            if (
                $elem
                    .find('[data-test="tab-designlib-svg-preview-card"]')
                    .filter(':contains("Focus_Tool_Mr_Beam_Laser_1.svg")')
                    .length
            ) {
            } else {
                const filepath = "Focus_Tool_Mr_Beam_Laser_1.svg";
                cy.get('.fileinput-button input[type="file"]').attachFile(
                    filepath
                );
                cy.wait(5000);
                cy.get('[data-test="tab-designlib-svg-preview-card"]')
                    .contains("Focus_Tool_Mr_Beam_Laser_1.svg")
                    .should("to.exist");
            }
        });
        cy.get('[data-test="tab-designlib-svg-preview-card"]')
            .filter(':contains("Focus_Tool_Mr_Beam_Laser_1.svg")')
            .click();
        cy.wait(3000);
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
        cy.get('[data-test="tab-workingarea-burger-menu"]').click();
        cy.get('[data-test="tab-workingarea-by-stroke-color"]').click();
        cy.get('[data-test="working-area-laser-button"]').click();
        cy.wait(2000);
        cy.focusReminder();
        cy.wait(2000);
        cy.get('[data-test="conversion-dialog-material-item"]')
            .contains("Cardboard, single wave")
            .click();
        cy.wait(1000);
        cy.get('[id="material_thickness_1.5"]').click();
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
        cy.get('[data-test="tab-designlib-mechinecode-file-card"]')
            .first()
            .find('[data-test="tab-designlib-mechinecode-file-icon-reorder"]')
            .click({ force: true })
            .invoke("prop", "innerText")
            .then((downloadFile) => {
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
            });
        cy.wait(7000);
        cy.readFile("cypress/fixtures/MrBeam_Lasers1.gco", {
            timeout: 40000,
        }).then((contentTestFile) => {
            cy.readFile("cypress/downloads/MrBeam_Lasers.gco", {
                timeout: 40000,
            }).then((contentFile) => {
                expect(contentTestFile).to.include(contentFile);
            });
        });
        cy.logout();
    });

    it("Add svg file", function () {
        cy.get('[data-test="working-area-tab-file"]').click();
        cy.get('[data-test="tab-designlib-svg-preview-card"]')
            .filter(':contains("Focus_Tool_Mr_Beam_Laser_1.svg")')
            .click();
        cy.wait(3000);
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
        cy.get('[data-test="tab-workingarea-burger-menu"]').click();
        cy.get('[data-test="tab-workingarea-horizontally"]')
            .filter(":visible")
            .click();
        cy.logout();
    });

    it("Add svg file", function () {
        cy.get('[data-test="working-area-tab-file"]').click();
        cy.get('[data-test="tab-designlib-svg-preview-card"]')
            .filter(':contains("Focus_Tool_Mr_Beam_Laser_1.svg")')
            .click();
        cy.wait(3000);
        cy.get('[data-test="tab-workingarea-move"]').click({ force: true });
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
        cy.get('[data-test="tab-workingarea-burger-menu"]').click();
        cy.get('[data-test="tab-workingarea-vertically"]')
            .filter(":visible")
            .click();
        cy.get('[data-test="tab-workingarea-burger-menu"]').first().click();
        cy.get('[data-test="tab-workingarea-into-shapes"]')
            .filter(":visible")
            .click({
                force: true,
            });
        cy.get('[data-test="tab-workingarea-detail-information"]').should(
            ($elem) => {
                expect($elem).to.have.length(12);
            }
        );
        cy.logout();
    });

    it("Add svg file  ", function () {
        cy.get('[data-test="working-area-tab-file"]').click();
        cy.get('[data-test="tab-designlib-svg-preview-card"]')
            .filter(':contains("Focus_Tool_Mr_Beam_Laser_1.svg")')
            .click();
        cy.wait(3000);
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
        cy.get('[data-test="tab-workingarea-burger-menu"]').click();
        cy.get('[data-test="tab-workingarea-vertically"]')
            .filter(":visible")
            .click();
        cy.get('[data-test="tab-workingarea-burger-menu"]').first().click();
        cy.get('[data-test="tab-workingarea-into-shapes"]')
            .filter(":visible")
            .click();
        cy.get('[data-test="tab-workingarea-burger-menu"]').last().click();
        cy.get('[data-test="tab-workingarea-horizontally"]')
            .filter(":visible")
            .click({
                force: true,
            });
        cy.get('[data-test="tab-workingarea-burger-menu"]').eq(10).click();
        cy.get('[data-test="tab-workingarea-by-stroke-color"]')
            .filter(":visible")
            .click({
                force: true,
            });
        cy.get('[data-test="tab-workingarea-detail-information"]').should(
            ($elem) => {
                expect($elem).to.have.length(13);
            }
        );
        cy.logout();
    });
});
