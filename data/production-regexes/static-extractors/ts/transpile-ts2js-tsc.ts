#!/usr/bin/env node

// Transpile TS to JS using tsc.
//
// Roughly equivalent to some command-line invocation of tsc,
// but I'm not sure which one. Anyway...

import * as ts from "typescript";
import * as fs from "fs";

// Accepts a tsFile as argument.
if (process.argv.length != 3) {
  console.log(`Usage: ${require('path').basename(process.argv[1])} ts-file.ts`);
  console.log(`  Transpiles TS to JS and prints to stdout`);
  process.exit(1);
}
const tsFile = process.argv[2];
const tsCode = fs.readFileSync(process.argv[2], "utf8");

// Transpile

// https://github.com/Microsoft/TypeScript-wiki/blob/master/Using-the-Compiler-API.md#a-simple-transform-function
try {
  let result = ts.transpileModule(tsCode, {
    compilerOptions: { module: ts.ModuleKind.CommonJS }
  });

  // Emit
  console.log(result.outputText);
  process.exit(0);
} catch (err) {
  console.error(`Error: ${err}`);
  process.exit(1);
}

