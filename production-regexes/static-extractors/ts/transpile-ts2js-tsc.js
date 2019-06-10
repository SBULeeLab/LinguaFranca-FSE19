#!/usr/bin/env node
"use strict";
exports.__esModule = true;
var ts = require("typescript");
var fs = require("fs");
// Accepts a tsFile as argument.
if (process.argv.length != 3) {
    console.log("Usage: " + require('path').basename(process.argv[1]) + " ts-file.ts");
    console.log("  Transpiles TS to JS and prints to stdout");
    process.exit(1);
}
var tsFile = process.argv[2];
var tsCode = fs.readFileSync(process.argv[2], "utf8");
// Transpile
// https://github.com/Microsoft/TypeScript-wiki/blob/master/Using-the-Compiler-API.md#a-simple-transform-function
try {
    var result = ts.transpileModule(tsCode, {
        compilerOptions: { module: ts.ModuleKind.CommonJS }
    });
    // Emit
    console.log(result.outputText);
    process.exit(0);
}
catch (err) {
    console.error("Error: " + err);
    process.exit(1);
}
