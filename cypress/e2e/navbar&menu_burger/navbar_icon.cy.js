describe("Navbar icons", function () {
    beforeEach(function () {
        cy.fixture("test-data").then(function (testData) {
            this.testData = testData;
        });
    });
    beforeEach(function () {
        cy.visit(this.testData.url_laser);
        cy.wait(20000);
        cy.loginLaser(this.testData.email, this.testData.password);
    });
    it("Message", function () {
        cy.get('[data-test="mrbeam-ui-index-tab-message"]').click();
        cy.get('[data-test="tab-message-list-message"]').click();
        cy.get('[data-test="tab-message-message-content-no-img"]').should(
            "to.visible"
        );
        cy.logout();
    });
    it("Restart - success", function () {
        cy.get("#navbar_systemmenu > .dropdown-toggle").click();
        cy.get(
            "#navbar_systemmenu > .dropdown-menu > :nth-child(3) > a"
        ).click();
        cy.get(".modal-scrollable > .modal > .modal-header")
            .contains("Are you sure?")
            .should("to.visible");
        cy.get(
            ".modal-scrollable > .modal > .modal-footer > .btn-danger"
        ).click();
        cy.contains(
            'The command "Restart OctoPrint" executed successfully'
        ).should("to.exist");
        cy.logout();
    });
    it("Restart - abort", function () {
        cy.get("#navbar_systemmenu > .dropdown-toggle").click();
        cy.get(
            "#navbar_systemmenu > .dropdown-menu > :nth-child(3) > a"
        ).click();
        cy.get(".modal-scrollable > .modal > .modal-header")
            .contains("Are you sure?")
            .should("to.visible");
        cy.get(
            '.modal-scrollable > .modal > .modal-footer > [data-dismiss="modal"]'
        ).click();
        cy.get(".modal-scrollable > .modal > .modal-header")
            .contains("Are you sure?")
            .should("not.visible");
        cy.contains(
            'The command "Restart OctoPrint" executed successfully'
        ).should("not.exist");
        cy.logout();
    });
    // This test is failing on GitHub actions
    it.skip("Language - de", function () {
        cy.intercept("GET", "http://localhost:5002/api/users/dev@mr-beam.org", {
            statusCode: 200,
            settings: { language: "de" },
        }).as("changeLang");
        cy.get("#navbar_login > .dropdown-toggle").click();
        cy.get("#usersettings_button").click();
        cy.get("#usersettings_interface_link > a").click();
        cy.get("fieldset > .control-group > .controls > select").select("de");
        cy.get("#usersettings_dialog > .modal-footer > .btn-primary").click();
        cy.wait("@changeLang").should("to.exist");
        cy.logout();
    });
    // This test is failing on GitHub actions
    it.skip("Language - en", function () {
        cy.intercept("GET", "http://localhost:5002/api/users/dev@mr-beam.org", {
            statusCode: 200,
            settings: { language: "en" },
        }).as("changeLang");
        cy.get("#navbar_login > .dropdown-toggle").click();
        cy.get("#usersettings_button").click();
        cy.get("#usersettings_interface_link > a").click();
        cy.get("fieldset > .control-group > .controls > select").select("en");
        cy.get("#usersettings_dialog > .modal-footer > .btn-primary").click();
        cy.wait("@changeLang").should("to.exist");
        cy.logout();
    });
    // This test is failing on GitHub actions
    it.skip("Language - es", function () {
        cy.intercept("GET", "http://localhost:5002/api/users/dev@mr-beam.org", {
            statusCode: 200,
            settings: { language: "es" },
        }).as("changeLang");
        cy.get("#navbar_login > .dropdown-toggle").click();
        cy.get("#usersettings_button").click();
        cy.get("#usersettings_interface_link > a").click();
        cy.get("fieldset > .control-group > .controls > select").select("es");
        cy.get("#usersettings_dialog > .modal-footer > .btn-primary").click();
        cy.wait("@changeLang").should("to.exist");
        cy.logout();
    });
    // This test is failing on GitHub actions
    it.skip("Language - it", function () {
        cy.intercept("GET", "http://localhost:5002/api/users/dev@mr-beam.org", {
            statusCode: 200,
            settings: { language: "it" },
        }).as("changeLang");
        cy.get("#navbar_login > .dropdown-toggle").click();
        cy.get("#usersettings_button").click();
        cy.get("#usersettings_interface_link > a").click();
        cy.get("fieldset > .control-group > .controls > select").select("it");
        cy.get("#usersettings_dialog > .modal-footer > .btn-primary").click();
        cy.wait("@changeLang").should("to.exist");
        cy.logout();
    });
    // This test is failing on GitHub actions
    it.skip("Language - fr", function () {
        cy.intercept("GET", "http://localhost:5002/api/users/dev@mr-beam.org", {
            statusCode: 200,
            settings: { language: "fr" },
        }).as("changeLang");
        cy.get("#navbar_login > .dropdown-toggle").click();
        cy.get("#usersettings_button").click();
        cy.get("#usersettings_interface_link > a").click();
        cy.get("fieldset > .control-group > .controls > select").select("fr");
        cy.get("#usersettings_dialog > .modal-footer > .btn-primary").click();
        cy.wait("@changeLang").should("to.exist");
        cy.logout();
    });
    // This test is failing on GitHub actions
    it.skip("Language - default", function () {
        cy.intercept("GET", "http://localhost:5002/api/users/dev@mr-beam.org", {
            statusCode: 200,
            settings: { language: "_default" },
        }).as("changeLang");
        cy.get("#navbar_login > .dropdown-toggle").click();
        cy.get("#usersettings_button").click();
        cy.get("#usersettings_interface_link > a").click();
        cy.get("fieldset > .control-group > .controls > select").select(
            "_default"
        );
        cy.get("#usersettings_dialog > .modal-footer > .btn-primary").click();
        cy.wait("@changeLang").should("to.exist");
        cy.logout();
    });
    it("Language - abort", function () {
        cy.get("#navbar_login > .dropdown-toggle").click();
        cy.get("#usersettings_button").click();
        cy.get(
            '#usersettings_dialog > .modal-footer > [data-dismiss="modal"]'
        ).click();
        cy.logout();
    });
});
