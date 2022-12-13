describe("About This Mr Beam", function () {
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

    it("Quickstart Guide - de", function () {
        cy.get('[data-test="about-settings-link-quickstart"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    it("Quickstart Guide - en", function () {
        cy.get(':nth-child(1) > [data-test="about-settings-link-quickstart"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    it("User manual - online", function () {
        cy.get(
            ':nth-child(1) > [data-test="about-settings-link-quickstart-online"]'
        )
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    it("User manual - de", function () {
        cy.get('[data-test="about-settings-link-quickstart"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    it("User manual - en", function () {
        cy.get(':nth-child(2) > [data-test="about-settings-link-quickstart"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    it("User manual - es", function () {
        cy.get('[data-test="about-settings-link-quickstart"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    it("User manual - fr", function () {
        cy.get('[data-test="about-settings-link-quickstart"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    it("User manual - it", function () {
        cy.get('[data-test="about-settings-link-quickstart"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    it("User manual - nl", function () {
        cy.get('[data-test="about-settings-link-quickstart"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    it("Link IG", function () {
        cy.get('[data-test="about-settings-link-instagram"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    it("Link twitter", function () {
        cy.get('[data-test="about-settings-link-twitter"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    it("Link YT", function () {
        cy.get('[data-test="about-settings-link-youtube"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    it("Link pinterest", function () {
        cy.get('[data-test="about-settings-link-pinterest"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    // Linkedin status code 999
    it.only("Links - linkedin", function () {
        cy.get('[data-test="about-settings-link-linkedin"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request({
                    failOnStatusCode: false,
                    method: "GET",
                    url: myLink,
                    followRedirect: false,
                  }).then((response) => {
                    expect(response.status).to.eq(200);
                  })
                });
                
    });
    it("Link TikTok", function () {
        cy.get('[data-test="about-settings-link-tiktok"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
    });
    it("Link Official user group", function () {
        cy.get('[data-test="about-settings-link-facebook-group"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    it("Link find.mr-beam service", function () {
        cy.get('[data-test="about-settings-link-find-mr-beam-org"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
    });
    it("Link Online resources", function () {
        cy.get('[data-test="about-settings-link-downloads"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    it("Link Source code", function () {
        cy.get('[data-test="about-settings-link-github"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    it("Link Recommend Mr Beam", function () {
        cy.get('[data-test="about-settings-link-aklamio"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    it("User manual - online", function () {
        cy.get(
            ':nth-child(2) > [data-test="about-settings-link-quickstart-online"]'
        )
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    it("Link support", function () {
        cy.get('[data-test="about-settings-link-support"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });

    it.only("Link privacy", function () {
        cy.get('[data-test="about-settings-link-web-site"]')
        .invoke("attr", "href")
        .then((myLink) => {
            cy.request({
                failOnStatusCode: false,
                method: "GET",
                url: myLink,
                followRedirect: false,
                failOnStatusCode: false 
              }).then((resp) => {
                expect(resp.status).to.eq(200)                
              })
            });
    });
    it("Privacy Policies - service", function () {
        cy.get('[data-test="about-settings-link-find-mr-beam"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    it("Privacy Policies - analytics", function () {
        cy.get('[data-test="about-settings-link-analytics"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
    it("Link - mr-beam.org", function () {
        cy.get('[data-test="about-settings-link-mr-beam-org"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });

    it("Link fb", function () {
        cy.get('[data-test="about-settings-link-facebook"]')
            .invoke("attr", "href")
            .then((myLink) => {
                cy.request(myLink).then((resp) => {
                    expect(resp.status).to.eq(200);
                });
            });
        cy.logout();
    });
});
