require("cypress-iframe");
require("@4tw/cypress-drag-drop");
require("cy-verify-downloads").addCustomCommand();
require("cypress-delete-downloads-folder").addCustomCommand();

Cypress.on("uncaught:exception", (err, runnable) => {
    // returning false here prevents Cypress from
    // failing the test
    return false;
});

Cypress.Commands.add("loginDesignStore", (email, password, code) => {
    cy.loginLaser(email, password);
    cy.laserSafety();
    cy.get('[data-test="mrbeam-ui-index-menu-burger"]').click();
    cy.get('[data-test="mrbeam-ui-index-tab-settings"]').click({ force: true });
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
                .should("not.exist");
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
    cy.hardResetModal();
    cy.get(".icon-remove").click({ force: true, multiple: true });
});

Cypress.Commands.add("focusReminder", () => {
    cy.wait(3000);

    cy.get("body").then(($body) => {
        let reminderLaser = $body.find('[id="laserhead_focus_reminder_modal"]');
        if (reminderLaser.is(":visible")) {
            cy.get(
                "#laserhead_focus_reminder_not_again > label > input"
            ).click();
            cy.get('[id="start_job_btn_focus_reminder"]')
                .contains("It's focused!")
                .click({ force: true });
        } else {
            cy.get('[id="laserhead_focus_reminder_modal"]').should(
                "not.be.visible"
            );
        }
    });
});

Cypress.Commands.add("hardResetModal", () => {
    cy.wait(3000);
    cy.get("body").then(($body) => {
        let reminderLaser = $body.find("#hard_refresh_overlay");
        if (reminderLaser.is(":visible")) {
            cy.get("#hard_refresh_checkbox").click();
            cy.get("#hard_refresh_overlay > .modal-footer > .btn").click({
                force: true,
            });
        } else {
            cy.get("#hard_refresh_overlay").should("not.be.visible");
        }
    });
});

Cypress.Commands.add("logout", () => {
    cy.get('[id="navbar_login"]').click();
    cy.get('[id="logout_button"]').click({ force: true });
});

Cypress.Commands.add("assertValueCopiedToClipboard", (value) => {
    cy.window().then((win) => {
        win.navigator.clipboard.readText().then((text) => {
            expect(text).to.eq(value);
        });
    });
});

Cypress.Commands.add("deleteGcoFile", () => {
    cy.get('[data-test="mrbeam-ui-index-design-library"]').click({
        force: true,
    });
    cy.get('[data-test="tab-designlib-filter-gcode-radio"]').click({
        force: true,
    });
    cy.wait(3000);
    cy.get('[data-test="tab-designlib-mechinecode-file-card"]')
        .if("exist")
        .then(() => {
            cy.get('[data-test="tab-designlib-mechinecode-file-card"]')
                .realHover({ multiple: true, force: true })
                .get('[data-test="tab-designlib-select-box"]')
                .click({ multiple: true, force: true });
            cy.get('[data-test="tab-designlib-delete-selection"]').click();
            cy.get('[data-test="tab-designlib-preview-card"]').should(
                "not.exist"
            );
        });
    cy.get('[data-test="tab-designlib-filter-design-radio"]').click();
    cy.get('[data-test="mrbeam-ui-index-working-area"]').click();
});

Cypress.Commands.add("designSettings", () => {
    cy.get('[data-test="tab-workingarea-rotation"]')
        .filter(":visible")
        .last()
        .clear({ force: true })
        .type("-50.5");
    cy.get('[data-test="tab-workingarea-horizontal"]')
        .filter(":visible")
        .last()
        .clear({ force: true })
        .type("116.3 mm");
    cy.get('[data-test="tab-workingarea-vertical"]')
        .filter(":visible")
        .last()
        .clear({ force: true })
        .type("132.3 mm");
});

Cypress.Commands.add("laserButtonClick", () => {
    cy.get('[data-test="working-area-laser-button"]').invoke(
        "removeAttr",
        "disabled"
    );
    cy.get('[data-test="working-area-laser-button"]').click();
    cy.focusReminder();
    cy.wait(3000);
});

Cypress.Commands.add("onlyLaserButtonClick", () => {
    cy.get('[data-test="working-area-laser-button"]').invoke(
        "removeAttr",
        "disabled"
    );
    cy.get('[data-test="working-area-laser-button"]').click();
});

Cypress.Commands.add("selectMaterial", () => {
    cy.get('[data-test="conversion-dialog-material-item"]')
        .contains("Cardboard, single wave")
        .click({ force: true });
    cy.wait(1000);
    cy.get('[data-test="conversion-dialog-material-color"]')
        .first()
        .if("exist")
        .click();
    cy.wait(1000);
    cy.get('[data-test="conversion-dialog-thickness-sample"]')
        .first()
        .if("exist")
        .click();
});

Cypress.Commands.add("downloadMrbFile", () => {
    cy.get('[data-test="tab-designlib-filter-recent-radio"]').click();
    cy.wait(2000);
    cy.get('[data-test="tab-designlib-recentjob-file-card"]')
        .first()
        .find('[data-test="tab-designlib-recentjob-file-icon-reorder"]')
        .click({ force: true })
        .invoke("prop", "innerText")
        .then((downloadFile) => {
            cy.intercept(
                "GET",
                `http://localhost:5002/downloads/files/local/${downloadFile}*`
            ).as("file");
            cy.window()
                .document()
                .then(function (doc) {
                    doc.addEventListener("click", () => {
                        setTimeout(function () {
                            doc.location.reload();
                        }, 5000);
                    });
                    cy.get('[data-test="tab-designlib-recentjob-file-card"]')
                        .filter(`:contains(${downloadFile})`)
                        .find(
                            '[data-test="tab-designlib-recentjob-file-icon-reorder"]'
                        );
                    cy.wait(1000);
                    cy.get(
                        '[data-test="tab-designlib-recentjob-file-download"]'
                    )
                        .filter(":visible")
                        .click();
                });
        });
});

import "cypress-file-upload";
import "cypress-if";
