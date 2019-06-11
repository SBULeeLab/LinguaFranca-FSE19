#!/usr/bin/env python3
# Analyze the results of testing a bunch of libLF.Regex's for syntax support.

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

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd

# Make sure plot labels are readable 
font = {'family' : 'normal',
      'weight' : 'normal',
      'size'   : 14}
matplotlib.rc('font', **font)

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

def allRegistries():
  return reg2lang.keys()

def allSLTestLanguages():
  return reg2lang.values()

def remainingTestLanguages(langsAlready):
  return [lang for lang in allSLTestLanguages() if lang not in langsAlready]

def registryToSLTestLanguage(registry):
  return reg2lang[registry]

def languageToRegistry(language):
  # Well this is ugly, but it's a small dictionary.
  for reg in reg2lang:
    if reg2lang[reg].lower() == language.lower():
      return reg
  raise ValueError('Could not find registry for {}'.format(language))

################

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

class SupportSet:
  def __init__(self, name, langs):
    self.name = name
    self.langs = langs
    self.count = 0
  
def makeReport_syntaxSupportSummary(regexes, visDir):
  libLF.log('\n\n--------------------------------')
  libLF.log('    Report: syntax support summary')
  libLF.log('--------------------------------\n\n')
  lang2SupportCounts = {}
  nSuppLangs2Counts = {}

  allLangs = set([l.lower() for l in reg2lang.values()]) # all

  allButRust = allLangs.copy()
  for lang in ['rust']:
    allButRust.remove(lang)

  allButRustAndGo = allLangs.copy()
  for lang in ['rust', 'go']:
    allButRustAndGo.remove(lang)

  allButRustAndJava = allLangs.copy()
  for lang in ['rust', 'java']:
    allButRustAndJava.remove(lang)

  allButRustAndRuby = allLangs.copy()
  for lang in ['rust', 'ruby']:
    allButRustAndRuby.remove(lang)

  allButRRJ = allLangs.copy()
  for lang in ['rust', 'ruby', 'java']:
    allButRRJ.remove(lang)

  langSuppSets = [
    SupportSet('All languages', allLangs),
    SupportSet('All languages but {{rust}}', allButRust),
    SupportSet('All languages but {{rust, go}}', allButRustAndGo),
    SupportSet('All languages but {{rust, java}}', allButRustAndJava),
    SupportSet('All languages but {{rust, ruby}}', allButRustAndRuby),
    SupportSet('All languages but {{rust, ruby, java}}', allButRRJ),
  ]

  # Calculate counts
  for regex in regexes:
    # Per-lang info
    for lang in regex.supportedLangs:
      if lang not in lang2SupportCounts:
        lang2SupportCounts[lang] = 0
      lang2SupportCounts[lang] += 1

    nLangs = len(regex.supportedLangs) 
    if nLangs not in nSuppLangs2Counts:
      nSuppLangs2Counts[nLangs] = 0
    nSuppLangs2Counts[nLangs] += 1

    if nLangs == 0:
      # Surprising outlier
      libLF.log('Regex /{}/ was supported in 0 langs? (registries {})' \
        .format(regex.pattern, regex.registriesUsedIn()))

    # Support sets
    for suppSet in langSuppSets:
      if suppSet.langs.issubset(set(regex.supportedLangs)):
        suppSet.count += 1
  
  libLF.log('\n\n')
  tableFormat = '%40s %30s %40s'
  libLF.log(tableFormat % ('Language', 'Number of supported regexes', 'Fraction of all regexes'))
  libLF.log(tableFormat % ('------------------------', '-----------------------------', '-------------------------'))
  for lang in lang2SupportCounts:
    fracStr = '%.2f' % (lang2SupportCounts[lang] / len(regexes))
    libLF.log(tableFormat % (lang, lang2SupportCounts[lang], fracStr))

  libLF.log('\n\n')
  tableFormat = '%40s %30s %40s'
  libLF.log(tableFormat % ('Number of supporting languages', 'Number of regexes', 'Fraction of all regexes'))
  libLF.log(tableFormat % ('-------------', '------------------------', '-------------------------'))
  for count in sorted(nSuppLangs2Counts.keys()):
    fracStr = '%.2f' % (nSuppLangs2Counts[count] / len(regexes))
    libLF.log(tableFormat % (count, nSuppLangs2Counts[count], fracStr))

  libLF.log('\n\n')
  tableFormat = '%40s %30s %25s'
  libLF.log(tableFormat % ('Language set', 'Number of supported regexes', 'Fraction of all regexes'))
  libLF.log(tableFormat % ('-------------------------', '---------------------------', '-----------------------'))
  for suppSet in langSuppSets:
    fracStr = '%.2f' % (suppSet.count / len(regexes))
    libLF.log(tableFormat % (suppSet.name, suppSet.count, fracStr))

