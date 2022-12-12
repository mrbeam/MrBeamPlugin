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
        cy.get(".icon-remove").click({ force: true, multiple: true });
        cy.wait(7000);
    });

    it("Switch sort", function () {
        let design1 = [];
        cy.get(".title_shortened").each((elements) => {
            design1.push(elements.text());
        });
        cy.wrap(design1).should("to.exist");
        cy.get('[data-test="tab-designlib-sort-name-radio"]').click();
        let design = [];
        cy.get(".title_shortened").each((elements) => {
            design.push(elements.text());
        });
        cy.wrap(design).should("not.equal", design1.sort());
        cy.logout();
    });

    it("Switch filter", function () {
        cy.get('[data-test="tab-designlib-filter-recent-radio"]').click();
        cy.get(".recentjob > .title")
            .if("visible")
            .contains(".mrb")
            .should("to.exist");
        cy.logout();
    });

    it("Switch filter", function () {
        cy.get('[data-test="tab-designlib-filter-gcode-radio"]').click();
        cy.get('[data-test="tab-designlib-mechinecode-file-title"]')
            .if("visible")
            .contains(".gco")
            .should("to.exist");
        cy.logout();
    });

    it("Single design in working area", function () {
        cy.get('[cy-data="tab-designlib-preview-card"]')
            .first()
            .invoke("prop", "innerText")
            .then((checkedItem) => {
                cy.get('[cy-data="tab-designlib-preview-card"]')
                    .filter(`:contains(${checkedItem})`)
                    .click();
                cy.get(".file_list_entry")
                    .filter(`:contains(${checkedItem})`)
                    .should("to.exist");
            });
    });

    it("Select/Unselect - file", function () {
        cy.get('[cy-data="tab-designlib-preview-card"]')
            .first()
            .invoke("prop", "innerText")
            .then((checkedItem) => {
                cy.get('[cy-data="tab-designlib-preview-card"]')
                    .filter(`:contains(${checkedItem})`)
                    .realHover()
                    .find('[data-test="tab-designlib-select-box"]')
                    .click({ force: true });
                cy.get('[data-test="tab-designlib-checked-file"]').should(
                    "to.visible"
                );
                cy.wait(3000);
                cy.get('[data-test="tab-designlib-unselect-all"]').click();
                cy.get('[data-test="tab-designlib-checked-file"]').should(
                    "not.visible"
                );
                cy.logout();
            });
    });

    it("Delete selection - file", function () {
        cy.get('[cy-data="tab-designlib-preview-card"]')
            .first()
            .invoke("prop", "innerText")
            .then((checkedItem) => {
                cy.get('[cy-data="tab-designlib-preview-card"]')
                    .first()
                    .contains(checkedItem)
                    .realHover()
                    .get('[data-test="tab-designlib-select-box"]')
                    .filter(":visible")
                    .click({ force: true });
                cy.get('[data-test="tab-designlib-delete-selection"]').click();
                cy.get('[cy-data="tab-designlib-preview-card"]')
                    .contains(checkedItem)
                    .should("not.exist");
            });
        cy.logout();
    });

    it("Search", function () {
        cy.get('[cy-data="tab-designlib-preview-card"]')
            .first()
            .invoke("prop", "innerText")
            .then((item) => {
                cy.get('[data-test="tab-designlib-search-input"]').clear();
                cy.get('[data-test="tab-designlib-search-input"]').type(item);
                cy.get('[cy-data="tab-designlib-preview-card"]')
                    .contains(item)
                    .should("to.exist");
            });
        cy.logout();
    });

    it("Upload designs by clicking", function () {
        const filepathSvg = "test.svg";
        cy.get('.fileinput-button input[type="file"]').attachFile(filepathSvg);
        cy.wait(5000);
        cy.get('[data-test="tab-designlib-files-svg"]')
            .first()
            .should("to.exist", filepathSvg);
        cy.logout();
    });

    it("Delete designs by burger menu", function () {
        cy.get('[cy-data="tab-designlib-preview-card"]')
            .first()
            .find('[data-test="tab-designlib-option-file"]')
            .click();
        cy.get('[data-test="tab-designlib-remove-file"]')
            .filter(":visible")
            .click();
        cy.get('[cy-data="tab-designlib-preview-card"]')
            .first()
            .should("not.exist", "test.svg");
        cy.logout();
    });
    // dynamically modal
    it("Add folder", function () {
        const time = new Date().getTime();
        const folderName = `folder ${time}`;
        cy.get('[data-test="tab-designlib-add-folder"]').click({
            force: true,
        });
        cy.get('[id="add_folder_dialog"]').within(() => {
            cy.get('.controls input[type="text"]').type(folderName);
            cy.get(".btn-primary").click();
        });
        cy.wait(7000);
        cy.get('[data-test="tab-designlib-dropdown-folder"]')
            .contains(folderName)
            .should("to.exist");
        cy.logout();
    });
    // dynamically modal
    it("Add folder - cancel button", function () {
        cy.get('[data-test="tab-designlib-add-folder"]').click({
            force: true,
        });
        cy.get('[id="add_folder_dialog"]').within(() => {
            cy.get(".btn").contains("Cancel").click();
        });
        cy.wait(7000);
        cy.get('[id="add_folder_dialog"]').should("not.visible");
        cy.logout();
    });

    it("Select/Unselect - folder", function () {
        cy.get(
            '[data-test="tab-designlib-folder-list"] > [data-test="tab-designlib-dropdown-folder"] > .title_shortened'
        )
            .eq(1)
            .invoke("prop", "innerText")
            .then((folder) => {
                cy.get('[data-test="tab-designlib-folder-list"]')
                    .filter(`:contains(${folder})`)
                    .realHover()
                    .find('[data-test="tab-designlib-folder-select-box"]')
                    .realClick({ force: true });
                cy.get('[data-test="tab-designlib-checked-folder"]').should(
                    "to.visible"
                );
                cy.wait(3000);
                cy.get('[data-test="tab-designlib-unselect-all"]').click();
                cy.get('[data-test="tab-designlib-checked-folder"]').should(
                    "not.visible"
                );
                cy.logout();
            });
    });
    // dynamically modal
    it("Delete selection - folder", function () {
        const time = new Date().getTime();
        const folderName = `folder ${time}`;
        cy.get('[data-test="tab-designlib-add-folder"]').click({
            force: true,
        });
        cy.get('[id="add_folder_dialog"]').within(() => {
            cy.get('.controls input[type="text"]').type(folderName);
            cy.get(".btn-primary").click();
        });
        cy.wait(7000);
        cy.get('[data-test="tab-designlib-dropdown-folder"]')
            .contains(folderName)
            .should("to.exist");
        cy.get(
            '[data-test="tab-designlib-folder-list"] > [data-test="tab-designlib-dropdown-folder"] > .title_shortened'
        )
            .eq(1)
            .invoke("prop", "innerText")
            .then((folder) => {
                cy.get('[data-test="tab-designlib-folder-list"]')
                    .filter(`:contains(${folder})`)
                    .realHover()
                    .find('[data-test="tab-designlib-folder-select-box"]')
                    .realClick({ force: true });
                cy.get('[data-test="tab-designlib-delete-selection"]').click();
                cy.get('[data-test="tab-designlib-folder-list"]')
                    .contains(folder)
                    .should("not.exist");
            });
        cy.logout();
    });

    it("Open folder and click back", function () {
        cy.get(
            '[data-test="tab-designlib-folder-list"] > [data-test="tab-designlib-folder-preview"]'
        )
            .eq(1)
            .filter(":visible")
            .click({ force: true });
        cy.get('[data-test="tab-designlib-back" ]').click();
        cy.get('[data-test="tab-designlib-back" ]').should("not.visible");
        cy.logout();
    });

    it("Delete folder by burger menu", function () {
        cy.get(
            '[data-test="tab-designlib-folder-list"] > [data-test="tab-designlib-dropdown-folder"]'
        )
            .eq(1)
            .invoke("prop", "innerText")
            .then((nameFolder) => {
                cy.get('[data-test="tab-designlib-dropdown-folder"]')
                    .filter(`:contains(${nameFolder})`)
                    .find('[data-test="tab-designlib-option-folder"]')
                    .click();
                cy.get('[data-test="tab-designlib-remove-folder"]')
                    .filter(":visible")
                    .realClick({ force: true });
                cy.get(
                    '[data-test="tab-designlib-folder-list"] > [data-test="tab-designlib-dropdown-folder"] > .title_shortened'
                )
                    .contains(nameFolder)
                    .should("not.exist");
            });
        cy.logout();
    });

    it("Download designs by burger menu", function () {
        cy.get('[cy-data="tab-designlib-preview-card"]')
            .first()
            .find('[data-test="tab-designlib-option-file"]')
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
                        cy.get('[cy-data="tab-designlib-preview-card"]')
                            .filter(`:contains(${downloadFile})`)
                            .find('[data-test="tab-designlib-option-file"]');
                        cy.wait(1000);
                        cy.get('[data-test="tab-designlib-download-file"]')
                            .filter(":visible")
                            .click();
                        cy.verifyDownload(downloadFile);
                    });
            });
    });
});
