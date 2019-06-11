#!/usr/bin/env python3
# Author: Jamie Davis <davisjam@vt.edu>
# Description: Test regex in Python

import sys
import json
import re

def main():
  # Arg parsing.
  if len(sys.argv) != 2:
    print("Error, usage: {} query-file.json".format(sys.argv[0]))
    sys.exit(1)

  queryFile = sys.argv[1]

  with open(queryFile, 'r', encoding='utf-8') as FH:
    cont = FH.read()
    log("Contents of {}: {}".format(queryFile, cont))
    obj = json.loads(cont)

  # Prepare a regexp
  resultObjects = []
  try:
    regexp = re.compile(obj['pattern'])
    obj['validPattern'] = True

    for stringToTry in obj['inputs']:
      resultObj = { 'input': stringToTry }

      # Try a match
      log("matching: pattern /{}/ input: length {}".format(obj['pattern'], len(stringToTry)))
      #matchResult = regexp.match(obj['input']) # Full-match semantics -- better case
      matchResult = regexp.search(stringToTry) # Partial-match semantics -- worse case

      # Print result
      resultObj['inputLength'] = len(stringToTry)
      resultObj['matched'] = 1 if matchResult else 0
      if matchResult:
        resultObj['matched'] = 1
        resultObj['matchContents'] = {
          'matchedString': matchResult.group(0),
          'captureGroups': [g if g is not None else "" for g in matchResult.groups()]
        }
      else:
        resultObj['matched'] = 0
        resultObj['matchContents'] = {}
      resultObjects.append(resultObj)
  except BaseException as e:
    log('Exception: ' + str(e))
    obj['validPattern'] = False
  
  obj['results'] = resultObjects
  sys.stdout.write(json.dumps(obj) + '\n')

def log(msg):
  sys.stderr.write(msg + '\n')

############

main()
