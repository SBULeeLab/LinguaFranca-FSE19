/**
 * Author: Jamie Davis <davisjam@vt.edu>
 * Author: Daniel Moyer
 *
 * Helper module for extract-regexps.js and instrument-regexps.js
 */
const parse = require("@babel/parser").parse,
  traverse = require("babel-traverse").default,
  generate = require("babel-generator").default,
  template = require("babel-template"),
  types = require("babel-types"),
  fs = require("fs");

module.exports.traverse = function(source, sourceF, instrumentFile) {
  return new Promise((resolve, reject) => {
    let ast = 0;
    ast = parse(source, {
        sourceType: "module",
    });

    if (!ast) {
      ast = parse(source, {
          sourceType: "script",
      });
    }

    if (!ast) {
      reject("Error parsing " + sourceF);
    }

    const paths = [];
    const regexObjs = [];

    traverse(ast, {
      RegExpLiteral(path) {
        paths.push(path);
        regexObjs.push({
          'pattern': path.node.pattern,
          'flags': path.node.flags
        });
      },
      NewExpression(path) {
        const node = path.node;
        if (path.node.callee.type === 'Identifier' && path.node.callee.name === 'RegExp') {
          paths.push(path);
          const pattern = (node['arguments'][0].type === 'StringLiteral') ?
                           node['arguments'][0].value : 'DYNAMIC-PATTERN';

          let flags = '';
          if (2 <= node['arguments'].length) {
             flags = (node['arguments'][1].type === 'StringLiteral') ?
                        node['arguments'][1].value : 'DYNAMIC-FLAGS';
          }
          regexObjs.push({
            'pattern': pattern,
            'flags': flags
          });
        }
      },
      // The argument to the search, match, and matchAll String.prototype
      // methods is implicitly converted to a RegExp.
      CallExpression(path) {
        const methods = ['search', 'match', 'matchAll'];
        const callee = path.node.callee;
        if (path.node.arguments.length === 1
            && types.isMemberExpression(callee)
            && types.isIdentifier(callee.property)
            && methods.includes(callee.property.name)) {

          const arg = path.node.arguments[0];
          const pattern = arg.type === 'StringLiteral' ? arg.value : 'DYNAMIC-PATTERN';
          paths.push(path.get('arguments.0'));
          regexObjs.push({
            'pattern': pattern,
            'flags': ''
          });
        }
      }
    });

    if (instrumentFile) {
      // Replace each regex node in the AST with instrumentation code.
      paths.forEach(path => {
        // Create a template node. The instrumentation code is wrapped in an
        // immediately-invoked anonymous function that writes the regex to a
        // file and then returns it.
        const instrumentation = template(`
          (()=>{
            const regexp = new RegExp(REGEXP);
            const fs = require('fs');
            const obj = {'file': SOURCEF, 'pattern': regexp.source, 'flags': regexp.flags };
            fs.writeFileSync(FILE, JSON.stringify(obj) + "\\n", {flag: "a"});
            return regexp;
          })()
        `);

        // Modify the AST by replacing REGEXP in the template with the original
        // regex node (whether a literal or expression).
        path.replaceWith(instrumentation({
          REGEXP: path.node,
          FILE: types.stringLiteral(instrumentFile),
          SOURCEF: types.stringLiteral(sourceF)
        }));
      });

      console.log(generate(ast).code);
    } else {

      const fullObj = {
        fileName: sourceF,
        language: 'JavaScript',
        couldParse: 1,
        regexes: regexObjs
      };
      console.log(JSON.stringify(fullObj));
    }
  });
}
