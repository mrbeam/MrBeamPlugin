const { defineConfig } = require("cypress");

module.exports = defineConfig({
    projectId: "zpa4f8",
    defaultCommandTimeout: 10000,
    requestTimeout: 30000,
    screenshotOnRunFailure: true,
    video: true,
    videoUploadOnPasses: false,
    viewportHeight: 980,
    viewportWidth: 1920,
    chromeWebSecurity: false,
    numTestsKeptInMemory: 0,
    e2e: {
        experimentalStudio: true,
        experimentalRunAllSpecs: true,
        setupNodeEvents(on, config) {
            return require("./cypress/plugins/index.js")(on, config);
        },
        baseUrl: "http://localhost:5002/",
    },
    reporter: "junit",
    reporterOptions: {
        mochaFile: "cypress/results/test-results-[hash].xml",
        testCaseSwitchClassnameAndName: false,
    },
    compilerOptions: {
        types: ["cypress", "@4tw/cypress-drag-drop"],
        types: ["cypress", "node", "cypress-real-events"],
    },
});
