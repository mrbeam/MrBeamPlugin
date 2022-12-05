describe("Access control", function () {
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

    it("Access control", function () {
        cy.get('[id="settings_users_link"]').click();
        cy.get('[title="Add user"]').click();
        cy.get("#settings-usersDialogAddUserName").clear("de");
        cy.get("#settings-usersDialogAddUserName").type("dev+1@mr-beam.org");
        cy.get("#settings-usersDialogAddUserPassword1").clear("a");
        cy.get("#settings-usersDialogAddUserPassword1").type("a");
        cy.get("#settings-usersDialogAddUserPassword2").clear("a");
        cy.get("#settings-usersDialogAddUserPassword2").type("a");
        cy.get("#settings-usersDialogAddUserActive").uncheck();
        cy.get("#settings-usersDialogAddUserAdmin").uncheck();
        cy.get(
            "#settings-usersDialogAddUser > .modal-footer > .btn-primary"
        ).click();
        cy.get(":nth-child(1) > .settings_users_active > .fa").click();
        cy.get(":nth-child(1) > .settings_users_active > .fa").click();
        cy.get(":nth-child(1) > .settings_users_admin > .fa").click();
        cy.get("#settings_users").click();
        cy.get(":nth-child(1) > .settings_users_actions > .fa-pencil").click();
        cy.get("#settings-usersDialogEditUserActive").check();
        cy.get("#settings-usersDialogEditUserAdmin").check();
        cy.get(
            "#settings-usersDialogEditUser > .modal-footer > .btn-primary"
        ).click();
    });

    it("Access control", function () {
        cy.get('[id="settings_users_link"]').click();
        cy.logout();
        cy.get('[id="login_screen_email_address_in"]')
            .clear()
            .type("dev+1@mr-beam.org");
        cy.get('[id="login_screen_password_in"]').clear().type("a");
        cy.get('[id="login_screen_login_btn"]').click();
    });

    it("Access control", function () {
        cy.get('[id="settings_users_link"]').click();
        cy.get(":nth-child(1) > .settings_users_actions > .fa-key").click();
        cy.get("#settings-usersDialogChangePasswordPassword1").clear("a");
        cy.get("#settings-usersDialogChangePasswordPassword1").type("aa");
        cy.get("#settings-usersDialogChangePasswordPassword2").clear("a");
        cy.get("#settings-usersDialogChangePasswordPassword2").type("aa");
        cy.get(
            "#settings-usersDialogChangePassword > .modal-footer > .btn-primary"
        ).click();
    });
    it("Access control", function () {
        cy.get('[id="settings_users_link"]').click();
        cy.get('[id="settings_users_link"]').click();
        cy.logout();
        cy.get('[id="login_screen_email_address_in"]')
            .clear()
            .type("dev+1@mr-beam.org");
        cy.get('[id="login_screen_password_in"]').clear().type("aa");
        cy.get('[id="login_screen_login_btn"]').click();
    });
    it("Access control", function () {
        cy.get('[id="settings_users_link"]').click();
    });
    it("Access control", function () {
        cy.get('[id="settings_users_link"]').click();
        cy.get(":nth-child(1) > .settings_users_actions > .fa-trash-o").click();
    });

    it("Access control", function () {
        cy.get('[id="settings_users_link"]').click();
        cy.get(".settings_users_actions > .fa-pencil").click();
        cy.get(
            '#settings-usersDialogEditUser > .modal-footer > [data-dismiss="modal"]'
        ).click();
        cy.get(".fa-key").click();
        cy.get(
            '#settings-usersDialogChangePassword > .modal-footer > [data-dismiss="modal"]'
        ).click();
    });
    it("Access control", function () {
        cy.get('[id="settings_users_link"]').click();
        cy.get("#mrb_settings_users_header > .show_only_online > a")
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
    });
});
