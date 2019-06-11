#!/usr/bin/env python3
# Extract the regexes from a Rust source file.
# Approach: tokenize the source file and look for a sequence of
# tokens of the form 'Regex::new(...).
# Caveats:
#   - The built-in Regex module may be imported under an alias.
#     We miss any declarations that use this alias ("false negatives").
#   - Another module may be imported under the alias 'Regex'.
#     If this module has a method 'new', we will treat calls to this
#     method as a regex creation ("false positives").

# Import libLF
import os
import sys
import re
sys.path.append('{}/lib'.format(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT']))
import libLF

import argparse
import shutil
import json

from collections import deque

def getTokenTree(rustc, rustFile):
  """Get parse tree for this Rust file.

  @param rustc - str - invocable rustc
  @param rustFile - str - file to parse
  @return tokenTree - obj - parsed JSON string from rustc
  """

  # Try unexpanded first. It seems to work more consistently, 
  # and in some of our test files the macro expansion removes a regex declaration
  # (e.g. rust-clippy/clippy_dev/src/lib.rs)
  cmd_noexp = "'{}' -Z ast-json-noexpand '{}' 2>/dev/null".format(rustc, rustFile)
  cmd_exp = "'{}' -Z ast-json '{}' 2>/dev/null".format(rustc, rustFile)
  for cmd in [cmd_noexp, cmd_exp]:
    _, out = libLF.runcmd(cmd)
    out = out.strip()

    # We don't care about complaints as long as it produces json
    if libLF.isNDJSON(out):
      return json.loads(out)
    else:
      libLF.log('Not NDJSON:\n{}'.format(out))
  raise ValueError('Could not get token tree from {}'.format(rustFile))
  

def walkTokenTree(root, frontierVisitor):
  """Walk parse tree
  
  This is safe to call from any kind of token-ish node"""
  # Must be iterative; tree is very deep.
  libLF.log('walking parse tree')

  # Regexes are commonly declared in an expression like this:
  #   Regex::new("str")
  #   Regex::new(r"str")
  # This declaration is tokenized as:
  #   Token->Ident->"Regex"
  #   Token->ModSep
  #   Token->Ident->"new"
  #   Delimited->Paren->Token->fields[x]->Literal->StrRaw
  # These tokens occur "together" as children of the expression,
  # and so our token tree BFS will produce such tokens one after another
  # in the relevant frontier. 

  # BFS.
  frontier = deque([root])
  depth = 0
  while len(frontier): # Repeat until an iteration results in an empty frontier.
    libLF.log('Exploring depth {} ({} nodes)'.format(depth, len(frontier)))
    nextFrontier = [] # No duplicates are possible in this environment, so no need for a set.

    # Give the frontierVisitor the current frontier.
    frontierVisitor.visitFrontier(frontier)

    # Build nextFrontier
    for node in frontier:
      # Append any children -- dict keys, list elems
      if type(node) is dict:
        for k in node.keys():
          nextFrontier.append(node[k])
      elif type(node) is list:
        for n in node:
          nextFrontier.append(n)

    # We exhausted frontier.
    # Replace it with nextFrontier.
    frontier = deque(nextFrontier)
    nextFrontier = []
    depth += 1

  libLF.log('Done walking')

class FrontierVisitor:
  """BFS FrontierVisitor to find token sequences like "Regex::new('str')".

  Detecting regexes requires examining multiple nodes.
  It's cheaper and easier to code if we work on the whole frontier rather than visiting
  nodes one by one.
  """
  def __init__(self):
    self.patterns = []

  def _addRegexPattern(self, regexPattern):
    self.patterns.append(regexPattern)
  
  def getRegexPatterns(self):
    """Returns a list of the regex patterns we saw during the traversal

    NB: In Rust, regex flags are inlined in the pattern.
    
    Returns:
      patterns str[]"""
    return self.patterns
  
  def _extractRegexPattern(self, delimitedTokenNode):
    """Extract the regex pattern from within this node.

    This node is the (...) from a Regex::new(...) call.
    """
    libLF.log('  delimitedNode of interest: {}'.format(json.dumps(delimitedTokenNode)))
    try:
      parenNode = delimitedTokenNode['fields'][1] 
      arg1 = parenNode['tts'][0]

      if parenNode['delim'] == "Paren" and arg1['variant'] == "Token":
        arg1Value = arg1['fields'][1]
        if arg1Value['variant'] == "Literal":
          argField = arg1Value['fields'][0] 
          # Tokens occur before the resolution of raw vs. "normal" strings.
          # In raw strings, a backslash is interpreted literally rather than escaping something,
          # with the exceptions of \x7F, \u{123}, \n, \0, and \\.
          #   e.g. r#"\d" to denote a digit in regex notation.
          # In "normal" strings, a backslash is needed to escape characters that would otherwise be special,
          #   e.g. "\\d" to denote a digit in regex notation.
          # Details here: https://doc.rust-lang.org/reference/tokens.html#raw-string-literals
          rawPattern = None
          if argField['variant'] == "StrRaw":
            # Raw strings are interpreted as patterns as-is.
            rawPattern = argField['fields'][0]
          elif argField['variant'] == "Str_":
            strPattern = str(argField['fields'][0])
            rawPattern = libLF.unescapeDoubleQuotes(strPattern)
          else:
            # TODO Can any other types occur here?
            print('Hmm, what have we here? {}'.format(argField))
            sys.exit(1)
          self._addRegexPattern(rawPattern)
        else: # Arg is not a Literal. DYNAMIC pattern.
          self._addRegexPattern("DYNAMIC")
    except:
      pass
  
  def visitFrontier(self, tokenNodes):
    # Consider every sequence of four nodes: Regex, ::, new, and ()
    for i in range(0, len(tokenNodes) - 4 + 1):
      regexNode = tokenNodes[i]
      colonsNode = tokenNodes[i+1]
      newNode = tokenNodes[i+2]
      delimitedNode = tokenNodes[i+3]

      if type(regexNode) is dict \
          and type(colonsNode) is dict \
          and type(newNode) is dict \
          and type(delimitedNode) is dict:
        try:
          regexNode_true = regexNode['variant'] == "Token" \
                          and regexNode['fields'][1]['variant'] == "Ident" \
                          and regexNode['fields'][1]['fields'][0] == "Regex"
          colonsNode_true = colonsNode['variant'] == "Token" \
                          and colonsNode['fields'][1] == "ModSep"
          newNode_true = newNode['variant'] == "Token" \
                        and newNode['fields'][1]['variant'] == "Ident" \
                        and newNode['fields'][1]['fields'][0] == "new"
          delimitedNode_true = delimitedNode['variant'] == "Delimited" \
                              and delimitedNode['fields'][1]['delim'] == "Paren"

          if regexNode_true and colonsNode_true and newNode_true and delimitedNode_true:
            libLF.log('Found Regex::new(...)')
            self._extractRegexPattern(delimitedNode)
        except BaseException as err:
          pass

def fileMightContainRegexes(rustFile):
  """Fast grep-based check on whether a regex is possible.

  True if grep finds 'Regex' in the file, else false.
  Our token tree analysis only finds regexes that involve the string "Regex", so...
  """
  _, out = libLF.runcmd("grep Regex '{}'".format(rustFile))
  if 0 <= out.find('Regex'):
    return True
  return False

def main(rustc, rustFile, dumpTokenTree):
  libLF.checkShellDependencies([rustc])

  if fileMightContainRegexes(rustFile):
    libLF.log('File might contain regexes, proceeding...')
    try:
      libLF.log('Getting token tree')
      tokenTree = getTokenTree(rustc, rustFile)
    except BaseException as err:
      libLF.log('Error getting token tree: {}'.format(err))
      sys.exit(1)
  
    try:
      libLF.log('Walking token tree')
      visitor = FrontierVisitor()
      walkTokenTree(tokenTree, visitor) 
      patterns = visitor.getRegexPatterns()
      libLF.log('Extracted {} patterns'.format(len(patterns)))
    except BaseException as err:
      libLF.log('Error walking token tree: {}'.format(err))
      sys.exit(1)
  else:
    libLF.log('File does not contain "Regex", no regexes possible')
    patterns = []

  regexes = [{'pattern': p, 'flags': ''} for p in patterns]
  sfwr = libLF.SimpleFileWithRegexes()
  sfwr.initFromRaw(fileName=rustFile, language='rust', couldParse=1, regexes=regexes)
  print(sfwr.toNDJSON())

  if dumpTokenTree:
    # "Pretty" JSON makes it easier for humans to decode
    asJSON = json.dumps(tokenTree, indent=2, separators=(',', ':'))
    libLF.log('\n' + asJSON)

###############################################

# Parse args
parser = argparse.ArgumentParser(description='Extract the regexes from a Rust source file.')
parser.add_argument('rustFile', help='Rust file')
parser.add_argument('--rustc', help='Which rustc to use? Default is whatever is in the PATH. Must be a "nightly" because we need -Z to work', required=False, default='rustc', dest='rustc')
parser.add_argument('--dumpTokenTree', help='Dump the token tree to stderr. It is large.', required=False, default=False, action='store_true')

args = parser.parse_args()
# Here we go!
main(args.rustc, args.rustFile, args.dumpTokenTree)
