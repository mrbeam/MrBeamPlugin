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
    it("Download - octoprint", function () {
        cy.get('[id="settings_logs_link"]').click();
        cy.window()
            .document()
            .then(function (doc) {
                doc.addEventListener("click", () => {
                    setTimeout(function () {
                        doc.location.reload();
                    }, 5000);
                });
                cy.get(
                    '[title="octoprint.log"] > .settings_logs_action > .fa-download'
                ).click();
                cy.verifyDownload("octoprint.log");
            });
    });
    it("Download frontend", function () {
        cy.get('[id="settings_logs_link"]').click();
        cy.window()
            .document()
            .then(function (doc) {
                doc.addEventListener("click", () => {
                    setTimeout(function () {
                        doc.location.reload();
                    }, 5000);
                });
                cy.get(
                    '[title="frontend.log"] > .settings_logs_action > .fa-download'
                ).click();
                cy.verifyDownload("frontend.log");
            });
    });
    it("Download - software plugin", function () {
        cy.get('[id="settings_logs_link"]').click();
        cy.window()
            .document()
            .then(function (doc) {
                doc.addEventListener("click", () => {
                    setTimeout(function () {
                        doc.location.reload();
                    }, 5000);
                });
                cy.get(
                    '[title="plugin_softwareupdate_console.log"] > .settings_logs_action > .fa-download'
                ).click();
                cy.verifyDownload("plugin_softwareupdate_console.log");
            });
    });
    it("Name (ascending)", function () {
        cy.get('[id="settings_logs_link"]').click();
        let elem1 = [];
        cy.get("thead > tr > .settings_logs_name").each((elements) => {
            elem1.push(elements.text());
        });
        cy.wrap(elem1).should("to.exist");
        cy.get("a").contains("Name (ascending)").last().click();
        let elem = [];
        cy.get("thead > tr > .settings_logs_name").each((elements) => {
            elem.push(elements.text());
        });
        cy.wrap(elem).should("not.equal", elem1.sort());
    });
    it("Modification date (descending)", function () {
        cy.get('[id="settings_logs_link"]').click();
        let elem1 = [];
        cy.get("thead > tr > .settings_logs_date").each((elements) => {
            elem1.push(elements.text());
        });
        cy.wrap(elem1).should("to.exist");
        cy.get("a").contains("Modification date (descending)").last().click();
        let elem = [];
        cy.get("thead > tr > .settings_logs_date").each((elements) => {
            elem.push(elements.text());
        });
        cy.wrap(elem).should("not.equal", elem1.sort());
    });
    it("Size (descending)", function () {
        cy.get('[id="settings_logs_link"]').click();
        let elem1 = [];
        cy.get("thead > tr > .settings_logs_size").each((elements) => {
            elem1.push(elements.text());
        });
        cy.wrap(elem1).should("to.exist");
        cy.get("a").contains("Size (descending)").last().click();
        let elem = [];
        cy.get("thead > tr > .settings_logs_size").each((elements) => {
            elem.push(elements.text());
        });
        cy.wrap(elem).should("not.equal", elem1.sort());
    });
});
