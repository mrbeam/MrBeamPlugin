describe("Menu burger", function () {
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
    });
    it("Lasersafety", function () {
        cy.get('[data-test="mrbeam-ui-index-tab-laser-safety"]').click();
        cy.get('[id="lasersafety_overlay"]').should("to.visible");
        cy.get(".modal-footer").filter(":visible").find(".btn-danger").click();
    });
    it("Fullscreen", function () {
        cy.get('[data-test="mrbeam-ui-index-tab-fullscreen-go"]').realClick();
        cy.document().its("fullscreenElement").should("not.equal", null);
        cy.get('[data-test="mrbeam-ui-index-menu-burger"]').click();
        cy.get('[data-test="mrbeam-ui-index-tab-manual-user"]').realClick();
        cy.document().its("fullscreenElement").should("equal", null);
    });
    it("Manual User", function () {
        cy.get('[data-test="mrbeam-ui-index-tab-manual-user"]')
            .click()
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    it("Quickstart Guide", function () {
        cy.get('[data-test="mrbeam-ui-index-tab-manual-user"]')
            .first()
            .click()
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });

    it("Find mr beam", function () {
        cy.get('[data-test="mrbeam-ui-index-tab-laser-find-mr-beam"]')
            .last()
            .click()
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    it.only("Support", function () {
        cy.get('[data-test="mrbeam-ui-index-tab-support"]').click();
        cy.get('[id="support_overlay"]').should("to.exist");
        cy.get(".wizard-table > tbody > :nth-child(2) > :nth-child(1) > a")
            .click()
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.get(".wizard-table > tbody > :nth-child(2) > :nth-child(2) > a")
            .click()
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.get(
            ".wizard-table > tbody > :nth-child(2) > :nth-child(3) > a"
        ).click();
        cy.get(".hopscotch-bubble-container").should("to.exist");
        cy.get(".hopscotch-content > ul > .show_only_online > a")
            .click()
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.get(".hopscotch-cta").click();
        cy.get(".hopscotch-bubble-container").should("not.exist");
    });
});
