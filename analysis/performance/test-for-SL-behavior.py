#!/usr/bin/env python3
# Test libLF.Regex's for SL behavior using the vuln-regex-detector suite.
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
  'godoc': 'Go'
}

def allSLTestLanguages():
  return reg2lang.values()

def remainingTestLanguages(langsAlready):
  return [lang for lang in allSLTestLanguages() if lang not in langsAlready]

def registryToSLTestLanguage(registry):
  return reg2lang[registry]

##########

class MyTask(libLF.parallel.ParallelTask):
  def __init__(self, regex, slTimeout, powerPumps):
    self.regex = regex
    self.slTimeout = slTimeout
    self.powerPumps = powerPumps
    self.slra = None
  
  def run(self):
    try:
      libLF.log('Working on regex: /{}/'.format(self.regex.pattern))
      # Run the analysis
      self.slra = self._testRegexForSLBehavior(self.regex)
      # Return
      libLF.log('Completed regex /{}/'.format(self.regex.pattern))
      return self.slra
    except KeyboardInterrupt:
      raise
    except BaseException as err:
      libLF.log('Exception while testing regex /{}/: '.format(self.regex.pattern) + err)
      return err

  def _testRegexForSLBehavior(self, regex):
    """Returns SLRegexAnalysis or raises an exception
    
    With lang_pump2timedOut populated for the language(s) this regex
    occurs in.
    """
    try:
      libLF.log('Testing regex: <{}>'.format(regex.pattern))
      slra = libLF.SLRegexAnalysis(regex, self.slTimeout, self.powerPumps)

      ## Query detectors
      slra.queryDetectors()

      ## Check its behavior in all available languages
      # (Not just the ones it appears in)
      # We can identify the "real" vs. "what-if" by looking at the slra.regex object.
      for lang in allSLTestLanguages():
        libLF.log('Validating detector opinions in {}'.format(lang))
        slra.validateDetectorOpinionsInLang(lang)
      return slra
    except BaseException as err:
      libLF.log('Exception while analyzing: err <{}> libLF.Regex {}'.format(err, regex.toNDJSON()))
      raise

################

def getTasks(regexFile, slTimeout, powerPumps):
  regexes = loadRegexFile(regexFile)
  tasks = [MyTask(regex, slTimeout, powerPumps) for regex in regexes]
  libLF.log('Prepared {} tasks'.format(len(tasks)))
  return tasks

def loadRegexFile(regexFile):
  """Return a list of Regex's"""
  regexes = []
  libLF.log('Loading regexes from {}'.format(regexFile))
  with open(regexFile, 'r') as inStream:
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

def main(regexFile, outFile, slTimeout, powerPumps, parallelism):
  libLF.log('regexFile {} outFile {} slTimeout {} powerPumps {} parallelism {}' \
    .format(regexFile, outFile, slTimeout, powerPumps, parallelism))
  #### Load data
  tasks = getTasks(regexFile, slTimeout, powerPumps)
  nRegexes = len(tasks)

  #### Process data

  # CPU-bound, no limits
  libLF.log('Submitting to map')
  results = libLF.parallel.map(tasks, parallelism,
    libLF.parallel.RateLimitEnums.NO_RATE_LIMIT, libLF.parallel.RateLimitEnums.NO_RATE_LIMIT,
    jitter=False)

  
  #### Emit results

  libLF.log('Writing results to {}'.format(outFile))
  nSuccesses = 0
  nExceptions = 0
  with open(outFile, 'w') as outStream:
    for slra in results:
        # Emit
        if type(slra) is libLF.SLRegexAnalysis:
          nSuccesses += 1
          outStream.write(slra.toNDJSON() + '\n')
        else:
          nExceptions += 1
  libLF.log('Successfully performed SLRegexAnalysis on {} regexes, {} exceptions'.format(nSuccesses, nExceptions))

  #### Analyze the successful SLRegexAnalysis's

  slras = [
    res
    for res in results
    if type(res) is libLF.SLRegexAnalysis
  ]

  # How many regexes exhibited SL behavior in any language?
  # TODO Must confirm whether this is testing full-match or partial-match semantics consistently,
  # or favor the most conservative behavior possible, or try both.
  slras_timedOut = list(
    filter(lambda slra: slra.everTimedOut(), slras)
  )
  libLF.log('{} of {} successful analyses timed out in some language'.format(len(slras_timedOut), len(slras)))

  # Did we find any differences in SL regex behavior across languages?
  # The answer to this is presumably always "yes" since we are including linear-time engines.
  slras_diffBehav = []
  for slra in slras:
    behaviors = set()
    for lang in allSLTestLanguages():
      behaviors.add(slra.predictedPerformanceInLang(lang))
    if len(behaviors) > 1:
      slras_diffBehav.append(slra)
  libLF.log('{} of the regexes had different performance in different languages'.format(len(slras_diffBehav)))

  # Did we find any differences in SL regex behavior across languages *for those they appeared in*?
  # This may be a more interesting metric.
  slras_diffBehav_real = []
  for slra in slras:
    behaviors = set()
    for registry in slra.regex.registriesUsedIn():
      lang = registryToSLTestLanguage(registry)
      behaviors.add(slra.predictedPerformanceInLang(lang))
    if len(behaviors) > 1:
      slras_diffBehav_real.append(slra)
  libLF.log('{} of the regexes had different performance in the languages they actually appeared in'.format(len(slras_diffBehav_real)))

#####################################################

# Parse args
parser = argparse.ArgumentParser(description='Test a set of libLF.Regex\'s for SL behavior. Regexes are tested in every supported language.')
parser.add_argument('--regex-file', type=str, help='In: File of libLF.Regex objects', required=True,
  dest='regexFile')
parser.add_argument('--out-file', type=str, help='Out: File of libLF.SLRegexAnalysis objects', required=True,
  dest='outFile')
parser.add_argument('--sl-timeout', type=int, help='Threshold used to determine super-linearity', required=False, default=5,
  dest='slTimeout')
parser.add_argument('--power-pumps', type=int, help='Number of pumps to trigger power-law SL behavior (e.g. quadratic)', required=False, default=500000,
  dest='powerPumps')
parser.add_argument('--parallelism', type=int, help='Maximum cores to use', required=False, default=libLF.parallel.CPUCount.CPU_BOUND,
  dest='parallelism')
args = parser.parse_args()

# Here we go!
main(args.regexFile, args.outFile, args.slTimeout, args.powerPumps, args.parallelism)
