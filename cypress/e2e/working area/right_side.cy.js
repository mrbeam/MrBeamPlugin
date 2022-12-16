describe("Laser Job", function () {
    beforeEach(function () {
        cy.fixture("test-data").then(function (testData) {
            this.testData = testData;
        });
    });

    beforeEach(function () {
        cy.visit(this.testData.url_laser);
        cy.wait(20000);
        cy.loginLaser(this.testData.email, this.testData.password);
        cy.visit(this.testData.url_laser);
    });

    it("Transform", function () {
        cy.get('[data-test="working-area-tab-text"]').click();
        cy.get('[data-test="quick-text-modal-text-input"]').type("MrBeam");
        cy.get('[data-test="quick-text-done-button"]').click();
        cy.get('[id="mbtransformTranslateGroup"]')
            .invoke("attr", "transform")
            .then((transformTranslate) => {
                cy.get('[id="translateHandle"]').move({
                    deltaX: -433.9689,
                    deltaY: -220.1241,
                    force: true,
                });
                cy.get('[id="mbtransformTranslateGroup"]').should(
                    "not.eq",
                    `${transformTranslate}`
                );
            });
        cy.get('[id="mbtransformScaleGroup"]')
            .invoke("attr", "transform")
            .then((transformSize) => {
                cy.get('[id="scaleHandleNW"]').move({
                    deltaX: 34.9689,
                    deltaY: 20.1241,
                    force: true,
                });
                cy.get('[id="mbtransformScaleGroup"]').should(
                    "not.eq",
                    `${transformSize}`
                );
            });
        cy.get('[id="mbtransformRotateGroup"]')
            .invoke("attr", "transform")
            .then((transformRotate) => {
                cy.get('[id="rotHandle"]').move({
                    deltaX: 53.9689,
                    deltaY: 70.1241,
                    force: true,
                });
                cy.get('[d="mbtransformRotateGroup"]').should(
                    "not.eq",
                    `${transformRotate}`
                );
            });
    });
});
