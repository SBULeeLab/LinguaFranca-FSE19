#!/usr/bin/env node

/**
 * Author: Jamie Davis <davisjam@vt.edu>
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

const babylon = require("babylon"),
  traverse = require("babel-traverse"),
  fs = require("fs"),
  child_process = require('child_process');

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

var sourceF = process.argv[2];

// Parse and identify the regexes
var source = fs.readFileSync(sourceF, { encoding: 'utf8' });

var ast = 0;
if (!ast) {
  try {
    ast = babylon.parse(source, {
        sourceType: "module",
    });
  }
  catch (e) { ast = 0; }
}

if (!ast) {
  try {
    ast = babylon.parse(source, {
        sourceType: "script",
    });
  }
  catch (e) { ast = 0; }
}

if (!ast) {
  // Error parsing? Handle cleanly.
  bail_couldNotParse();
}

var allStaticRegexps = [];

try {
  traverse.default(ast, {
    enter(path) {
      var node = path.node;
      try {
        var regexpObj;

        if (node.type === 'RegExpLiteral') {
          var lineNumber = -1;
          if (node.loc != null){
            lineNumber = node.loc.start.line;
          }
          regexpObj = { pattern: node.pattern,
                        flags:   node.flags,
                        lineNumber: lineNumber
                      };
        }
        else if (node.type === 'NewExpression' && // new RegExp declaration
          node.callee.type === 'Identifier' && node.callee.name === 'RegExp') // of type RegExp
        {
          var pattern = (node['arguments'][0].type === 'StringLiteral') ?
                           node['arguments'][0].value : 'DYNAMIC-PATTERN';

          var flags = '';
          if (2 <= node['arguments'].length) {
             flags = (node['arguments'][1].type === 'StringLiteral') ?
                        node['arguments'][1].value : 'DYNAMIC-FLAGS';
          }
          var lineNumber = -1;
          if (node.loc != null){
            lineNumber = node.loc.start.line;
          }
          regexpObj = { pattern: pattern,
                        flags:   flags,
                        lineNumber: lineNumber
                      };
        }
      } catch (e) {} // Ignore all the null pointer exceptions -- regexes will not trigger NPEs.

      if (regexpObj) {
        allStaticRegexps.push(regexpObj);
      }
    }
  });
}
catch (e) {
  // Error traversing? Handle cleanly.
  bail_couldNotParse();
}

// Emit in a JSON array
var regexesArray = [];
allStaticRegexps.forEach((regexp) => {
  regexesArray.push(regexp);
});

var fullObj = { fileName: sourceF,
                language: 'JavaScript',
                couldParse: 1,
                regexes: regexesArray
              };
console.log(JSON.stringify(fullObj));

process.exit(0);

function bail_couldNotParse() {
  var result = { fileName: sourceF,
                 language: 'JavaScript',
                 couldParse: 0,
                 regexes: []
               };
  console.log(JSON.stringify(result));
  process.exit(0);
}
