require("cypress-iframe");
require("@4tw/cypress-drag-drop");

Cypress.on("uncaught:exception", (err, runnable) => {
    // returning false here prevents Cypress from
    // failing the test
    return false;
});

Cypress.Commands.add("loginDesignStore", (email, password, code) => {
    cy.loginLaser(email, password);
    cy.laserSafety();
    cy.get('[id="burger_menu_link"]').click();
    cy.get('[id="settings_tab_btn"]').click({ force: true });
    cy.get('[id="settings_plugin_mrbeam_dev_design_store_link"]').click();
    cy.get('[id="settings-mrbeam-design-store-environment"]').select("dev");
    cy.get('[data-test="mrbeam-ui-index-design-store"]').click();
    cy.wait(10000);
    cy.loginStore(code);
});

Cypress.Commands.add("laserSafety", () => {
    cy.get("body").then(($body) => {
        if (
            $body.find('[id="lasersafety_overlay"]').filter(":visible").length
        ) {
            cy.get('[id="lasersafety_overlay"]').within(() => {
                cy.get('[type="checkbox"]').as("checkboxes");
                cy.get("@checkboxes")
                    .should("have.length", 7)
                    .each(($elem) => {
                        let item = cy.wrap($elem);
                        item.scrollIntoView();
                        item.click();
                    });
            });
            cy.get(".modal-footer")
                .filter(":visible")
                .find(".btn-danger")
                .click();
        } else {
            cy.get('[id="lasersafety_overlay"]').should("not.visible");
        }
    });
});

Cypress.Commands.add("ignoreUpdate", () => {
    cy.wait(3000);
    cy.get("body").then(($body) => {
        if (
            $body
                .find(".ui-pnotify-container")
                .filter(":visible")
                .filter(':contains("Update Available")').length
        ) {
            cy.get("button").filter(':contains("Ignore")').click();
        } else {
            cy.get(".ui-pnotify-container")
                .filter(':contains("Update Available")')
                .should("not.visible");
        }
    });
});

Cypress.Commands.add("loginStore", (code) => {
    cy.get('[id="design_store_iframe"]')
        .its("0.contentDocument.body")
        .should("not.be.empty")
        .then((body) => {
            cy.wrap(body);
            if (
                body.find('[id="registration_modal"]').filter(":visible").length
            ) {
                cy.iframe('[id="design_store_iframe"]').then(($button) => {
                    cy.get($button)
                        .contains("Enter your existing code")
                        .click();
                });
                cy.iframe('[id="design_store_iframe"]')
                    .find(
                        '[placeholder="XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"]'
                    )
                    .first()
                    .type(code);
                cy.iframe('[id="design_store_iframe"]')
                    .contains("Verify")
                    .click();
                cy.iframe('[id="design_store_iframe"]').then(($button) => {
                    cy.get($button).contains("Browse the Store").click();
                });
            } else {
                cy.get('[id="registration_modal"]').should("not.exist");
            }
        });
});

Cypress.Commands.add("loginLibrary", (email, password) => {
    cy.loginLaser(email, password);
    cy.get('[data-test="mrbeam-ui-index-design-library"]').click();
    cy.get('[id="workingarea"]').should("to.exist");
});

Cypress.Commands.add("runWelcomeWizardIfPresent", (email, password) => {
    cy.get("body").then(($body) => {
        if (
            $body.find('[data-test="first-run-wizard"]').filter(":visible")
                .length > 0
        ) {
            cy.get(".modal-footer").contains("Next").click();
            cy.wait(1000);
            cy.get('[id="wizard_plugin_corewizard_acl_input_username"]')
                .clear()
                .type(email);
            cy.get('[id="wizard_plugin_corewizard_acl_input_pw1"]')
                .clear()
                .type(password);
            cy.get('[id="wizard_plugin_corewizard_acl_input_pw2"]')
                .clear()
                .type(password);
            cy.get(".modal-footer").contains("Next").click();
            cy.wait(1000);
            cy.get('[id="wizard_plugin_corewizard_lasersafety"]').within(() => {
                cy.get('[type="checkbox"]').as("checkboxes");
                cy.get("@checkboxes")
                    .should("have.length", 7)
                    .each(($elem) => {
                        let item = cy.wrap($elem);
                        item.scrollIntoView();
                        item.click();
                    });
            });
            cy.get(".modal-footer").contains("Next").click();
            cy.get(".button-finish").click();
        } else {
            cy.get('[data-test="first-run-wizard"]').should("not.exist");
        }
    });
});

Cypress.Commands.add("runloginUserIfPresent", (email, password) => {
    cy.get("body").then(($body) => {
        if (
            $body.find('[data-test="loginscreen_dialog"]').filter(":visible")
                .length > 0
        ) {
            cy.get('[id="login_screen_email_address_in"]').clear().type(email);
            cy.get('[id="login_screen_password_in"]').clear().type(password);
            cy.get('[id="login_screen_login_btn"]').click();
        } else {
            cy.get('[data-test="loginscreen_dialog"]').should("not.visible");
            cy.reload();
            cy.get('[id="login_screen_email_address_in"]').clear().type(email);
            cy.get('[id="login_screen_password_in"]').clear().type(password);
            cy.get('[id="login_screen_login_btn"]').click();
        }
    });
});

Cypress.Commands.add("loginLaser", (email, password) => {
    cy.runWelcomeWizardIfPresent(email, password);
    cy.runloginUserIfPresent(email, password);
    cy.wait(2000);
    cy.get('[id="workingarea"]').should("to.exist");
    cy.ignoreUpdate();
});

Cypress.Commands.add("focusReminder", () => {
    cy.wait(3000);
    cy.get('.modal-dialog').then(($body) => {
        if (
            $body
                .find('[id="laserhead_focus_reminder_modal"]')
                .filter(":visible").length
        ) {
            cy.get(
                "#laserhead_focus_reminder_not_again > label > input"
            ).check();
            cy.get('[id="start_job_btn_focus_reminder"]')
                .contains("It's focused!")
                .click({ force: true });
        } else {
            cy.get('[id="laserhead_focus_reminder_modal"]')
                .filter(":visible")
                .should("not.exist");
        }
    });
    
});

Cypress.Commands.add("logout", () => {
    cy.get('[id="navbar_login"]').click();
    cy.get('[id="logout_button"]').click({ force: true });
});

import "cypress-file-upload";
