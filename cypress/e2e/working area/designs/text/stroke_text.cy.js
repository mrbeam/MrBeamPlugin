describe.skip("Laser Job - quick text", function () {
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
        cy.deleteDownloadsFolder();
        cy.deleteGcoFile();
    });

    //Test quick text stroke straight, concave down and concave up
    it("Quick text stroke", function () {
        cy.wait(3000);

        // Add 1st design stroke text straight
        cy.get('[data-test="working-area-tab-text"]').click();
        cy.get('[data-test="quick-text-modal-text-input"]').type(
            "StrokeTextStraight"
        );
        cy.get('[data-test="quick-text-color-picker-fill"]').click();
        cy.get('[data-test="quick-text-modal-text-straight"]').click();
        cy.get('[data-test="quick-text-stroke-input"]').click();
        //cy.get('[id="qt_colorPicker_stroke"]').click();
        //cy.get('[id="qt_colorPicker_stroke"] > .track > canvas').realClick({
        //    position: "top",
        //});
        cy.get('[data-test="quick-text-font-button-left"]').last().click();
        cy.get('[data-test="quick-text-done-button"]').click();
        cy.get('[id="translateHandle"]').move({
            deltaX: 433.9689,
            deltaY: 220.1241,
            force: true,
        });
        cy.designSettings();

        // Add 2nd design stroke text concave down
        cy.get('[data-test="working-area-tab-text"]').click();
        cy.get('[data-test="quick-text-modal-text-input"]').type(
            "StrokeTextConcaveDown"
        );
        cy.get('[data-test="quick-text-modal-text-cw"]').click();
        cy.get('[data-test="quick-text-color-picker-fill"]').click();
        cy.get('[data-test="quick-text-stroke-input"]').click();
        //cy.get('[id="qt_colorPicker_stroke"]').click();
        cy.get('[id="qt_colorPicker_stroke"] > .track > canvas').realClick({
            position: "top",
        });
        cy.get('[data-test="quick-text-circle-input"]').trigger("right");
        cy.get('[data-test="quick-text-font-button-left"]').last().click();
        cy.get('[data-test="quick-text-done-button"]').click();
        cy.get('[id="translateHandle"]').move({
            deltaX: 50.9689,
            deltaY: 220.1241,
            force: true,
        });
        cy.designSettings();

        // Add 3rd design stroke text concave up
        cy.get('[data-test="working-area-tab-text"]').click();
        cy.get('[data-test="quick-text-modal-text-input"]').type(
            "StrokeTextConcaveUp"
        );
        cy.get('[data-test="quick-text-font-button-left"]').last().dblclick();
        cy.get('[data-test="quick-text-modal-text-ccw"]').click();
        cy.get('[data-test="quick-text-color-picker-fill"]').click();
        cy.get('[data-test="quick-text-stroke-input"]').click();
        //cy.get('[id="qt_colorPicker_stroke"]').click();
        cy.get('[id="qt_colorPicker_stroke"] > .track > canvas').realClick({
            position: "left",
        });
        cy.get('[data-test="quick-text-circle-input"]').trigger("left");
        cy.get('[data-test="quick-text-font-button-left"]').last().click();
        cy.get('[data-test="quick-text-done-button"]').click();
        cy.get('[id="translateHandle"]').move({
            deltaX: 70.9689,
            deltaY: 80.1241,
            force: true,
        });
        cy.designSettings();

        // Start the laser job
        cy.laserButtonClick();
        cy.selectMaterial();
        cy.get('[data-test="laser-job-start-button"]').dblclick({
            force: true,
        });
        cy.get(".alert-success").should("to.exist", "Preparation done");
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
                cy.readFile("cypress/fixtures/StrokeTextStraight_2more.gco", {
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
                    cy.readFile(
                        "cypress/downloads/StrokeTextStraight_2more.gco",
                        {
                            timeout: 40000,
                        }
                    ).then((contentDownloadFile) => {
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

    it("Add text - ok button", function () {
        cy.get('[data-test="working-area-tab-text"]').click();
        cy.get('[data-test="quick-text-modal-window"]').should("to.visible");
        cy.get('[data-test="quick-text-done-button"]').click();
        cy.get('[data-test="quick-text-modal-window"]').should("not.visible");
        cy.logout();
    });
});
