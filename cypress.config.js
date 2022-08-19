const { defineConfig } = require("cypress");

module.exports = defineConfig({
    defaultCommandTimeout: 10000,
    requestTimeout: 30000,
    screenshotOnRunFailure: true,
    video: true,
    videoUploadOnPasses: false,
    viewportHeight: 980,
    viewportWidth: 1920,
    chromeWebSecurity: false,
    e2e: {
        setupNodeEvents(on, config) {
            return require("./cypress/plugins/index.js")(on, config);
        },
        baseUrl: "http://localhost:5002/",
    },
});
