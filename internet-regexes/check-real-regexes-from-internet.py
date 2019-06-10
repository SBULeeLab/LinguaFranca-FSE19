#!/usr/bin/env python3
# Description:
#   Compare a file of "real regexes" to a file of "InternetRegexSources"

# Import our lib
import os
import sys
sys.path.append('{}/lib'.format(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT']))
import libLF

from contextlib import ExitStack
from functools import partial
import json
import sys
import os
import argparse
import re

# input: readable file stream
# output: dictionary mapping key 'pattern' to a list of the InternetRegexSources that define this pattern
def getInternetPatternsDict(internetPatternsStream):
  internetPatterns = {}

  internetPatternsStream.seek(0)
  for line in internetPatternsStream:
    # Skip blank lines
    if re.match('^\s*$', line):
      continue

    libLF.log('Handling line <{}>'.format(line))
    source = libLF.InternetRegexSource.factory(line)
    libLF.log('Got InternetSource: {}'.format(source.toNDJSON()))

    for pattern in source.patterns:
      if pattern in internetPatterns:
        internetPatterns[pattern].append(source)
      else:
        internetPatterns[pattern] = [source]
  libLF.log('Read in {} unique internetPatterns'.format(len(internetPatterns.keys())))
  return internetPatterns

def main(internetPatternsFile, realPatternsFile, writingDifficultyThreshold, outFile):
  with ExitStack() as stack:
    internetPatternsStream = stack.enter_context(open(internetPatternsFile, 'r'))
    realPatternsStream = stack.enter_context(open(realPatternsFile, 'r'))
    outStream = stack.enter_context(open(outFile, 'w'))

    internetPatternsDict = getInternetPatternsDict(internetPatternsStream)
    uniqueModulesWithInternetRegexSource = set()

    for line in realPatternsStream:
      # Skip blank lines
      if re.match('^\s*$', line):
        continue

      # TODO Python representation of RegexpUsage for the regexes we extract in the future.
      # For now, load a raw regexp object from ESEC/FSE and check for a match in our dict
      obj = libLF.fromNDJSON(line)

      # Discard patterns that could be independently derived.
      if libLF.scorePatternWritingDifficulty(obj['pattern']) < writingDifficultyThreshold:
        continue

      if obj['pattern'] in internetPatternsDict:
        libLF.log('realPattern /{}/ matches internet source'.format(obj['pattern']))
        obj['internetSources'] = [ o.toNDJSON() for o in internetPatternsDict[obj['pattern']] ]
        for module in obj['modules']:
          uniqueModulesWithInternetRegexSource.add(module)
      else:
        libLF.log('realPattern /{}/ does not match internet source'.format(obj['pattern']))
        obj['internetSources'] = []
      outStream.write(json.dumps(obj, sort_keys=True) + '\n')

    libLF.log('{} unique modules contained regexes from internet sources:\n{}'.format(len(uniqueModulesWithInternetRegexSource), uniqueModulesWithInternetRegexSource))

###############################################

# Parse args
parser = argparse.ArgumentParser(description='Determine whether regex patterns from source code match an Internet source')
parser.add_argument('--internet-patterns', '-i', help='Path to Internet regexes file. See internet-regexps/README.md for format.', required=True)
parser.add_argument('--real-patterns', '-r', help='Path to real regexes file. See ecosystem-regexps/README.md for format.', required=True)
parser.add_argument('--writing-difficulty-threshold', '-d', help='Only consider patterns >= this writing difficulty. Below this we consider independent derivation possible', type=int, default=0, required=False)
parser.add_argument('--out-file', '-o', help='Where to write results?', required=True)

args = parser.parse_args()

assert(0 <= args.writing_difficulty_threshold)

# Here we go!
main(args.internet_patterns, args.real_patterns, args.writing_difficulty_threshold, args.out_file)
