#!/usr/bin/env python3
# Given a regex, check which languages it can be instantiated in.
# This analysis can run single-node many-core.

# Import libLF
import os
import sys
import re
sys.path.append(os.path.join(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT'], 'lib'))
import libLF

import json
import tempfile
import argparse
import traceback

##########

reg2lang = {
  'npm': 'JavaScript', # TypeScript is evaluated on a JS engine
  'crates.io': 'Rust',
  'packagist': 'PHP',
  'pypi': 'Python',
  'rubygems': 'Ruby',
  'cpan': 'Perl',
  'maven': 'Java',
  'godoc': 'Go',
}

##########

class MyTask(libLF.parallel.ParallelTask):
  def __init__(self, regex):
    self.regex = regex
  
  def run(self):
    try:
      libLF.log('Working on regex: /{}/'.format(self.regex.pattern))
      # Run the analysis
      for lang in reg2lang.values():
        self.regex.isSupportedInLanguage(lang.lower())
      # Return
      libLF.log('Completed regex')
      return self.regex
    except KeyboardInterrupt:
      raise
    except BaseException as err:
      libLF.log('Error handling regex /{}/: {}'.format(self.regex.pattern, err))
      return err

################

def getTasks(regexFile):
  regexes = loadRegexFile(regexFile)
  tasks = [MyTask(regex) for regex in regexes]
  libLF.log('Prepared {} tasks'.format(len(tasks)))
  return tasks

def loadRegexFile(regexFile):
  """Return a list of Regex's"""
  regexes = []
  libLF.log('Loading regexes from {}'.format(regexFile))
  with open(regexFile, 'r', encoding='utf-8') as inStream:
    for line in inStream:
      line = line.strip()
      if len(line) == 0:
        continue
      
      try:
        # Build a Regex
        regex = libLF.Regex()
        regex.initFromNDJSON(line)

        regexes.append(regex)
      except KeyboardInterrupt:
        raise
      except BaseException as err:
        libLF.log('Exception parsing line:\n  {}\n  {}'.format(line, err))
        traceback.print_exc()

    libLF.log('Loaded {} regexes from {}'.format(len(regexes), regexFile))
    return regexes

################

def main(regexFile, outFile, parallelism):
  libLF.log('regexFile {} outFile {} parallelism {}' \
    .format(regexFile, outFile, parallelism))

  #### Load data
  libLF.log('\n\n-----------------------')
  libLF.log('Loading regexes from {}'.format(regexFile))

  tasks = getTasks(regexFile)
  nRegexes = len(tasks)

  #### Process data
  libLF.log('\n\n-----------------------')
  libLF.log('Computing syntax support in {}'.format(reg2lang.values()))

  # CPU-bound, no limits
  libLF.log('Submitting to map')
  results = libLF.parallel.map(tasks, parallelism,
    libLF.parallel.RateLimitEnums.NO_RATE_LIMIT, libLF.parallel.RateLimitEnums.NO_RATE_LIMIT,
    jitter=False)

  #### Emit results

  libLF.log('\n\n-----------------------')
  libLF.log('Writing results to {}'.format(outFile))
  nSuccesses = 0
  nExceptions = 0
  with open(outFile, 'w') as outStream:
    for regex in results:
        # Emit
        if type(regex) is libLF.Regex:
          nSuccesses += 1
          outStream.write(regex.toNDJSON() + '\n')
        else:
          nExceptions += 1
  libLF.log('Successfully performed language compatibility testing on {} regexes, {} exceptions'.format(nSuccesses, nExceptions))

  #### Analyze the successful Regex's for a quick summary

  libLF.log('\n\n-----------------------')
  libLF.log('Generating a quick summary of regex syntax support')
  regexes = [
    res
    for res in results
    if type(res) is libLF.Regex
  ]

  lang2SupportCounts = {}
  nSuppLangs2Counts = {}
  
  for regex in regexes:
    for lang in regex.supportedLangs:
      if lang not in lang2SupportCounts:
        lang2SupportCounts[lang] = 0
      lang2SupportCounts[lang] += 1

    nLangs = len(regex.supportedLangs) 
    if nLangs not in nSuppLangs2Counts:
      nSuppLangs2Counts[nLangs] = 0
    nSuppLangs2Counts[nLangs] += 1

    if nLangs == 0:
      libLF.log('Regex /{}/ was supported in 0 langs? (registries {})' \
        .format(regex.pattern, regex.registriesUsedIn()))
  
  tableFormat = '%30s %20s'
  libLF.log(tableFormat % ('Number of supporting languages', 'Number of regexes'))
  for count in sorted(nSuppLangs2Counts.keys()):
    libLF.log(tableFormat % (count, nSuppLangs2Counts[count]))

  libLF.log('\n\n')
  tableFormat = '%15s %20s'
  libLF.log(tableFormat % ('Language', 'Number of supported regexes'))
  for lang in lang2SupportCounts:
    libLF.log(tableFormat % (lang, lang2SupportCounts[lang]))

  #### Sanity check: Every regex works in the registry in which it was found
  
  problematicRegexes = []
  libLF.log('\n\n-----------------------')
  libLF.log('Confirming that every regex works in the registry in which it was found')
  for regex in regexes:
    # Check this regex
    #libLF.log('  Checking that /{}/ works in the languages for registries {} (it worked in {})' \
    #  .format(regex.pattern, regex.registriesUsedIn(), regex.supportedLangs))
    isProblem = False
    for registry in regex.registriesUsedIn():
      if reg2lang[registry].lower() not in [l.lower() for l in regex.supportedLangs]:
        # Surprise! Why wasn't it supported?
        libLF.log('    Warning: regex /{}/ not supported in {} but it was found in {}' \
          .format(regex.pattern, reg2lang[registry], regex.registriesUsedIn()))
        isProblem = True
    if isProblem:
      problematicRegexes.append(regex)

  if len(problematicRegexes):
    libLF.log('Uh oh, {} regexes did not work in at least one of the registries in which they were found' \
      .format(len(problematicRegexes)))
  else:
    libLF.log('Good, all regexes worked in the registries in which they were found')

#####################################################

# Parse args
parser = argparse.ArgumentParser(description='Test a set of libLF.Regex\'s for the languages in which they are supported')
parser.add_argument('--regex-file', type=str, help='In: File of libLF.Regex objects', required=True,
  dest='regexFile')
parser.add_argument('--out-file', type=str, help='Out: File of libLF.Regex objects', required=True,
  dest='outFile')
parser.add_argument('--parallelism', type=int, help='Maximum cores to use', required=False, default=libLF.parallel.CPUCount.CPU_BOUND,
  dest='parallelism')
args = parser.parse_args()

# Here we go!
main(args.regexFile, args.outFile, args.parallelism)
