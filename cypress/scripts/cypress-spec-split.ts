// Script from https://echobind.com/post/running-cypress-tests-in-parallel

// cypress-spec-split.ts

import { promises as fs } from 'fs';
import globby = require("globby");
import { Minimatch } from 'minimatch';

// These are the same properties that are set in cypress.config.
// In practice, it's better to export these from another file, and
// import them here and in cypress.config, so that both files use
// the same values.
const specPatterns = {
  specPattern: './cypress/e2e/**/*.cy.{ts,tsx,js,jsx}',
  excludeSpecPattern: ['tsconfig.json'],
};

// used to roughly determine how many tests are in a file
const testPattern = /(^|\s)(it|test)\(/g;

const isCli = require.main?.filename === __filename;

function getArgs() {
  const [totalRunnersStr, thisRunnerStr] = process.argv.splice(2);

  if (!totalRunnersStr || !thisRunnerStr) {
    throw new Error('Missing arguments');
  }

  const totalRunners = totalRunnersStr ? Number(totalRunnersStr) : 0;
  const thisRunner = thisRunnerStr ? Number(thisRunnerStr) : 0;

  if (isNaN(totalRunners)) {
    throw new Error('Invalid total runners.');
  }

  if (isNaN(thisRunner)) {
    throw new Error('Invalid runner.');
  }

  return { totalRunners, thisRunner };
}

async function getTestCount(filePath: string): Promise<number> {
  const content = await fs.readFile(filePath, 'utf8');
  return content.match(testPattern)?.length || 0;
}

// adapated from:
// https://github.com/bahmutov/find-cypress-specs/blob/main/src/index.js
async function getSpecFilePaths(): Promise<string[]> {
  const options = specPatterns;

  const files = await globby(options.specPattern, {
    ignore: options.excludeSpecPattern,
  });

  // go through the files again and eliminate files that match
  // the ignore patterns
  const ignorePatterns = [...(options.excludeSpecPattern || [])];

  // a function which returns true if the file does NOT match
  // all of our ignored patterns
  const doesNotMatchAllIgnoredPatterns = (file: string) => {
    // using {dot: true} here so that folders with a '.' in them are matched
    // as regular characters without needing an '.' in the
    // using {matchBase: true} here so that patterns without a globstar **
    // match against the basename of the file
    const MINIMATCH_OPTIONS = { dot: true, matchBase: true };
    return ignorePatterns.every((pattern) => {
      return !new Minimatch(pattern, MINIMATCH_OPTIONS).match(file);
    });
  };

  const filtered = files.filter(doesNotMatchAllIgnoredPatterns);

  return filtered;
}

async function sortSpecFilesByTestCount(specPathsOriginal: string[]): Promise<string[]> {
  const specPaths = [...specPathsOriginal];

  const testPerSpec: Record<string, number> = {};

  for (const specPath of specPaths) {
    testPerSpec[specPath] = await getTestCount(specPath);
  }

  return (
    Object.entries(testPerSpec)
      // Sort by the number of tests per spec file, so that we get a bit closer to
      // splitting up the files evenly between the runners. It won't be perfect,
      // but better than just splitting them randomly. And this will create a
      // consistent file list/ordering so that file division is deterministic.
      .sort((a, b) => b[1] - a[1])
      .map((x) => x[0])
  );
}

export function splitSpecs(specs: string[], totalRunners: number, thisRunner: number): string[] {
  return specs.filter((_, index) => index % totalRunners === thisRunner);
}

(async () => {
  // only run this if called via the CLI
  if (!isCli) {
    return;
  }

  try {
    const specFilePaths = await sortSpecFilesByTestCount(await getSpecFilePaths());

    if (!specFilePaths.length) {
      throw Error('No spec files found.');
    }

    const { totalRunners, thisRunner } = getArgs();

    const specsToRun = splitSpecs(specFilePaths, totalRunners, thisRunner);

    console.log(specsToRun.join(','));
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
})();
