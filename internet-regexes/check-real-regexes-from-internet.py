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

def main(internetPatternsFile, realPatternsFile, writingDifficultyThreshold):
  with ExitStack() as stack:
    internetPatternsStream = stack.enter_context(open(internetPatternsFile, 'r'))
    realPatternsStream = stack.enter_context(open(realPatternsFile, 'r'))

    internetPatternsDict = getInternetPatternsDict(internetPatternsStream)
    nRegexesMatchingInternetRegex = 0

    for line in realPatternsStream:
      # Skip blank lines
      if re.match(r'^\s*$', line):
        continue

      try:
        regex = libLF.Regex().initFromNDJSON(line)

        # Discard patterns that could be independently derived.
        if libLF.scorePatternWritingDifficulty(regex.pattern) < writingDifficultyThreshold:
          continue

        if regex.pattern in internetPatternsDict:
          libLF.log('realPattern /{}/ matches internet source'.format(regex.pattern))
          nRegexesMatchingInternetRegex += 1
        else:
          libLF.log('realPattern /{}/ does not match internet source'.format(obj['pattern']))
      except:
        pass

    libLF.log('{} regexes matched internet sources'.format(nRegexesMatchingInternetRegex))

###############################################

# Parse args
parser = argparse.ArgumentParser(description='Determine whether regex patterns from source code match an Internet source')
parser.add_argument('--internet-patterns', '-i', help='Path to Internet regexes file', required=True)
parser.add_argument('--real-patterns', '-r', help='Path to file of libLF.Regex objects', required=True)
parser.add_argument('--writing-difficulty-threshold', '-d', help='Only consider patterns >= this writing difficulty. Below this we consider independent derivation possible', type=int, default=0, required=False)

args = parser.parse_args()

assert(0 <= args.writing_difficulty_threshold)

# Here we go!
main(args.internet_patterns, args.real_patterns, args.writing_difficulty_threshold)
