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
        cy.visit(this.testData.url_laser);
        cy.deleteDownloadsFolder();
        cy.wait(5000);
    });

    it("Add svg file", function () {
        cy.get('[data-test="working-area-tab-file"]').click();
        cy.get('[data-test="tab-designlib-files-list"]').then(($elem) => {
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
        cy.laserButtonClick();
        cy.get('[data-test="conversion-dialog-material-item"]')
            .contains("Cardboard, single wave")
            .click();
        cy.wait(1000);
        cy.get('[id="material_thickness_1.5"]').click();
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
                cy.wait(7000);
                cy.readFile(
                    "cypress/fixtures/Focus_Tool_Mr_Beam_Laser_1.svg.5x.gco",
                    {
                        timeout: 40000,
                    }
                ).then((contentTestFile) => {
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
                            let bodyNoComments = $body.replace(/^;.*$/gm, "");
                            let contentTestFileNoComments =
                                contentTestFile.replace(/^;.*$/gm, "");
                            expect(bodyNoComments).to.equal(
                                contentTestFileNoComments
                            );
                        });
                });
            });

        cy.logout();
    });

    it("Split SVG by every option", function () {
        cy.get('[data-test="working-area-tab-file"]').click();
        cy.get('[data-test="tab-designlib-svg-preview-card"]')
            .filter(':contains("Focus_Tool_Mr_Beam_Laser_1.svg")')
            .click();
        cy.wait(3000);
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
