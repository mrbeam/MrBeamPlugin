describe('Password', () => {
  beforeEach(function () {
        cy.fixture("test-data").then(function (testData) {
            this.testData = testData;
        });
    });

    beforeEach(function () {
        cy.visit(this.testData.url_laser);
        cy.wait(10000);
        cy.loginLaser(this.testData.email, this.testData.password);
    });

    it("Enter new password -- success", function () {
        //check existence of the User Settings under profile icon
        cy.get('[id="navbar_login"]').click();
        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .should("to.exist");

        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .click({force: true});

        //check existence of the password input field
        cy.get('[id="usersettings_dialog"]')
        .should("to.exist");

        //check typing new password and repeating it
        cy.get('[id="userSettings-access_password"]')
        .type("MrBeamHotSecretPassword");

        cy.get('[id="userSettings-access_repeatedPassword"]')
        .type("MrBeamHotSecretPassword");

        //error message does not show when matching passwords
        cy.get('[id="usersettings_access"]')
        .get('.form-horizontal')
        .get('.help-inline').should('be.not.visible');

        //confirm button is not disabled when matching passwords
        cy.get(
            '[id="usersettings_dialog"] > .modal-footer > .btn-primary'
        ).should('not.be.disabled');

        cy.get(
            '[id="usersettings_dialog"] > .modal-footer > .btn-primary'
        ).click({force: true});

        //check the new password after the re-login
        cy.logout();
        cy.get('[id="login_screen_password_in"]').clear().type("MrBeamHotSecretPassword");
        cy.get('[id="login_screen_login_btn"]').click();

        //check if login with new password is successful
        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .should("be.not.visible");

        cy.logout();
        cy.get('[id="login_screen_password_in"]').clear().type("MrBeamHotSecretPassword");
        cy.get('[id="login_screen_login_btn"]').click();
        cy.wait(10000);

        // reset password of dev account to "a"
        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .click({force: true});

        cy.get('[id="userSettings-access_password"]')
        .type("a");

        cy.get('[id="userSettings-access_repeatedPassword"]')
        .type("a");

        cy.get(
            '[id="usersettings_dialog"] > .modal-footer > .btn-primary'
        ).click({force: true});

        cy.wait(10000);

        cy.logout();
        cy.get('[id="login_screen_password_in"]').clear().type("a");
        cy.get('[id="login_screen_login_btn"]').click();

    });

    it("Enter new password -- failure", function () {
        //check existence of the User Settings under profile icon
        cy.get('[id="navbar_login"]').click();
        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .should("to.exist");

        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .click({force: true});

        //check existence of the password input field
        cy.get('[id="usersettings_dialog"]')
        .should("to.exist");

        //check typing new password and repeating it
        cy.get('[id="userSettings-access_password"]')
        .type("MrBeamHotSecretPassword");

        cy.get('[id="userSettings-access_repeatedPassword"]')
        .type("MrBeamSuperHotSecretPassword");

        //error message shows when mismatching passwords
        cy.get('[id="usersettings_access"]')
        .get('.form-horizontal')
        .get('.help-inline').should('be.visible');

        //confirm button is disabled when mismatching passwords
        cy.get(
            '[id="usersettings_dialog"] > .modal-footer > .btn-primary'
        ).should('be.disabled');

        cy.get('[id="userSettings-access_repeatedPassword"]').clear().type("MrBeamHotSecretPassword");

        cy.get(
            '[id="usersettings_dialog"] > .modal-footer > .btn-primary'
        ).click({force: true});

        //check a wrong password after the re-login
        cy.logout();
        cy.get('[id="login_screen_password_in"]').clear().type("a");
        cy.get('[id="login_screen_login_btn"]').click();

        //check if login with wrong password does not work
        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .should("be.not.visible");

        cy.get('[id="login_screen_password_in"]').clear().type("MrBeamHotSecretPassword");
        cy.get('[id="login_screen_login_btn"]').click();
        cy.wait(10000);

        // reset password of dev account to "a"
        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .click({force: true});

        cy.get('[id="userSettings-access_password"]')
        .type("a");

        cy.get('[id="userSettings-access_repeatedPassword"]')
        .type("a");

        cy.get(
            '[id="usersettings_dialog"] > .modal-footer > .btn-primary'
        ).click({force: true});
    });
});
