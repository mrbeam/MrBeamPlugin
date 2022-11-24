describe("Library design", function () {
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
        cy.get('[data-test="tab-designbib-sort-name-radio"]').click();
        cy.get('[data-bind="foreach: foldersOnlyABCList()"]').should(
            "to.exist"
        );
        cy.logout();
    });

    it("Switch filter", function () {
        cy.get('[data-test="tab-designbib-filter-gcode-radio"]').click();
        cy.get('[data-bind="foreach: foldersOnlyABCList()"]').should(
            "to.exist"
        );
        cy.logout();
    });

    it("Select/Unselect - file", function () {
        cy.get('[data-test="library-design-files-svg"]')
            .first()
            .invoke('prop', 'innerText').then(checkedItem => {
            cy.get('[data-test="library-design-files-svg"]').filter(`:contains(${checkedItem})`).realHover()
              .find('[data-test="tab-design-library-svg-select-box"]').click({ force: true })
            cy.get('[data-test="tab-design-library-checked-file"]').should('to.visible')  
            cy.wait(3000);
            cy.get('[data-test="library-design-unselect-all"]').click();
            cy.get('[data-test="tab-design-library-checked-file"]').should('not.visible')  
            cy.logout();
        });
    });

    it("Delete selection - file", function () {
        cy.get('[data-test="library-design-files-svg"]')
            .first()
            .invoke('prop', 'innerText').then(checkedItem => {
                cy.get('[data-test="library-design-files-svg"]').first().contains(checkedItem).realHover()
                  .get('[data-test="tab-design-library-svg-select-box"]').filter(':visible').click({ force: true })
                cy.get('[data-test="library-design-delete-selection"]').click();
                cy.get('[data-test="library-design-files-svg"]').contains(checkedItem).should('not.exist')
            })
        cy.logout();
    });

    it("Search", function () {
        cy.get('[data-test="tab-design-library-svg-preview-card"]')
            .eq(1)
            .invoke('prop', 'innerText').then(item => {
                cy.get('[data-test="tab-design-library-search-input"]').clear();
                cy.get('[data-test="tab-design-library-search-input"]').type(item);
                cy.get('[data-test="tab-design-library-svg-preview-card"]').contains(item).should('to.exist')
            })
        cy.logout();
    });

    it("Upload designs by clicking", function () {
        const filepathSvg = "test.svg";
        cy.get('[data-test="tab-design-library-upload-file"] input[type="file"]').attachFile(filepathSvg);
        cy.wait(5000);
        cy.get('[data-test="library-design-files-svg"]')
            .first()
            .should("to.exist", "test.svg");
        cy.logout();
    });

    it("Delete designs by burger menu", function () {
        cy.get('[data-test="library-design-files-svg"]')
            .first()
            .find('[data-test="tab-design-library-option-file"]')
            .click();
        cy.get('[data-test="tab-design-library-remove-file"]').click();
        cy.get('[data-test="library-design-files-svg"]')
            .first()
            .should("not.exist", "test.svg");
        cy.logout();
    });
    // dynamically modal
    it("Add folder", function () {
        const time = new Date().getTime();
        const folderName = `folder ${time}`
        cy.get('[data-test="library-design-add-folder"]').click({ force: true });
        cy.get('[id="add_folder_dialog"]').within(() => {
            cy.get('.controls input[type="text"]').type(folderName);
            cy.get(".btn-primary").click();
        });
        cy.wait(7000);
        cy.get('[data-test="tab-design-library-folder-list"]')
            .contains(folderName)
            .should("to.exist");
        cy.logout();
    });
    // dynamically modal
    it("Add folder - cancel button", function () {
        cy.get('[data-test="library-design-add-folder"]').click({ force: true });
        cy.get('[id="add_folder_dialog"]').within(() => {
            cy.get(".btn").contains("Cancel").click();
        });
        cy.wait(7000);
        cy.get('[id="add_folder_dialog"]')
            .should("not.visible");
        cy.logout();
    });

    it("Select/Unselect - folder", function () {
        cy.get('[data-test="tab-design-library-folder-list"]').last().invoke('prop','innerText').then((folder) => {
            cy.get('[data-test="tab-design-library-folder-list"]').filter(`:contains(${folder})`).realHover()
              .find('[data-test="tab-design-library-folder-select-box"]').click({ force: true })
            cy.get('[data-test="tab-design-library-checked-folder"]').should('to.visible')  
            cy.wait(3000);
            cy.get('[data-test="library-design-unselect-all"]').click();
            cy.get('[data-test="tab-design-library-checked-folder"]').should('not.visible')  
            cy.logout();
        });
    });
    // dynamically modal
    it("Delete selection - folder", function () {
        const time = new Date().getTime();
        const folderName = `folder ${time}`
        cy.get('[data-test="library-design-add-folder"]').click({ force: true });
        cy.get('[id="add_folder_dialog"]').within(() => {
            cy.get('.controls input[type="text"]').type(folderName);
            cy.get(".btn-primary").click();
        });
        cy.wait(7000);
        cy.get('[data-test="tab-design-library-folder-list"]')
            .contains(folderName)
            .should("to.exist");
        cy.get('[data-test="tab-design-library-folder-list"]').last().invoke('prop','innerText').then((folder) => {
            cy.get('[data-test="tab-design-library-folder-list"]').filter(`:contains(${folder})`).realHover()
              .find('[data-test="tab-design-library-folder-select-box"]').click({ force: true })
              cy.get('[data-test="library-design-delete-selection"]').click();
              cy.get('[data-test="tab-design-library-folder-list"]').contains(folder).should('not.exist')
            });
        cy.logout();
    });   

    it("Open folder and click back", function () {
        cy.get('[data-test="tab-design-library-folder-preview"]').eq(0).click({ force: true });
        cy.get('[data-test="library-design-back" ]').click();
        cy.logout();
    });

    it("Delete folder by burger menu", function () {
        cy.get('[data-test="tab-design-library-folder-list"]').first().invoke('prop', 'innerText').then(nameFolder => {
            cy.get('[data-test="tab-design-library-dropdown-folder"]')
              .filter(`:contains(${nameFolder})`).find('[data-test="tab-design-library-option-folder"]')
              .click();
            cy.get('[data-test="tab-design-library-remove-folder"]').first().click();
            cy.get('[data-test="tab-design-library-folder-list"]')
              .should("not.exist", nameFolder);
        })
        cy.logout();
    });

    it("Download designs by burger menu", function () {
        cy.intercept(
            "GET",
            "http://localhost:5002/downloads/files/local/Test_plan_1.svg"
        ).as("downloadFile");
        cy.get('[data-test="library-design-files-svg"]')
            .first()
            .find('[data-test="tab-design-library-option-file"]')
            .click();
        cy.wait(1000);
        cy.get('[data-test="tab-design-library-download-file"]').click();
        cy.wait("@downloadFile");
    });
});
