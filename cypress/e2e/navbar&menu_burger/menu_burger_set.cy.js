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
        cy.logout();
    });
    it.skip("Fullscreen", function () {
        cy.get('[data-test="mrbeam-ui-index-tab-fullscreen-go"]').realClick();
        cy.document().its("fullscreenElement").should("not.equal", null);
        cy.get('[data-test="mrbeam-ui-index-menu-burger"]').click();
        cy.get('[data-test="mrbeam-ui-index-tab-fullscreen-exit"]').realClick();
        cy.document().its("fullscreenElement").should("equal", null);
        cy.logout();
    });
    it("Manual User", function () {
        cy.get('[data-test="mrbeam-ui-index-tab-manual-user"]')
            .contains("User Manual")
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
            .contains("Quickstart Guide")
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
    it("Support", function () {
        cy.get('[data-test="mrbeam-ui-index-tab-support"]').click();
        cy.get('[id="support_overlay"]').should("to.exist");
        cy.get('[id="support_overlay"]')
            .contains("Youtube channel")
            .click()
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.get('[id="support_overlay"]')
            .contains("Knowledge Base")
            .click()
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.get('[id="support_overlay"]').contains("guided tour").click();
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
        cy.get('[id="support_overlay"]').find(".close").click();
        cy.logout();
    });

    it("Guided Tour - When tour is started then it will run trough till end", function () {
        cy.get('[data-test="mrbeam-ui-index-tab-guided-tour"]').click();
        cy.get(".hopscotch-bubble-container").should("be.visible");
        cy.get(".hopscotch-bubble-number").should("have.text", 1);
        cy.get(".hopscotch-next").click();

        //TODO currently skipped as the homing button is not visible in the guided tour
        cy.get(".hopscotch-bubble-container").should("be.visible");
        cy.get(".hopscotch-bubble-number").should("have.text", 2);
        cy.get('[data-test="mrbeam-ui-homing_overlay_homing_btn"]').click();

        //TODO currently skipped as the homing button is not visible in the guided tour
        cy.get(".hopscotch-bubble-number").should("have.text", 3);
        cy.get(".hopscotch-next").click();

        cy.get(".hopscotch-bubble-container").should("be.visible");
        cy.get(".hopscotch-bubble-number").should("have.text", 4);
        cy.get(".hopscotch-next").click();

        cy.get(".hopscotch-bubble-container").should("be.visible");
        cy.get(".hopscotch-bubble-number").should("have.text", 5);
        cy.get('[data-test="tab-designlib-filter-design-radio"]').should(
            "be.checked"
        );
        cy.get('[data-test="mrbeam-ui-index-design-library"]').click();

        cy.get('[data-test="tab-designlib-files-list"]').should("be.visible");
        cy.get(".hopscotch-bubble-container").should("be.visible");
        cy.get(".hopscotch-bubble-number").should("have.text", 6);
        cy.get(
            '[data-test="tab-designlib-svg-preview-card"][mrb_name="Schluesselanhaenger.svg"]'
        ).click();

        cy.get('[data-test="mrbeam-ui-tab-workingarea"]').should("be.visible");
        cy.get(".hopscotch-bubble-container").should("be.visible");
        cy.get(".hopscotch-bubble-number").should("have.text", 7);
        cy.get(".hopscotch-next").click();

        cy.get(".hopscotch-bubble-container").should("be.visible");
        cy.get(".hopscotch-bubble-number").should("have.text", 8);
        cy.get('[data-test="working-area-laser-button"]').click();

        cy.get(".hopscotch-bubble-container").should("be.visible");
        cy.get(".hopscotch-bubble-number").should("have.text", 9);
        cy.get('[data-test="mrbeam-ui-start_job_btn_focus_reminder"]').click();

        cy.get('[data-test="conversion-dialog-vector-graphics"]').should(
            "be.visible"
        );
        cy.get(".hopscotch-bubble-container").should("be.visible");
        cy.get(".hopscotch-bubble-number").should("have.text", 10);
        cy.get(
            '[data-test="conversion-dialog-material-item"][mrb_name="/plugin/mrbeam/static/img/materials/Felt.jpg"]'
        ).click();

        cy.get('[data-test="conversion-dialog-vector-graphics"]').should(
            "be.visible"
        );
        cy.get(".hopscotch-bubble-container").should("be.visible");
        cy.get(".hopscotch-bubble-number").should("have.text", 11);
        cy.get(
            '[data-test="conversion-dialog-material-color"]#material_color_eb5a3e'
        ).click();

        cy.get('[data-test="conversion-dialog-vector-graphics"]').should(
            "be.visible"
        );
        cy.get(".hopscotch-bubble-container").should("be.visible");
        cy.get(".hopscotch-bubble-number").should("have.text", 12);
        cy.get(
            '[data-test="conversion-dialog-thickness-sample"]#material_thickness_3'
        ).click();

        cy.get('[data-test="conversion-dialog-vector-graphics"]').should(
            "be.visible"
        );
        cy.get(".hopscotch-bubble-container").should("be.visible");
        cy.get(".hopscotch-bubble-number").should("have.text", 13);
        cy.get('[data-test="laser-job-start-button"]').click();

        cy.get('[data-test="conversion-dialog-vector-graphics"]').should(
            "be.visible"
        );
        cy.get(
            '[data-test="mrbeam-ui-conversion-dialoge-header-preparing"]'
        ).should("be.visible");
        cy.get(
            '[data-test="mrbeam-ui-conversion-dialoge-header-preparing"]'
        ).should("have.text", "Preparing...");
        cy.get(".hopscotch-bubble-container").should("be.visible");
        cy.get(".hopscotch-bubble-number").should("have.text", 14);

        //TODO wait some time
        cy.get('[data-test="conversion-dialog-vector-graphics"]', {
            timeout: 10000,
        }).should("not.be.visible");

        //TODO currently skipped as we can't start a laserjob
        cy.get('[data-test="mrbeam-ui-modal-ready-to-laser"]').should(
            "be.visible"
        );
        cy.get('[data-test="mrbeam-ui-rady-to-laser-start-text"]').should(
            "be.visible"
        );
        cy.get(".hopscotch-bubble-container").should("be.visible");
        cy.get(".hopscotch-bubble-number").should("have.text", 15);
        cy.get(".hopscotch-next").click();

        //TODO currently skipped as we can't start a laserjob
        cy.get('[data-test="mrbeam-ui-modal-congratulations"]').should(
            "be.visible"
        );
        cy.get(
            '[data-test="mrbeam-ui-modal-congratulations-ok-button"]'
        ).click();
        cy.get('[data-test="mrbeam-ui-modal-congratulations"]').should(
            "not.be.visible"
        );
    });
});
