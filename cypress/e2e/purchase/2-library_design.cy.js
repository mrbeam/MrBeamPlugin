describe("Login", function () {
    beforeEach(function () {
        cy.fixture("test-data").then(function (testData) {
            this.testData = testData;
        });
    });

    beforeEach(function () {
        cy.visit(this.testData.url);
        cy.wait(15000);
        cy.loginLibrary(this.testData.email, this.testData.password);
        cy.wait(7000);
    });

    it("Switch sort", function () {
        cy.get('[id="design_lib_sort_name_radio"]').click();
        cy.get('[data-bind="foreach: foldersOnlyABCList()"]').should(
            "to.exist"
        );
        cy.logout();
    });

    it("Switch filter", function () {
        cy.get('[id="design_lib_filter_gcode_radio"]').click();
        cy.get('[data-bind="foreach: foldersOnlyABCList()"]').should(
            "to.exist"
        );
        cy.logout();
    });

    it("Select/Unselect", function () {
        cy.get(".files_template_model_svg")
            .first()
            .realHover()
            .find(".selection_box")
            .first()
            .click({ force: true });
        cy.wait(3000);
        cy.get(".btn-link").find(".icon-remove").click();
        cy.logout();
    });

    it("Delete selection", function () {
        cy.get(".files_template_model_svg")
            .first()
            .realHover()
            .find(".selection_box")
            .click({ force: true });
        cy.get(".btn-danger").find(".icon-trash").click();
        cy.logout();
    });

    it("Upload designs by clicking", function () {
        const filepathSvg = "test.svg";
        cy.get('.fileinput-button input[type="file"]').attachFile(filepathSvg);
        cy.wait(5000);
        cy.get(".files_template_model_svg")
            .first()
            .should("to.exist", "test.svg");
        cy.logout();
    });

    it("Delete designs by burger menu", function () {
        cy.get(".files_template_model_svg")
            .first()
            .should("contain", "test.svg")
            .find(".icon-reorder")
            .click();
        cy.get(".icon-trash:visible").click();
        cy.get(".files_template_model_svg")
            .first()
            .should("not.exist", "test.svg");
        cy.logout();
    });

    it("Add folder", function () {
        cy.get(".addfolder-button").click({ force: true });
        cy.get('[id="add_folder_dialog"]').within(() => {
            cy.get('.controls input[type="text"]').type("test folder");
            cy.get(".btn-primary").click();
        });
        cy.wait(7000);
        cy.get(".file_list_entry > .title")
            .contains("test folder")
            .should("to.exist");
        cy.logout();
    });

    it("Open folder and click back", function () {
        cy.get(".preview").eq(0).click({ force: true });
        cy.get(".back-arrow").click();
        cy.logout();
    });

    it("Delete folder by burger menu", function () {
        cy.get(
            "#gcode_file_23e36bc802346e6e128d3370e49fc959 > .file_list_entry > .title > .dropdown-toggle > .icon-reorder"
        )
            .first()
            .click();
        cy.get(".dropdown-menu").get(".icon-trash:visible").first().click();
        cy.get(".file_list_entry > .title")
            .first()
            .should("not.exist", "test folder");
        cy.logout();
    });

    it("Download designs by burger menu", function () {
        cy.intercept(
            "GET",
            Cypress.config().baseUrl + "/downloads/files/local/Test_plan_1.svg"
        ).as("downloadFile");
        cy.get(".files_template_model_svg")
            .first()
            .find(".icon-reorder")
            .click();
        cy.wait(1000);
        cy.get(".icon-download-alt:visible").click();
        cy.wait("@downloadFile");
    });
});
