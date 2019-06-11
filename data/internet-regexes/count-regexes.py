#!/usr/bin/env python3
# Description:
#   Count total and unique regexes in internetSources-X.json files.   

# Import our lib
import os
import sys
sys.path.append('{}/lib'.format(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT']))
import libLF

import json
import argparse
import re

def main(regexFile):
  libLF.log('Counting regexes in {}'.format(regexFile))

  totalSources = 0
  totalPatterns = 0
  uniquePatterns = set()
  with open(regexFile, 'r') as inStream:
    for line in inStream:
      if len(line) is 0:
        continue
      totalSources = totalSources + 1
      internetRegexSource = libLF.InternetRegexSource.factory(line)

      totalPatterns = totalPatterns + len(internetRegexSource.patterns)

      for pattern in internetRegexSource.patterns:
        uniquePatterns.add(pattern)

    libLF.log('Found {} total regexes in {} InternetSources. Found {} unique regexes.'.format(totalPatterns, totalSources, len(uniquePatterns)))

###############################################

# Parse args
parser = argparse.ArgumentParser(description='Count the total and unique regexes from an internetsources-X.json file')
parser.add_argument('--regex-file', '-f', help='Path to internetSources-X.json file', required=True)

args = parser.parse_args()

# Here we go!
main(args.regex_file)
