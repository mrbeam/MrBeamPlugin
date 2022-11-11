// cypress-ci-run.ts

/**
 * This script runs Cypress tests in CI. It exists because we need to get split
 * up the tests between multiple runners, but we can't run that script in a way
 * that will pass a value to --spec directly, using cypress-io/github-action's
 * `command` property. It just won't let us include an env variable or do
 * command substitution.
 *
 * So, we can either just not use cypress-io/github-action or use a script like
 * this one to run the tests.
 */
import { exec } from 'child_process';

type GetEnvOptions = {
  required?: boolean;
};

function getEnvNumber(varName: string, { required = false }: GetEnvOptions = {}): number {
  if (required && process.env[varName] === undefined) {
    throw Error(`${varName} is not set.`);
  }

  const value = Number(process.env[varName]);

  if (isNaN(value)) {
    throw Error(`${varName} is not a number.`);
  }

  return value;
}

function getArgs() {
  return {
    totalRunners: getEnvNumber('TOTAL_RUNNERS', { required: true }),
    thisRunner: getEnvNumber('THIS_RUNNER', { required: true }),
  };
}

(async () => {
  try {
    const { totalRunners, thisRunner } = getArgs();

    const command = `yarn cypress run --spec "$(yarn --silent ts-node --quiet cypress/scripts/cypress-spec-split.ts ${totalRunners} ${thisRunner})"`;

    console.log(`Running: ${command}`);

    const commandProcess = exec(command);

    // pipe output because we want to see the results of the run

    if (commandProcess.stdout) {
      commandProcess.stdout.pipe(process.stdout);
    }

    if (commandProcess.stderr) {
      commandProcess.stderr.pipe(process.stderr);
    }

    commandProcess.on('exit', (code) => {
      process.exit(code || 0);
    });
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
})();
