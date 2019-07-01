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

VERBOSE = False

# input: readable file stream
# output: dictionary mapping key 'pattern' to a list of the InternetRegexSources that define this pattern
def getInternetPatternsDict(internetPatternsStream):
  internetPatterns = {}

  internetPatternsStream.seek(0)
  for line in internetPatternsStream:
    # Skip blank lines
    if re.match('^\s*$', line):
      continue

    source = libLF.InternetRegexSource.factory(line)

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

    nRegexes = 0
    nRealRegexesAtLeastXDifficult = 0
    for line in realPatternsStream:
      # Skip blank lines
      if re.match(r'^\s*$', line):
        continue

      try:
        regex = libLF.Regex().initFromNDJSON(line)
        nRegexes += 1

        # Discard patterns that could be independently derived.
        if libLF.scorePatternWritingDifficulty(regex.pattern) < writingDifficultyThreshold:
          continue
        nRealRegexesAtLeastXDifficult += 1

        if regex.pattern in internetPatternsDict:
          libLF.log('realPattern /{}/ matches internet source'.format(regex.pattern))
          nRegexesMatchingInternetRegex += 1
        else:
          if VERBOSE:
            libLF.log('realPattern /{}/ does not match internet source'.format(regex.pattern))
      except Exception as e:
        libLF.log("Exception?: {}".format(e))
        pass

    nInternetRegexesAtLeastXDifficult = 0
    for pat in internetPatternsDict:
      if libLF.scorePatternWritingDifficulty(pat) < writingDifficultyThreshold:
        continue
      nInternetRegexesAtLeastXDifficult += 1

    # Print summary
    print('{}/{} real regexes matched any of the {} internet regexes (among the {} real regexes and {} internet regexes at least {} difficult)'.format(nRegexesMatchingInternetRegex, nRegexes, len(internetPatternsDict), nRealRegexesAtLeastXDifficult, nInternetRegexesAtLeastXDifficult, writingDifficultyThreshold))

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
