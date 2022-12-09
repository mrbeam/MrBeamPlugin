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
        cy.get(".icon-remove").click({ force: true, multiple: true });
        cy.get('[data-test="mrbeam-ui-index-menu-burger"]').click();
    });
    it("Lasersafety", function () {
        cy.get('[data-test="mrbeam-ui-index-tab-laser-safety"]').click();
        cy.get('[id="lasersafety_overlay"]').should("to.visible");
        cy.get(".modal-footer").filter(":visible").find(".btn-danger").click();
    });
    it("Fullscreen", function () {
        cy.get("#go_fullscreen_menu_item").realClick();
        cy.document().its("fullscreenElement").should("not.equal", null);
        cy.get('[data-test="mrbeam-ui-index-menu-burger"]').click();
        cy.get("#exit_fullscreen_menu_item").realClick();
        cy.document().its("fullscreenElement").should("equal", null);
    });
    it("Manual User", function () {
        cy.get(".dropdown-menu > :nth-child(7) > a")
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
        cy.get(".dropdown-menu > :nth-child(8) > a")
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
        cy.get(".dropdown-menu > :nth-child(12) > a")
            .click()
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    it("Support", function () {
        cy.get("#support_menu_item").click();
        cy.get('[id="support_overlay"]').should("to.exist");
    });
});