def makeReport_regexesNotSupportedInSourceRegistries(regexes, visDir):
  libLF.log('\n\n--------------------------------')
  libLF.log('    Report: Regexes not supported in languages they appeared in')
  libLF.log('        (i.e. extraction/evaluation issues)')
  libLF.log('--------------------------------\n\n')

  #### Sanity check: Every regex works in the registry in which it was found
  problematicRegexes = []
  lang2shouldBeSupported = {} # Total # regexes found in this lang
  lang2nUnsupported = {} # Total # of those regexes that were not supported
  libLF.log('\n\n-----------------------')
  libLF.log('Confirming that every regex works in the registry in which it was found')
  for regex in regexes:
    # Check this regex
    #libLF.log('  Checking that /{}/ works in the languages for registries {} (it worked in {})' \
    #  .format(regex.pattern, regex.registriesUsedIn(), regex.supportedLangs))
    isProblem = False
    for registry in regex.registriesUsedIn():
      lang = reg2lang[registry]
      # lang2shouldBeSupported 
      if lang not in lang2shouldBeSupported:
        lang2shouldBeSupported[lang] = 0
      lang2shouldBeSupported[lang] += 1
      if lang.lower() not in [l.lower() for l in regex.supportedLangs]:
        # Surprise! Why wasn't it supported?
        libLF.log('    Warning: regex /{}/ not supported in {} but it was found in {}' \
          .format(regex.pattern, lang, regex.registriesUsedIn()))
        isProblem = True
        # lang2nUnsupported
        if lang not in lang2nUnsupported:
          lang2nUnsupported[lang] = 0
        lang2nUnsupported[lang] += 1
    if isProblem:
      problematicRegexes.append(regex)

  if len(problematicRegexes):
    libLF.log('----------------------------------------------')
    libLF.log('')
    libLF.log('Warning: {} ({:.02f}%) regexes did not work in at least one of the registries in which they were found' \
      .format(len(problematicRegexes), 100 * (len(problematicRegexes)/len(regexes))))
    libLF.log('')
    tableFormat = '%30s %40s %40s'
    libLF.log(tableFormat % ('Language', 'Number of regexes unsupported', 'Perc of regexes from that lang'))
    libLF.log(tableFormat % ('-------------------', '------------------------------', '-------------------------'))
    for lang in lang2nUnsupported:
      libLF.log(tableFormat % (lang, lang2nUnsupported[lang], '%.2f' % (lang2nUnsupported[lang] / lang2shouldBeSupported[lang])))
  else:
    libLF.log('Good, all regexes worked in the registries in which they were found')

################

def main(regexFile, visDir):
  libLF.log('regexFile {} visDir {}' \
    .format(regexFile, visDir))

  #### Load data
  regexes = loadRegexFile(regexFile)

  #### Generate reports
  makeReport_regexesNotSupportedInSourceRegistries(regexes, visDir)
  makeReport_syntaxSupportSummary(regexes, visDir)

#####################################################

# Parse args
parser = argparse.ArgumentParser(description='Analyze the results of testing libLF.Regex\'s for syntax support')
parser.add_argument('--regex-file', type=str, help='In: File of libLF.Regex objects', required=True,
  dest='regexFile')
parser.add_argument('--vis-dir', help='Out: Where to save plots?', required=False, default='/tmp/vis',
  dest='visDir')
# TODO: Emit some sub-list?
args = parser.parse_args()

# Here we go!
main(args.regexFile, args.visDir)
