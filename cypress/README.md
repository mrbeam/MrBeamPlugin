## How to run cypress tests:

1. Run docker container => how to build and run a docker image can be found at the root README.md of this repo
2. Open terminal and go to the root folder of the repo:

```shell
cd ./MrBeamPlugin
```

3. Install dependencies:

```shell
nvm install 18.7.0
npm install
```

4. Run cypress app

```shell
npm run cypress:open
```

5. click E2E Testing
6. Start E2E Testing in {selected browser}


## How to generate JUnit reports
1. Run cypress
    ```shell
    npm run cypress:run
    ```
    This will generate a xml report per test file

2. Merge all the xml reports into one
    ```shell
    npm run merge-reports
    ```
3. Import the merged results xml to Jira
