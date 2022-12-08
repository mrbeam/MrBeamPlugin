describe('language', () => {
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

    it("Set language -- De", function () {
        //check existence of the User Settings under profile icon
        cy.get('[id="navbar_login"]').click();
        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .should("to.exist");

        // test abort button in language settings
        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .click({force: true});

        cy.get('[id="usersettings_dialog"]')
        .get('.modal-body')
        .children()
        .find('[id=usersettings_interface_link]')
        .click()
        cy.get(
            '[id="usersettings_dialog"] > .modal-footer > .btn'
        ).eq(0).click({force: true});
        cy.get('[id=usersettings_interface_link]').should("not.be.visible");

        // set language to German and test the name of the working area after the reload
        cy.get('[id="navbar_login"]').click();
        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .click({force: true});

        cy.get('[id="usersettings_dialog"]')
        .get('.modal-body')
        .children()
        .find('[id=usersettings_interface_link]')
        .click()

        cy.get('[id=usersettings_interface]')
        .get('.control-group')
        .get('.controls')
        .get('select').eq(13).select('de', { force: true });
        cy.wait(5000);

        // test confirm button in language settings
        cy.get(
            '[id="usersettings_dialog"] > .modal-footer > .btn-primary'
        ).click({force: true});

        cy.reload();
        cy.get('[id=mrbeam-main-tabs]').contains("arbeitsbereich").should("to.exist");
    });

    it("Set language -- En", function () {
        //check existence of the User Settings under profile icon
        cy.get('[id="navbar_login"]').click();
        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .should("to.exist");

        // test abort button in language settings
        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .click({force: true});

        cy.get('[id="usersettings_dialog"]')
        .get('.modal-body')
        .children()
        .find('[id=usersettings_interface_link]')
        .click()
        cy.get(
            '[id="usersettings_dialog"] > .modal-footer > .btn'
        ).eq(0).click({force: true});
        cy.get('[id=usersettings_interface_link]').should("not.be.visible");

        // set language to German and test the name of the working area after the reload
        cy.get('[id="navbar_login"]').click();
        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .click({force: true});

        cy.get('[id="usersettings_dialog"]')
        .get('.modal-body')
        .children()
        .find('[id=usersettings_interface_link]')
        .click()

        cy.get('[id=usersettings_interface]')
        .get('.control-group')
        .get('.controls')
        .get('select').eq(13).select('en', { force: true });
        cy.wait(5000);

        // test confirm button in language settings
        cy.get(
            '[id="usersettings_dialog"] > .modal-footer > .btn-primary'
        ).click({force: true});

        cy.reload();
        cy.get('[id=mrbeam-main-tabs]').contains("working area").should("to.exist");
    });

    it("Set language -- Es", function () {
        //check existence of the User Settings under profile icon
        cy.get('[id="navbar_login"]').click();
        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .should("to.exist");

        // test abort button in language settings
        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .click({force: true});

        cy.get('[id="usersettings_dialog"]')
        .get('.modal-body')
        .children()
        .find('[id=usersettings_interface_link]')
        .click()
        cy.get(
            '[id="usersettings_dialog"] > .modal-footer > .btn'
        ).eq(0).click({force: true});
        cy.get('[id=usersettings_interface_link]').should("not.be.visible");

        // set language to German and test the name of the working area after the reload
        cy.get('[id="navbar_login"]').click();
        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .click({force: true});

        cy.get('[id="usersettings_dialog"]')
        .get('.modal-body')
        .children()
        .find('[id=usersettings_interface_link]')
        .click()

        cy.get('[id=usersettings_interface]')
        .get('.control-group')
        .get('.controls')
        .get('select').eq(13).select('es', { force: true });
        cy.wait(5000);

        // test confirm button in language settings
        cy.get(
            '[id="usersettings_dialog"] > .modal-footer > .btn-primary'
        ).click({force: true});

        cy.reload();
        cy.get('[id=mrbeam-main-tabs]').contains("área de trabajo").should("to.exist");
    });

    it("Set language -- Fr", function () {
        //check existence of the User Settings under profile icon
        cy.get('[id="navbar_login"]').click();
        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .should("to.exist");

        // test abort button in language settings
        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .click({force: true});

        cy.get('[id="usersettings_dialog"]')
        .get('.modal-body')
        .children()
        .find('[id=usersettings_interface_link]')
        .click()
        cy.get(
            '[id="usersettings_dialog"] > .modal-footer > .btn'
        ).eq(0).click({force: true});
        cy.get('[id=usersettings_interface_link]').should("not.be.visible");

        // set language to German and test the name of the working area after the reload
        cy.get('[id="navbar_login"]').click();
        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .click({force: true});

        cy.get('[id="usersettings_dialog"]')
        .get('.modal-body')
        .children()
        .find('[id=usersettings_interface_link]')
        .click()

        cy.get('[id=usersettings_interface]')
        .get('.control-group')
        .get('.controls')
        .get('select').eq(13).select('fr', { force: true });
        cy.wait(5000);

        // test confirm button in language settings
        cy.get(
            '[id="usersettings_dialog"] > .modal-footer > .btn-primary'
        ).click({force: true});

        cy.reload();
        cy.get('[id=mrbeam-main-tabs]').contains("espace de travail").should("to.exist");
    });
    it("Set language -- It", function () {
        //check existence of the User Settings under profile icon
        cy.get('[id="navbar_login"]').click();
        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .should("to.exist");

        // test abort button in language settings
        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .click({force: true});

        cy.get('[id="usersettings_dialog"]')
        .get('.modal-body')
        .children()
        .find('[id=usersettings_interface_link]')
        .click()
        cy.get(
            '[id="usersettings_dialog"] > .modal-footer > .btn'
        ).eq(0).click({force: true});
        cy.get('[id=usersettings_interface_link]').should("not.be.visible");

        // set language to German and test the name of the working area after the reload
        cy.get('[id="navbar_login"]').click();
        cy.get('[id="login_dropdown_loggedin"]')
        .children()
        .find('[id="usersettings_button"]')
        .click({force: true});

        cy.get('[id="usersettings_dialog"]')
        .get('.modal-body')
        .children()
        .find('[id=usersettings_interface_link]')
        .click()

        cy.get('[id=usersettings_interface]')
        .get('.control-group')
        .get('.controls')
        .get('select').eq(13).select('it', { force: true });
        cy.wait(5000);

        // test confirm button in language settings
        cy.get(
            '[id="usersettings_dialog"] > .modal-footer > .btn-primary'
        ).click({force: true});

        cy.reload();
        cy.get('[id=mrbeam-main-tabs]').contains("area di lavoro").should("to.exist");
    });
});
