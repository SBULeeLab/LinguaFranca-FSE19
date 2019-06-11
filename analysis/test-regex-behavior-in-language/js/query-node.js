#!/usr/bin/env node
// Author: Jamie Davis <davisjam@vt.edu>
// Description: Test regex in Node.js

var fs = require('fs');

// Arg parsing.
var queryFile = process.argv[2];
if (!queryFile) {
  console.log(`Error, usage: ${process.argv[1]} query-file.json`);
  process.exit(1);
}

// Load query from file.
var query = JSON.parse(fs.readFileSync(queryFile, 'utf-8'));

// Check query is valid.
var validQuery = true;
var requiredQueryKeys = ['pattern', 'inputs'];
requiredQueryKeys.forEach((k) => {
  if (typeof(query[k]) === 'undefined') {
    validQuery = false;
  }
});
if (!validQuery) {
  console.error(`Error, invalid query. Need keys ${JSON.stringify(requiredQueryKeys)}. Got ${JSON.stringify(query)}`);
  process.exit(1);
}

// Try to match string against pattern.
var result = query;

results = [];
try {
	var re = new RegExp(query.pattern);
	result.validPattern = 1;

  query['inputs'].forEach(input => {
    console.error(`matching: pattern /${query.pattern}/ inputStr: len ${input.length}`);

    var jsMatch = input.match(re); // Partial-match semantics
    //console.error(`pattern /${query.pattern}/ input <${input}> jsMatch <${jsMatch}>`);
    var matched = jsMatch ? 1 : 0;
    var matchedString = '';
    var captureGroups = [];
    if (matched) {
      matchedString = jsMatch[0];
      captureGroups = jsMatch.slice(1).map(g => {
        // Convert unused groups (null) to empty captures ("") for cross-language consistency
        if (g == null) { 
          return '';
        } else {
          return g;
        }
      });
    }
    results.push({
      "input": input,
      "matched": matched,
      "matchContents": {
        "matchedString": matchedString,
        "captureGroups": captureGroups,
      },
    });
  });
} catch (e) {
  console.error(e);
	result.validPattern = 0;
}
result.results = results;

console.log(JSON.stringify(result));

process.exit(0);
