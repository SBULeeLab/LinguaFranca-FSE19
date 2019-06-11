#!/usr/bin/env python3
# Given an extracted list of regexes, reduce to unique regexes
# This is like analyze-regex-duplication but simpler, more friendly to manual analysis

# Import libLF
import os
import sys
import re
sys.path.append('{}/lib'.format(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT']))
import libLF
import argparse
import tarfile
import re
import subprocess
import shutil
import pprint

def loadRegexUsages(regexUsageFile):
  """Returns libLF.RegexUsage[]"""
  ret = []
  libLF.log('Loading RegexUsage\'s from {}'.format(regexUsageFile))
  with open(regexUsageFile, 'r') as inStream:
    for line in inStream:
      line = line.strip()
      if len(line) == 0:
        continue
      
      try:
        # Build the Regex
        ru = libLF.RegexUsage()
        ru.initFromNDJSON(line)

        ret.append(ru)
      except KeyboardInterrupt:
        raise
      except BaseException as err:
        libLF.log('Exception parsing line:\n  {}\n  {}'.format(line, err))

    libLF.log('Loaded {} RegexUsage\'s'.format(len(ret)))
    return ret

def main(regexFiles, outFile):
    # Load
    nRegexUsages = 0
    file2regexUsages = {}
    for f in regexFiles:
        file2regexUsages[f] = loadRegexUsages(f)
        nRegexUsages += len(file2regexUsages[f])
    libLF.log('Loaded {} regexUsage\'s from {} files'.format(nRegexUsages, len(regexFiles)))
    
    # Identify unique regexes in each file.
    nPerFileUniquePatterns = 0
    file2patterns = {}
    for f in file2regexUsages:
        file2patterns[f] = set([ru.pattern for ru in file2regexUsages[f]])
        file2patterns[f].discard('DYNAMIC')
        nPerFileUniquePatterns += len(file2patterns[f])
        libLF.log('{} unique patterns in {}:\n{}' \
            .format(len(file2patterns[f]), f, pprint.pformat(sorted(file2patterns[f]))))
    libLF.log('Counting unique regexes per file, got {} unique regexes'.format(nPerFileUniquePatterns))
    
    # Identify global unique regexes.
    uniqPatterns = set()
    for f in file2patterns:
        uniqPatterns |= file2patterns[f]
    libLF.log('Globally, got {} unique regexes'.format(len(uniqPatterns)))
    
    # Did we find any intersections among files? Pigeonhole principle.
    if len(uniqPatterns) < nPerFileUniquePatterns:
        perFileUniquePatterns = [p for perFilePatterns in file2patterns.values() for p in perFilePatterns]
        duplicates = set([p for p in perFileUniquePatterns if perFileUniquePatterns.count(p) > 1])
        libLF.log('{} regexes appeared in multiple files: {}'.format(len(duplicates), duplicates))
    else:
        libLF.log('Each unique regex appeared in only 1 file'.format(nPerFileUniquePatterns - len(uniqPatterns)))

    # Emit
    regexes = [libLF.Regex().initFromRaw(p, {}, {}) for p in uniqPatterns]
    libLF.log('Emitting to {}'.format(outFile))
    with open(outFile, 'w') as outStream:
        for regex in regexes:
            outStream.write(regex.toNDJSON() + '\n')

###############################################

# Parse args
parser = argparse.ArgumentParser(description='Reduce libLF.RegexUsage\'s to a unique set of libLF.Regex\'s (with empty registry fields)')
parser.add_argument('--regex-usage-files', '-f', nargs='+', type=str, help='Files: libLF.RegexUsage\'s as produced by regex-extractor', required=True,
    dest='regexUsageFiles')
parser.add_argument('--out-file', '-o', help='Where to write Regex objects as NDJSON?', required=True,
    dest='outFile')

args = parser.parse_args()

# Here we go!
main(args.regexUsageFiles, args.outFile)
