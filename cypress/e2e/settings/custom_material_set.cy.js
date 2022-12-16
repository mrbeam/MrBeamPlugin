describe("Navbar icons", function () {
    beforeEach(function () {
        cy.fixture("test-data").then(function (testData) {
            this.testData = testData;
        });
    });

    beforeEach(function () {
        cy.visit(this.testData.url_laser);
        cy.wait(10000);
        cy.loginLaser(this.testData.email, this.testData.password);
        cy.get('[data-test="mrbeam-ui-index-menu-burger"]').click();
        cy.get('[data-test="mrbeam-ui-index-tab-settings"]').click({
            force: true,
        });
    });
    it("Knowledge base", function () {
        cy.get('[id="settings_plugin_mrbeam_custom_material_link"]').click();
        cy.get('[data-test="custom-material-learn-how"] > a')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
    });
    it("Download backup", function () {
        cy.get('[id="settings_plugin_mrbeam_custom_material_link"]').click();
        cy.get('[data-test="custom-material-settings-backup"]')
            .click()
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

                        cy.verifyDownload(downloadFile);
                    });
            });
    });
    it("Restore", function () {
        cy.get('[id="settings_plugin_mrbeam_custom_material_link"]').click();
        const file = "MrBeam-CustomMaterialBackup-2022-12-08.json";
        cy.get('[data-test="custom-material-settings-input-file"]').attachFile(
            file
        );
        cy.contains("Custom Material Settings restored.").should("to.exist");
    });
});
