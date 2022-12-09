describe('Quickstart Guide', () => {
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

    it("Quickstart Guide -- De", function () {
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

        // click on quickstart guide under burger menu icon
        cy.get('[id="burger_menu_link"]')
        .click({force: true});
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Quickstart Guide").should("to.exist");

        // test find.mr.beam website url & title
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Quickstart Guide").invoke('removeAttr', 'target').click({force: true});
        cy.url().should('eq', 'http://localhost:5002/plugin/mrbeam/docs/dreamcut/de/QuickstartGuide.pdf');
    });

    it("Quickstart Guide -- En", function () {
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

        // click on quickstart guide under burger menu icon
        cy.get('[id="burger_menu_link"]')
        .click({force: true});
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Quickstart Guide").should("to.exist");

        // test find.mr.beam website url & title
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Quickstart Guide").invoke('removeAttr', 'target').click({force: true});
        cy.url().should('eq', 'http://localhost:5002/plugin/mrbeam/docs/dreamcut/en/QuickstartGuide.pdf');
    });

    it("Quickstart Guide -- Es", function () {
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

        // click on quickstart guide under burger menu icon
        cy.get('[id="burger_menu_link"]')
        .click({force: true});
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Guía de inicio rápido").should("to.exist");

        // test find.mr.beam website url & title
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Guía de inicio rápido").invoke('removeAttr', 'target').click({force: true});
        cy.url().should('eq', 'http://localhost:5002/plugin/mrbeam/docs/dreamcut/en/QuickstartGuide.pdf');
    });

    it("Quickstart Guide-- Fr", function () {
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

        // click on quickstart guide under burger menu icon
        cy.get('[id="burger_menu_link"]')
        .click({force: true});
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Guide de démarrage rapide").should("to.exist");

        // test find.mr.beam website url & title
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Guide de démarrage rapide").invoke('removeAttr', 'target').click({force: true});
        cy.url().should('eq', 'http://localhost:5002/plugin/mrbeam/docs/dreamcut/en/QuickstartGuide.pdf');
    });

    it("Quickstart Guide -- It", function () {
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

        // click on quickstart guide under burger menu icon
        cy.get('[id="burger_menu_link"]')
        .click({force: true});
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Guida Rapida").should("to.exist");

        // test find.mr.beam website url & title
        cy.get('[id="burger_menu"] > .dropdown-menu').contains("Guida Rapida").invoke('removeAttr', 'target').click({force: true});
        cy.url().should('eq', 'http://localhost:5002/plugin/mrbeam/docs/dreamcut/en/QuickstartGuide.pdf');
    });
});
