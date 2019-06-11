#!/usr/bin/env node

/**
 * Author: Jamie Davis <davisjam@vt.edu>
 * Author: Daniel Moyer
 *
 * Description: Print all statically-declared regexes in the specified JavaScript file.
 *              Prints a JSON object with keys: filename regexes[]
 *                     filename is the path provided
 *                     regexes is an array of objects, each with keys: pattern flags
 *                       pattern and flags are each either a string or 'DYNAMIC-{PATTERN|FLAGS}' 
 *
 * Requirements:
 *   - run npm install
 *   - ECOSYSTEM_REGEXP_PROJECT_ROOT must be defined
 */

"use strict";

const traverse = require("./traverse").traverse,
  fs = require("fs");

// Usage
if (process.argv.length != 3) {
  console.log('Usage: ' + process.argv[1] + ' source-to-analyze.js');
  console.error(`You gave ${JSON.stringify(process.argv)}`);
  process.exit(0);
}

// Check for dependencies
if (!process.env.ECOSYSTEM_REGEXP_PROJECT_ROOT) {
  console.log('Error, must define env var ECOSYSTEM_REGEXP_PROJECT_ROOT');
  process.exit(1);
}

const sourceF = process.argv[2];
const source = fs.readFileSync(sourceF, { encoding: 'utf8' });

traverse(source, sourceF).catch((e) => {
  const result = {
    fileName: sourceF,
    language: 'JavaScript',
    couldParse: 0,
    regexes: []
  };
  console.log(JSON.stringify(result));
});
