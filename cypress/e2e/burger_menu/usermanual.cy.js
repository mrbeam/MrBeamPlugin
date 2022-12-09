describe('User manual', () => {
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

    it("User manual -- De", function () {
        // set language to German
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
        // check language is german
        cy.get('[id=mrbeam-main-tabs]').contains("arbeitsbereich").should("to.exist");

        // check existence of burger menu icon
        cy.get('[id="burger_menu_link"]')
        .should("to.exist");

        // click on user manual under burger menu icon
        cy.get('[id="burger_menu_link"]')
        .click({force: true});
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Betriebsanleitung").should("to.exist");

        // test user manual website url & title
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Betriebsanleitung").invoke('removeAttr', 'target').click({force: true});
        cy.url().should('eq', 'http://localhost:5002/plugin/mrbeam/docs/dreamcut/de/UserManual.pdf');
    });

    it("User manual -- En", function () {
        // set language to English
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
        // check language is english
        cy.get('[id=mrbeam-main-tabs]').contains("working area").should("to.exist");

        // check existence of burger menu icon
        cy.get('[id="burger_menu_link"]')
        .should("to.exist");

        // click on user manual under burger menu icon
        cy.get('[id="burger_menu_link"]')
        .click({force: true});
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("User Manual").should("to.exist");

        // test user manual website url & title
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("User Manual").invoke('removeAttr', 'target').click({force: true});
        cy.url().should('eq', 'http://localhost:5002/plugin/mrbeam/docs/dreamcut/en/UserManual.pdf');
    });

    it("User manual -- Es", function () {
        // set language to Spanish
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
        // check language is german
        cy.get('[id=mrbeam-main-tabs]').contains("área de trabajo").should("to.exist");

        // check existence of burger menu icon
        cy.get('[id="burger_menu_link"]')
        .should("to.exist");

        // click on user manual under burger menu icon
        cy.get('[id="burger_menu_link"]')
        .click({force: true});
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Manual del usuario").should("to.exist");

        // test user manual website url & title
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Manual del usuario").invoke('removeAttr', 'target').click({force: true});
        cy.url().should('eq', 'http://localhost:5002/plugin/mrbeam/docs/dreamcut/es/UserManual.pdf');
    });

    it("User manual -- Fr", function () {
        // set language to French
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
        // check language is german
        cy.get('[id=mrbeam-main-tabs]').contains("espace de travail").should("to.exist");

        // check existence of burger menu icon
        cy.get('[id="burger_menu_link"]')
        .should("to.exist");

        // click on user manual under burger menu icon
        cy.get('[id="burger_menu_link"]')
        .click({force: true});
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Manuel d’Instructions").should("to.exist");

        // test user manual website url & title
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Manuel d’Instructions").invoke('removeAttr', 'target').click({force: true});
        cy.url().should('eq', 'http://localhost:5002/plugin/mrbeam/docs/dreamcut/fr/UserManual.pdf');
    });

    it("User manual -- It", function () {
        // set language to Italian
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
        // check language is german
        cy.get('[id=mrbeam-main-tabs]').contains("area di lavoro").should("to.exist");

        // check existence of burger menu icon
        cy.get('[id="burger_menu_link"]')
        .should("to.exist");

        // click on user manual under burger menu icon
        cy.get('[id="burger_menu_link"]')
        .click({force: true});
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Manuale Utente").should("to.exist");

        // test user manual website url & title
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Manuale Utente").invoke('removeAttr', 'target').click({force: true});
        cy.url().should('eq', 'http://localhost:5002/plugin/mrbeam/docs/dreamcut/it/UserManual.pdf');
    });
});
