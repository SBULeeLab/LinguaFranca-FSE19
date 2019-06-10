#!/usr/bin/env python3
# Description:
#   Convert a set of libLF.ModuleInfo's to libLF.GitHubProject's.
#   Use defaults.

# Import libLF
import os
import sys
import re
sys.path.append('{}/lib'.format(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT']))
import libLF

import argparse
import json

#################################################

def main(moduleInfoFile, outFile):
  nAttempts = 0
  nSuccesses = 0
  nFailures = 0
  with open(moduleInfoFile, 'r') as inStream, \
       open(outFile, 'w') as outStream:
    for line in inStream:
      try:
        line = line.strip()
        if len(line) > 0:
          nAttempts += 1
          mi = libLF.ModuleInfo().initFromJSON(line)
          ghp = libLF.GitHubProject().initFromRaw(
            owner='UNKNOWN',
            name='UNKNOWN',
            registry=mi.registry,
            modules=[mi.toNDJSON()],
            tarballPath=mi.tarballPath
          )
          outStream.write(ghp.toNDJSON() + '\n')
          nSuccesses += 1
      except:
        libLF.log('Discarding: {}'.format(line))
        nFailures += 1
  libLF.log('Out of {} ModuleInfo\'s: {} successful conversions, {} failures'.format(nAttempts, nSuccesses, nFailures))

###############################################

# Parse args
parser = argparse.ArgumentParser(description='Convert ModuleInfo to GitHubProject')
parser.add_argument('--module-info-file', help='in: NDJSON of ModuleInfo\'s', required=True, dest='moduleInfoFile')
parser.add_argument('--out-file', help='out: NDJSON of GitHubProject\'s', required=True, dest='outFile')
args = parser.parse_args()

# Here we go!
main(args.moduleInfoFile, args.outFile)
