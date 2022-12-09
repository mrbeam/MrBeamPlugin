describe("Software update", function () {
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

    it("Link this link", function () {
        cy.get('[id="settings_plugin_softwareupdate_link"]').click();
        cy.get('[data-test="software-channel-stable-channel-link"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
    });

    it("Link what's new in the beta channel", function () {
        cy.get('[id="settings_plugin_softwareupdate_link"]').click();
        cy.get('[data-test="software-channel-beta-channel-link"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
    });
    it("Link OctoPrint", function () {
        cy.get('[id="settings_plugin_softwareupdate_link"]').click();
        cy.get(
            '[title="OctoPrint"] > .settings_plugin_softwareupdate_column_information > .muted > [data-bind="visible: releaseNotes"] > a'
        )
            .if("visible")
            .then(() => {
                cy.get(
                    '[title="OctoPrint"] > .settings_plugin_softwareupdate_column_information > .muted > [data-bind="visible: releaseNotes"] > a'
                )
                    .invoke("attr", "href")
                    .then((myLink) => {
                        cy.request(myLink).then((resp) => {
                            expect(resp.status).to.eq(200);
                        });
                    });
            });
    });
    it("Link Find My Mr Beam", function () {
        cy.get('[id="settings_plugin_softwareupdate_link"]').click();
        cy.get(
            '[title="OctoPrint-FindMyMrBeam"] > .settings_plugin_softwareupdate_column_information > .muted > [data-bind="visible: releaseNotes"] > a'
        )
            .if("visible")
            .then(() => {
                cy.get(
                    '[title="OctoPrint-FindMyMrBeam"] > .settings_plugin_softwareupdate_column_information > .muted > [data-bind="visible: releaseNotes"] > a'
                )
                    .invoke("attr", "href")
                    .then((myLink) => {
                        cy.request(myLink).then((resp) => {
                            expect(resp.status).to.eq(200);
                        });
                    });
            });
    });
    it("Link OctoPrint Netconnected Plugin", function () {
        cy.get('[id="settings_plugin_softwareupdate_link"]').click();
        cy.get(
            '[title="OctoPrint-Netconnectd Plugin"] > .settings_plugin_softwareupdate_column_information > .muted > [data-bind="visible: releaseNotes"] > a'
        )
            .if("visible")
            .then(() => {
                cy.get(
                    '[title="OctoPrint-Netconnectd Plugin"] > .settings_plugin_softwareupdate_column_information > .muted > [data-bind="visible: releaseNotes"] > a'
                )
                    .invoke("attr", "href")
                    .then((myLink) => {
                        cy.request(myLink).then((resp) => {
                            expect(resp.status).to.eq(200);
                        });
                    });
            });
    });
    it("Link Mr Beam", function () {
        cy.get('[id="settings_plugin_softwareupdate_link"]').click();
        cy.get(
            '[title=" MrBeam Plugin"] > .settings_plugin_softwareupdate_column_information > .muted > [data-bind="visible: releaseNotes"] > a'
        )
            .if("visible")
            .then(() => {
                cy.get(
                    '[title=" MrBeam Plugin"] > .settings_plugin_softwareupdate_column_information > .muted > [data-bind="visible: releaseNotes"] > a'
                )
                    .invoke("attr", "href")
                    .then((myLink) => {
                        cy.request(myLink).then((resp) => {
                            expect(resp.status).to.eq(200);
                        });
                    });
            });
    });
    it("Software channel - beta", function () {
        cy.get('[id="settings_plugin_softwareupdate_link"]').click();
        cy.get('[data-test="software-channel-select-bata-stable"]').select(
            "BETA"
        );
        cy.reload(true);
        cy.wait(2000);
        cy.get(".navbar-header > span > a")
            .contains("BETA")
            .should("to.visible");
    });
    it("Software channel - stable", function () {
        cy.get('[id="settings_plugin_softwareupdate_link"]').click();
        cy.get('[data-test="software-channel-select-bata-stable"]').select(
            "PROD"
        );
        cy.reload(true);
        cy.wait(2000);
        cy.get(".navbar-header > span > a").should("not.exist");
    });
    it("Software channel", function () {
        cy.get('[id="settings_plugin_softwareupdate_link"]').click();

        cy.get(".sticky-footer").click();
        cy.contains("Everything is up-to-date")
            .if("exist")
            .should("exist")
            .else("to.visible")
            .contains("Update Available")
            .should("exist");
    });
});
