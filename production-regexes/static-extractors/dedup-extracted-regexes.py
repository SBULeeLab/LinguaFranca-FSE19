#!/usr/bin/env python3
# Analyze regex duplication.
# Input: GHPs post-extraction, and InternetSource's
# Output: Graphs and files of the unique Regex's

# Import libLF
import os
import sys
import re
sys.path.append('{}/lib'.format(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT']))
import libLF
import argparse
import statistics
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import math

import itertools

############

matplotlib.rcParams.update({
  'axes.labelsize': 'x-large',
  'axes.titlesize': 'xx-large',
  'xtick.labelsize': 'x-large',
  'ytick.labelsize': 'x-large',
  'font.family': 'normal',
  'legend.fontsize': 'x-large',
})

############

DUP_LENGTH_LIMITS = [0, 5, 10, 15, 20]
OFFICIAL_DUP_LENGTH_LIMIT = 15

############

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

def getGHPs(ghpFile, curPrefix=None, newPrefix=None):
  """Return a list of GHPs, optionally with regexPath prefixes changed."""
  ghps = []
  with open(ghpFile, 'r') as inStream:
    for line in inStream:
      line = line.strip()
      if len(line) == 0:
        continue
      
      try:
        # Build a GitHubProject
        ghp = libLF.GitHubProject()
        ghp.initFromJSON(line)

        # regexPath, dynRegexPath prefix massaging
        if curPrefix is not None and newPrefix is not None:
          curPath = ghp.regexPath
          newPath = newPrefix + curPath[len(curPrefix):]
          ghp.regexPath = newPath

          curPath = ghp.dynRegexPath
          newPath = newPrefix + curPath[len(curPrefix):]
          ghp.dynRegexPath = newPath

        ghps.append(ghp)
      except KeyboardInterrupt:
        raise
      except BaseException as err:
        libLF.log('Exception parsing line:\n  {}\n  {}'.format(line, err))

    libLF.log('Loaded {} ghps from {}'.format(len(ghps), ghpFile))
    return ghps

def getInternetSourceList(internetSourceFile):
  """Return a list of InternetSource's"""
  isl = []
  with open(internetSourceFile, 'r') as inStream:
    for line in inStream:
      line = line.strip()
      if len(line) == 0:
        continue
      
      try:
        internetSource = libLF.InternetRegexSource()
        internetSource.initFromNDJSON(line)
        isl.append(internetSource)
      except KeyboardInterrupt:
        raise
      except BaseException as err:
        libLF.log('Exception parsing line:\n  {}\n  {}'.format(line, err))

    libLF.log('Loaded {} InternetSource\'s from {}'.format(len(isl), internetSourceFile))
    return isl

def processOneGitHubProject(i, regexTypes, skipStatic, skipDynamic, ghp, # inputs
  pattern2Regex, registry2nRegexUsages, registry2nUniqueRegexes,
  registry2nModules, registry2nModulesWithRegexes, pattern_to_reg2modules # outputs
  ):
    """Update pattern2Regex based on the regexes in this GHP."""
    projectName = ghp.owner + '/' + ghp.name

    # Count this module
    if ghp.registry not in registry2nModules:
      registry2nModules[ghp.registry] = 0
    registry2nModules[ghp.registry] += 1

    for regexType in regexTypes:
      if regexType == libLF.Regex.USE_TYPE_STATIC and skipStatic:
        libLF.log("Skipping static regexes from {}".format(projectName))
        continue
      elif regexType == libLF.Regex.USE_TYPE_DYNAMIC and skipDynamic:
        libLF.log("Skipping dynamic regexes from {}".format(projectName))
        continue
      projectContainedRegexesOfThisType = False

      if regexType == libLF.Regex.USE_TYPE_STATIC:
        regexFile = ghp.regexPath
      elif regexType == libLF.Regex.USE_TYPE_DYNAMIC:
        regexFile = ghp.dynRegexPath
      else:
        raise ValueError("Error, unexpected regexType {}".format(regexType))
      libLF.log("{}: {} regexes are in {}".format(projectName, regexType, regexFile))

      if not regexFile or len(regexFile) == 0 or not regexFile.endswith(".json"):
        libLF.log("No {} regex file for {} (perhaps that form of extraction failed)".format(regexType, projectName))
        return
      if not os.path.isfile(regexFile):
        libLF.log("No such file <{}> for {} regexes from {} (path error?)".format(regexFile, regexType, projectName))
        return

      # Handle the regexes of this type
      regexUsages = loadRegexUsages(regexFile)

      filteredRU = [
        ru
        for ru in regexUsages
        # Non-string regex are bugs in the extractor
        if type(ru.pattern) is str
      ]
      nRegexUsagesInThisGHP = len(filteredRU)

      # Identify the unique patterns in this regexFile
      # and update the appropriate data structures
      uniquePatternsInThisGHP = set()
      for regexUsage in filteredRU:
        # 'DYNAMIC'/'DYNAMIC-PATTERN' don't count as unique regexes
        if regexType == libLF.Regex.USE_TYPE_STATIC and (regexUsage.pattern == "DYNAMIC" or regexUsage.pattern == "DYNAMIC-PATTERN"):
          continue

        projectContainedRegexesOfThisType = True

        # Count regexes at most once per project
        if regexUsage.pattern in uniquePatternsInThisGHP:
          continue

        # First time we've seen this pattern in this project
        if regexUsage.pattern not in pattern2Regex:
          # First time we've seen it anywhere
          regex = libLF.Regex()
          regex.initFromRaw(regexUsage.pattern, {}, {})
          pattern2Regex[regexUsage.pattern] = regex
        # Mark this pattern as used in a module in this registry 
        pattern2Regex[regexUsage.pattern].usedInRegistry(ghp.registry, regexType)
        uniquePatternsInThisGHP.add(regexUsage.pattern)

        # Add this registry/module to the list of modules that used this regex
        if regexUsage.pattern not in pattern_to_reg2modules:
          pattern_to_reg2modules[regexUsage.pattern] = {}
        if ghp.registry not in pattern_to_reg2modules[regexUsage.pattern]:
          pattern_to_reg2modules[regexUsage.pattern][ghp.registry] = {
            libLF.Regex.USE_TYPE_STATIC: set(),
            libLF.Regex.USE_TYPE_DYNAMIC: set(),
          }
        
        if ghp.registry != "cpan":
          moduleName = "{}/{}".format(ghp.owner, ghp.name)
        else:
          moduleName = "cpan-{}".format(i) # No GitHub owner/name for CPAN, just use a unique ID
        pattern_to_reg2modules[regexUsage.pattern][ghp.registry][regexType].add(moduleName)

      # Update tracker of frequency of regex usages of this type
      libLF.log('{} {} regex usages in {}:{}'.format(nRegexUsagesInThisGHP, regexType, ghp.registry, projectName))
      if ghp.registry not in registry2nRegexUsages:
        registry2nRegexUsages[ghp.registry] = {
          libLF.Regex.USE_TYPE_STATIC: [],
          libLF.Regex.USE_TYPE_DYNAMIC: [],
        }
      registry2nRegexUsages[ghp.registry][regexType].append(nRegexUsagesInThisGHP)

      # Update tracker of frequency of unique regex usages of this type
      libLF.log('{} unique {} patterns in {}:{}'.format(len(uniquePatternsInThisGHP), regexType, ghp.registry, projectName))
      if ghp.registry not in registry2nUniqueRegexes:
        registry2nUniqueRegexes[ghp.registry] = {
          libLF.Regex.USE_TYPE_STATIC: [],
          libLF.Regex.USE_TYPE_DYNAMIC: [],
        }
      registry2nUniqueRegexes[ghp.registry][regexType].append(len(uniquePatternsInThisGHP))

      # Update tracker of number of modules with regexes of this type
      if ghp.registry not in registry2nModulesWithRegexes:
        registry2nModulesWithRegexes[ghp.registry] = {
          libLF.Regex.USE_TYPE_STATIC: 0,
          libLF.Regex.USE_TYPE_DYNAMIC: 0,
        }
      if projectContainedRegexesOfThisType:
        registry2nModulesWithRegexes[ghp.registry][regexType] += 1

def processOneInternetSource(internetSource, pattern2Regex):
  """Update pattern2Regex based on the regexes in this InternetSource.
  
  This must be called after processing the GHPs.
  Since there are non-regex code snippets in the InternetSource's,
  we only trust entities that we find in the GHPs to be regexes."""
  nRegexesSeen = 0

  # Check each unique pattern in internetSource
  for uniqPattern in set(internetSource.patterns):
    # Is this a "wild" regex? (appears in a GHP)
    if uniqPattern in pattern2Regex:
        pattern2Regex[uniqPattern].usedInInternetSource(internetSource.type)
        nRegexesSeen += 1
  libLF.log('{} GHP regexes found in a {} post'.format(nRegexesSeen, internetSource.type))


def visualizeBar(tuples, title, xlabel, ylabel, outFile, logAxis=None, rotate=None):
  fig, ax = plt.subplots()
  
  if(rotate is not None and rotate == True):
    plt.xticks(rotation=30)
  xlabels = [degree for degree, count in tuples]
  data = [count for degree, count in tuples]

  ax.bar(xlabels, data, align='center', alpha=0.5)

  ax.set_xticks(np.arange(len(xlabels)), xlabels)
  ax.set_ylabel(ylabel)
  ax.set_xlabel(xlabel)
  ax.set_title(title) 
  if(logAxis is not None and logAxis == True):
    ax.set_yscale('log')

  plt.tight_layout()
  plt.savefig(outFile, bbox_inches='tight', pad_inches=0)
  libLF.log('Saved plot to {}'.format(outFile))

def visualizeUniqueRegexPerRegistryCountsPerModule(regUniqueCountAndSizeTuples, title, outFile):
  fig, ax = plt.subplots()
  
  plt.xticks(rotation=30)
  # Sort by count of regexes, largest first, so plot is easier to interpret
  regUniqueCountAndSizeTuples.sort(key=lambda elt: elt[1], reverse=True)
  xlabels = [reg for reg, count, size in regUniqueCountAndSizeTuples]
  data = [count for _, count, _ in regUniqueCountAndSizeTuples]
  
  ax.bar(xlabels, data, align='center', alpha=0.5)

  ax.set_xticks(np.arange(len(xlabels)), xlabels)
  ax.set_ylabel('Number of unique regexes')
  ax.set_title(title) 

  plt.tight_layout()
  plt.savefig(outFile, bbox_inches='tight', pad_inches=0)
  libLF.log('Saved plot to {}'.format(outFile))

def loadRegexList(regexListFile):
  """Returns regexList, registries, internetSources"""
  regexList = []
  registries = set()
  internetSourceTypes = set()
  libLF.log('Loading regexes from {}'.format(regexListFile))
  with open(regexListFile, 'r') as inStream:
    for line in inStream:
      line = line.strip()
      if len(line) == 0:
        continue
      
      try:
        # Build the Regex
        regex = libLF.Regex()
        regex.initFromNDJSON(line)

        regexList.append(regex)
        registries = registries.union(regex.registriesUsedIn())
        internetSourceTypes = internetSourceTypes.union(regex.internetSourcesAppearedIn())
      except KeyboardInterrupt:
        raise
      except BaseException as err:
        libLF.log('Exception parsing line:\n  {}\n  {}'.format(line, err))

    libLF.log('Loaded {} Regex\'es'.format(len(regexList)))
    return regexList, list(registries), list(internetSourceTypes)

def perRegistryBoxPlots(regAndNumsTuples, title, ylabel, outFile, showOutliers=False, logScaleY=False):
  """Create a box plot for the distribution in each registry

  Box: 25/50/75 percentile
  Whiskers: (10, 90) percentile
  
  regAndNumsTuples: [(r1, nums), (r2, nums), ...]
  """
  fig, ax = plt.subplots()
  plt.xticks(rotation=30)
  ax.set_title(title)
  ax.set_ylabel(ylabel)

  xlabels = [reg for reg, nums in regAndNumsTuples]
  data = [nums for reg, nums in regAndNumsTuples]
  ax.boxplot(data,
    labels=xlabels,
    showfliers=showOutliers, # Outliers may make it hard to read.
    whis=[10,90] # Whiskers will show 10th and 90th percentile (rather than Q1/Q3 * IQR which isn't meaningful for non-normal data)
  )
  if logScaleY:
    plt.yscale('log')
  plt.tight_layout()
  plt.savefig(outFile, bbox_inches='tight', pad_inches=0)
  libLF.log('Figure for {}: {}'.format(title, outFile))

def getRegistry2nUniqueRegexes(registries, pattern2Regex):
  registry2nUniqueRegexes = {}
  for r in registries:
    registry2nUniqueRegexes[r] = 0

  for _, regex in pattern2Regex.items():
    for reg in regex.registriesUsedIn():
      registry2nUniqueRegexes[reg] += 1
  return registry2nUniqueRegexes

def getRegistry2nUniqueRegexesByType(registries, pattern_to_reg2modules):
  registry2nUniqueRegexesByType = {}
  for reg in registries:
    registry2nUniqueRegexesByType[reg] = {
      libLF.Regex.USE_TYPE_STATIC: 0,
      libLF.Regex.USE_TYPE_DYNAMIC: 0,
      "intersection": 0 # counts all regexes found both STATIC and DYNAMIC, so <= the value of the other keys.
    }

  # For each unique known pattern
  for pattern in pattern_to_reg2modules:
    # For each registry it appeared in
    for reg in pattern_to_reg2modules[pattern]:
      # For each possible extraction type by which it was seen in that registry
      foundInAllExtractionTypes = True
      for regexType in pattern_to_reg2modules[pattern][reg]:
        # If we saw it using this approach, count it
        if len(pattern_to_reg2modules[pattern][reg][regexType]) > 0:
          registry2nUniqueRegexesByType[reg][regexType] += 1
        else:
          foundInAllExtractionTypes = False
      if foundInAllExtractionTypes:
        registry2nUniqueRegexesByType[reg]["intersection"] += 1
  return registry2nUniqueRegexesByType

def makeReport_uniqueRegexesPerRegistry(registries, pattern2Regex):
  print("\n\n----------------\n\n")
  print("Report: Unique regexes per registry")
  print("\n\n----------------\n\n")

  registry2nUniqueRegexes = getRegistry2nUniqueRegexes(registries, pattern2Regex)

  formatStr = "%20s %20s %20s"
  print(formatStr % ("Language", "Registry", "Num unique regexes"))
  print(formatStr % ("-"*20, "-"*20, "-"*20))
  totalSum = 0
  for reg, count in registry2nUniqueRegexes.items():
    print(formatStr % (reg2lang[reg.lower()], reg, str(count)))
    totalSum += count
  print(" (Sum including duplicates = {})".format(totalSum))

def makeReport_staticDynamicRegexCorpus(registries, pattern_to_reg2modules,
  registry2nModules, registry2nModulesWithRegexes):
  print("\n\n----------------\n\n")
  print("Report: Regex corpus by extraction type")
  print("\n\n----------------\n\n")

  registry2nUniqueRegexesByType = getRegistry2nUniqueRegexesByType(registries, pattern_to_reg2modules)

  formatStr = "%20s %20s %20s %30s"
  print(formatStr % ("Extraction method", "Language", "# unique regexes", "# contributing modules (%%)"))
  print(formatStr % ("-"*20, "-"*20, "-"*20, "-"*30))
  for reg, nUniqueRegexesByType in registry2nUniqueRegexesByType.items():
    for regexType in nUniqueRegexesByType:
      nContributingModules = registry2nModulesWithRegexes[reg][regexType] if regexType != "intersection" else -1
      print(formatStr % (
        regexType,
        reg2lang[reg.lower()],
        nUniqueRegexesByType[regexType],
        "%d (%d%%)" % (nContributingModules, 100 * nContributingModules / registry2nModules[reg])
      ))

class RegexDupInfo:
  """Tracks the extent of regex duplication within a registry"""
  def __init__(self):
    self.nIntraLang = 0
    self.nInterLang = 0
    self.nInternet = 0
  
  def addIntraLang(self):
    self.nIntraLang += 1

  def addInterLang(self):
    self.nInterLang += 1

  def addInternet(self):
    self.nInternet += 1
  
  @staticmethod
  def registriesWithIntraLang(regex):
    regs = []
    for reg in regex.registriesUsedIn():
      # If used >1 in this registry, it is an intra-lang duplicate
      if regex.useCount_registry_to_nModules[reg] > 1:
        regs.append(reg)
    return regs

  @staticmethod
  def registriesWithInterLang(regex):
    regs = regex.registriesUsedIn()
    # If used in >1 registry, it is an inter-lang duplicate
    if len(regs) > 1:
      return regs
    return []

  @staticmethod
  def registriesWithInternet(regex):
    # If appears in any Internet source, it is an internet duplicate
    fromInternet = False
    for IS, nPosts in regex.useCount_IStype_to_nPosts.items():
      if nPosts > 0:
        fromInternet = True
        break
    
    if fromInternet:
      return regex.registriesUsedIn()
    return []

def makeReport_duplicatedRegexes(registries, pattern2Regex, visDir):
  print("\n\n----------------\n\n")
  print("Report: Duplicated regexes")
  print("\n\n----------------\n\n")

  registry2nUniqueRegexes = getRegistry2nUniqueRegexes(registries, pattern2Regex)

  lengthLimit_2_registry2dupInfo = {}
  for dupLengthLimit in DUP_LENGTH_LIMITS:
    registry2dupInfo = {} # reg -> RegexDupInfo
    for reg in registries:
      registry2dupInfo[reg] = RegexDupInfo()

    for pattern, regex in pattern2Regex.items():
      #libLF.log("dupLengthLimit {} pattern {} regex.pattern {}".format(dupLengthLimit, pattern, regex.pattern))
      # Only look at duplicates at list dupLengthLimit long
      # Otherwise consider them as independently derived, not duplicates
      if dupLengthLimit <= len(pattern):
        # Intra-lang duplicates
        for registry in RegexDupInfo.registriesWithIntraLang(regex):
          registry2dupInfo[registry].addIntraLang()
        # Inter-lang duplicates
        for registry in RegexDupInfo.registriesWithInterLang(regex):
          registry2dupInfo[registry].addInterLang()
        # Internet duplicates
        for registry in RegexDupInfo.registriesWithInternet(regex):
          registry2dupInfo[registry].addInternet()
    
    lengthLimit_2_registry2dupInfo[dupLengthLimit] = registry2dupInfo
    
  ### Table
  formatStr = "%20s %20s %20s %20s %20s %20s"
  print(formatStr % ("Language", "# uniq regex",
    "min regex len for dup",
    "# intra lang", "# inter lang", "# internet"))
  print(formatStr % ("-"*20, "-"*20, "-"*20, "-"*20, "-"*20, "-"*20))
  for lengthLimit in sorted(lengthLimit_2_registry2dupInfo.keys()):
    registry2dupInfo = lengthLimit_2_registry2dupInfo[lengthLimit]

    def val_to_val_and_perc(num, outOf):
      return "{} ({:.1f})".format(num, 100*num/outOf)

    for registry, dupInfo in registry2dupInfo.items():
      print(formatStr % (reg2lang[registry.lower()], str(registry2nUniqueRegexes[registry.lower()]),
        str(lengthLimit),
        val_to_val_and_perc(dupInfo.nIntraLang, registry2nUniqueRegexes[registry.lower()]),
        val_to_val_and_perc(dupInfo.nInterLang, registry2nUniqueRegexes[registry.lower()]),
        val_to_val_and_perc(dupInfo.nInternet, registry2nUniqueRegexes[registry.lower()]),
        ))

    # End of a section
    print(formatStr % ("-"*20, "-"*20, "-"*20, "-"*20, "-"*20, "-"*20))
  
  ### Barplot

  # Ordered by module counts at time of study, most to least
  PLOT_LANG_ORDER = ["JavaScript", "Java", "PHP", "Python", "Ruby", "Go", "Perl", "Rust"]
  registry2dupInfo = lengthLimit_2_registry2dupInfo[OFFICIAL_DUP_LENGTH_LIMIT]
  # Convert to lang2... so we can easily plot in order
  lang2nRegexes = {}
  lang2dupInfo = {}
  for reg, nRegexes in registry2nUniqueRegexes.items():
    lang2nRegexes[reg2lang[reg.lower()]] = nRegexes
  for reg, dupInfo in registry2dupInfo.items():
    lang2dupInfo[reg2lang[reg.lower()]] = dupInfo
  
  intraDups =     [ (100 * lang2dupInfo[l].nIntraLang / lang2nRegexes[l]) for l in PLOT_LANG_ORDER]
  interDups =     [ (100 * lang2dupInfo[l].nInterLang / lang2nRegexes[l]) for l in PLOT_LANG_ORDER]
  internetDups =  [ (100 * lang2dupInfo[l].nInternet  / lang2nRegexes[l]) for l in PLOT_LANG_ORDER]

  ind = np.arange(len(PLOT_LANG_ORDER))
  barSetWidth= 0.9
  indivBarWidth = barSetWidth / 3

  plt.style.use('grayscale')

  fig, ax = plt.subplots()
  ax.bar(ind - indivBarWidth, intraDups,    indivBarWidth, label='Intra-language duplicates')
  ax.bar(ind,                 interDups,    indivBarWidth, label='Inter-language duplicates', hatch='/')
  ax.bar(ind + indivBarWidth, internetDups, indivBarWidth, label='Internet duplicates', hatch='\\')

  ax.set_ylabel('Percent of the unique regexes')
  ax.set_title('Re-used regexes, by language')
  ax.set_xticks(ind)
  ax.set_xticklabels(PLOT_LANG_ORDER, rotation=45)
  ax.xaxis.set_tick_params(length=0)
  #ax.legend(fontsize='x-large')
  plt.tight_layout()
  outFile = os.path.join(visDir, 'per-language-regex-duplication.png')
  plt.savefig(outFile, bbox_inches='tight', pad_inches=0)
  libLF.log('Saved plot to {}'.format(outFile))

def makeReport_modulesWithDuplicatedRegexes(langGHPCounts, pattern2regex, pattern_to_reg2modules, visDir):
  print("\n\n----------------\n\n")
  print("Report: Modules with duplicated regexes")
  print("\n\n----------------\n\n")

  lengthLimit_2_lang2modulesWithDups = {}
  for dupLengthLimit in DUP_LENGTH_LIMITS:
    libLF.log("Analyze: dupLengthLimit {}".format(dupLengthLimit))
    lang2modulesWithDups = {}
    for _, lang in reg2lang.items():
      lang2modulesWithDups[lang] = {
        'intra': set(),
        'inter': set(),
        'internet': set(),
        'any': set(),
      }

    for pattern, reg2modules in pattern_to_reg2modules.items():
      if len(pattern) >= dupLengthLimit:
        #libLF.log("re-use: Pattern /{}/".format(pattern))

        nRegistriesWithRegex = 0
        for reg, modules in reg2modules.items():
          # Modules with intra-registry regex re-use
          if len(modules) > 1:
            lang2modulesWithDups[reg2lang[reg.lower()]]['intra'] |= modules
            if dupLengthLimit == OFFICIAL_DUP_LENGTH_LIMIT:
              libLF.log("   real re-use on /{}/: intra: reg {}: {}".format(pattern, reg, modules))
          
          if len(modules) > 0:
            nRegistriesWithRegex += 1
        
        # Modules with inter-registry regex re-use
        if nRegistriesWithRegex > 1:
          for reg, modules in reg2modules.items():
            lang2modulesWithDups[reg2lang[reg.lower()]]['inter'] |= modules
            if dupLengthLimit == OFFICIAL_DUP_LENGTH_LIMIT:
              libLF.log("   real re-use on /{}/: inter: reg {}: {}".format(pattern, reg, modules))

        # Modules with internet regex re-use
        if len(RegexDupInfo.registriesWithInternet(pattern2regex[pattern])) > 0:
          for reg, modules in reg2modules.items():
            lang2modulesWithDups[reg2lang[reg.lower()]]['internet'] |= modules
            if dupLengthLimit == OFFICIAL_DUP_LENGTH_LIMIT:
              libLF.log("   real re-use on /{}/: internet: reg {}: {}".format(pattern, reg, modules))
          
          # Results are really high, let's see what the patterns are...
          libLF.log("  lengthLimit {}: Internet re-used: /{}/".format(dupLengthLimit, pattern))

        # Modules with any dups: OR the other classes
        lang2modulesWithDups[reg2lang[reg.lower()]]['any'] |= (
          lang2modulesWithDups[reg2lang[reg.lower()]]['intra'] |
          lang2modulesWithDups[reg2lang[reg.lower()]]['inter'] |
          lang2modulesWithDups[reg2lang[reg.lower()]]['internet'] 
        )
    
    libLF.log("dupLengthLimit {}, lang2modulesWithDups {}".format(dupLengthLimit, lang2modulesWithDups))
    lengthLimit_2_lang2modulesWithDups[dupLengthLimit] = lang2modulesWithDups

  ### Table
  formatStr = "%20s %20s %25s %20s %20s %20s %20s"
  print(formatStr % ("Language", "# modules",
    "min regex len for dup",
    "# intra lang", "# inter lang", "# internet", "# any"))
  print(formatStr % ("-"*20, "-"*20, "-"*25, "-"*20, "-"*20, "-"*20, "-"*20))

  for lengthLimit in sorted(lengthLimit_2_lang2modulesWithDups.keys()):
    libLF.log("Table for lengthLimit {}".format(lengthLimit))
    lang2modulesWithDups = lengthLimit_2_lang2modulesWithDups[lengthLimit]

    def val_to_val_and_perc(num, outOf):
      return "{} ({:.1f})".format(num, 100*num/outOf)

    totalModulesWithIntraLangDups = 0
    totalModulesWithInterLangDups = 0
    totalModulesWithInternetDups = 0
    totalModulesWithAnyDups = 0
    totalModulesAnalyzed = 0
    for lang, dupInfo in lang2modulesWithDups.items():
      libLF.log("lengthLimit {}: {} had {} dups of type intra".format(lengthLimit, lang, len(dupInfo['intra']) ))
      print(formatStr % (lang, langGHPCounts[lang],
        lengthLimit,
        val_to_val_and_perc(len(dupInfo['intra']), langGHPCounts[lang]),
        val_to_val_and_perc(len(dupInfo['inter']), langGHPCounts[lang]),
        val_to_val_and_perc(len(dupInfo['internet']), langGHPCounts[lang]),
        val_to_val_and_perc(len(dupInfo['any']), langGHPCounts[lang]),
        ))
      # Unique per language; no overlap between languages.
      totalModulesWithIntraLangDups += len(dupInfo['intra'])
      totalModulesWithInterLangDups += len(dupInfo['inter'])
      totalModulesWithInternetDups  += len(dupInfo['internet'])
      totalModulesWithAnyDups       += len(dupInfo['any'])
      totalModulesAnalyzed += langGHPCounts[lang]
    print(formatStr % ("ACROSS ALL LANGS", totalModulesAnalyzed,
      lengthLimit, 
      val_to_val_and_perc(totalModulesWithIntraLangDups, totalModulesAnalyzed),
      val_to_val_and_perc(totalModulesWithInterLangDups, totalModulesAnalyzed),
      val_to_val_and_perc(totalModulesWithInternetDups, totalModulesAnalyzed),
      val_to_val_and_perc(totalModulesWithAnyDups, totalModulesAnalyzed),
      ))

    # End of a section
    print(formatStr % ("-"*20, "-"*20, "-"*25, "-"*20, "-"*20, "-"*20, "-"*20))
  print()
  libLF.log("Done with report")

  ### Barplot

  # Ordered by module counts at time of study, most to least
  PLOT_LANG_ORDER = ["JavaScript", "Java", "PHP", "Python", "Ruby", "Go", "Perl", "Rust"]
  lang2modulesWithDups = lengthLimit_2_lang2modulesWithDups[OFFICIAL_DUP_LENGTH_LIMIT]
  
  NUM_BARS = 4
  intraDups =     [ (100 * len(lang2modulesWithDups[l]['intra'])     / langGHPCounts[l]) for l in PLOT_LANG_ORDER]
  interDups =     [ (100 * len(lang2modulesWithDups[l]['inter'])     / langGHPCounts[l]) for l in PLOT_LANG_ORDER]
  internetDups =  [ (100 * len(lang2modulesWithDups[l]['internet'])  / langGHPCounts[l]) for l in PLOT_LANG_ORDER]
  anyDups =       [ (100 * len(lang2modulesWithDups[l]['any'])       / langGHPCounts[l]) for l in PLOT_LANG_ORDER]

  ind = np.arange(len(PLOT_LANG_ORDER))
  barSetWidth= 0.8
  indivBarWidth = barSetWidth / NUM_BARS

  plt.style.use('grayscale')

  fig, ax = plt.subplots()
  ax.bar(ind - 1*indivBarWidth, anyDups,      indivBarWidth, label='Any dups.')
  ax.bar(ind - 0*indivBarWidth, intraDups,    indivBarWidth, label='Intra-lang. dups.', hatch='//')
  ax.bar(ind + 1*indivBarWidth, interDups,    indivBarWidth, label='Inter-lang. dups.', hatch='\\\\')
  ax.bar(ind + 2*indivBarWidth, internetDups, indivBarWidth, label='Internet dups.', hatch='o')

  ax.set_ylabel('Percent of modules')
  #for tick in ax.yaxis.get_major_ticks():
  #  tick.label.set_fontsize('x-large')
  ax.set_title('Modules with re-used regexes, by language')
  ax.set_xticks(ind)
  ax.set_xticklabels(PLOT_LANG_ORDER, rotation=45)
  ax.xaxis.set_tick_params(length=0)
  ax.legend()
  plt.tight_layout()
  outFile = os.path.join(visDir, 'per-language-modules-with-duplicates.png')
  plt.savefig(outFile, bbox_inches='tight', pad_inches=0)
  libLF.log('Saved plot to {}'.format(outFile))

def makeReport_mostDuplicatedRegexes(pattern2Regex):
  print("\n\n----------------\n\n")
  print("Report: Most-duplicated regexes")
  print("\n\n----------------\n\n")

  pattern_langs_dupCount = []
  for pattern, regex in pattern2Regex.items():
    dupCount = 0
    for reg in regex.registriesUsedIn():
      if regex.useCount_registry_to_nModules[reg] >= 0:
        dupCount += regex.useCount_registry_to_nModules[reg]
    assert(dupCount > 0)
    libLF.log("Pattern /{}/ used in {} modules".format(pattern, dupCount))
    pattern_langs_dupCount.append((pattern, len(regex.registriesUsedIn()), dupCount))

  formatStr = "%-15s %-10s %-20s %-100s"
  print(formatStr % ("Length limit", "Num langs.", "Total num. modules", "Pattern"))
  
  pattern_langs_dupCount.sort(key=lambda p_c: p_c[2], reverse=True)
  for length in DUP_LENGTH_LIMITS:
    print(formatStr % ("-"*15, "-"*10, "-"*20, "-"*100))
    nToPrint = 250
    for pattern, nLangs, dupCount in itertools.islice(filter(lambda p_c: len(p_c[0]) >= length,
                                                  pattern_langs_dupCount),
                                           nToPrint):
      print(formatStr % (length, nLangs, dupCount, pattern))
  print(formatStr % ("-"*15, "-"*10, "-"*20, "-"*100))

def countUniqueRegexes(fileName):
  regexUsages = loadRegexUsages(fileName)
  uniqueRegexes = set()
  for ru in regexUsages:
    # Non-string regex are bugs in the extractor
    if type(ru.pattern) is not str:
      continue
    # 'DYNAMIC'/'DYNAMIC-PATTERN' are not duplicates.
    if ru.pattern == "DYNAMIC" or ru.pattern == "DYNAMIC-PATTERN":
      continue
    uniqueRegexes.add(ru.pattern)
  return len(uniqueRegexes)
    
def loadRegexUsages(fileName):
  """Return libLF.RegexUsage[] from NDJSON file"""
  regexUsages = []
  with open(fileName, 'r') as inStream:
    for line in inStream:
      line = line.strip()
      if len(line) == 0:
        continue
        
      ru = libLF.RegexUsage()
      try:
        ru.initFromNDJSON(line)
        regexUsages.append(ru)
      except BaseException:
        libLF.log("Could not parse line in {}: {}".format(fileName, line))
  return regexUsages

def findProjectsAboveCountPercentileCutoff(ghps, regexType, countPercentileCutoff):
  if countPercentileCutoff <= 0 or 100 <= countPercentileCutoff:
    # Ways to say "don't discard any"
    return []

  libLF.log("Computing {} percentile cutoff for p'ile {}".format(regexType, countPercentileCutoff))
  nonZeroProjRegexCounts = []
  for ghp in ghps:
    if regexType == libLF.Regex.USE_TYPE_DYNAMIC:
      regexPath = ghp.dynRegexPath
    elif regexType == libLF.Regex.USE_TYPE_STATIC:
      regexPath = ghp.regexPath
    else:
      raise ValueError("Error, unexpected regexType {}".format(regexType))
    # skip: No file
    if not regexPath or len(regexPath) == 0:
      continue
    if not os.path.isfile(regexPath):
      continue

    # Count unique dynamic regexes
    regexCount = countUniqueRegexes(regexPath)
    if regexCount == 0:
      # skip: No regexes
      continue
    # Keep
    nonZeroProjRegexCounts.append((ghp, regexCount))

  libLF.log("{}: {} projects with >0 {} regexes".format(ghps[0].registry, len(nonZeroProjRegexCounts), regexType))
  if len(nonZeroProjRegexCounts) == 0:
    # If nobody has any dynamic regexes, I guess we're done here
    return []
  # Sort from fewest to most regexes so that we can use percentile indexing
  nonZeroProjRegexCounts.sort(key=lambda x: x[1])

  counts = [x[1] for x in nonZeroProjRegexCounts]
  percentiles = [
    (p, np.percentile(counts, p, interpolation='lower'))
    for p in [10, 25, 50, 75, 90]
  ]
  libLF.log("{}: regex percentiles: {}".format(ghps[0].registry, percentiles))

  # Identify projects above the cutoff
  regCountAtCutoff = np.percentile(counts, countPercentileCutoff, interpolation='lower')
  cutoffIx = counts.index(regCountAtCutoff)
  libLF.log("{}: you should omit the {} projects above the {} p'ile (they have {} - {} {} regexes)" \
    .format(ghps[0].registry, len(nonZeroProjRegexCounts) - cutoffIx, countPercentileCutoff,
    nonZeroProjRegexCounts[cutoffIx][1], nonZeroProjRegexCounts[-1][1],
    regexType
    ))
  for ghp, nReg in nonZeroProjRegexCounts[cutoffIx:]:
    projectName = ghp.owner + '/' + ghp.name
    url = "https://www.github.com/{}".format(projectName)
    libLF.log("  Outlier project ({} regexes): {} -> {}".format(nReg, projectName, url))

  # Return surviving projects
  return [
    pair[0]
    for pair in nonZeroProjRegexCounts[cutoffIx:]
  ]

def main(regexTypes, ghpLists, intSrcLists, ghpCurPrefix, ghpNewPrefix, countPercentileCutoff, uniqueRegexFile, uniqueXRegistryRegexFile, makeDuplReports, visDir):
  libLF.log("regexTypes {} ghpLists {} intSrcLists {} ghpCurPrefix {} ghpNewPrefix {} countPercentileCutoff {} uniqueRegexFile {} uniqueXRegistryRegexFile {} makeDuplReports {} visDir {}" \
    .format(regexTypes, ghpLists, intSrcLists, ghpCurPrefix, ghpNewPrefix, countPercentileCutoff, uniqueRegexFile, uniqueXRegistryRegexFile, makeDuplReports, visDir))
  #### Load data

  registries = set() # ['cpan', 'perl', ...]
  internetSourceTypes = set() # ['StackOverflow', 'RegExLib', ...]

  pattern2Regex = {} # pattern -> Regex
  pattern_to_reg2modules = {} # pattern -> {"cpan": { "static": set("m1", "m2", ...), "dynamic": ...}, ... }
  registry2nRegexUsages = {} # registry -> { "static": [nRegexUsageInModule1, ...], "dynamic": ... }
  registry2nUniqueRegexes = {} # registry -> { "static": [nUniqueRegexesInModule, ...], "dynamic": ... }
  registry2nModules = {} # { registry -> int }
  registry2nModulesWithRegexes = {} # registry -> { "static": N_MODULES_NREG>0, "dynamic": N_MODULES_NREG>0 }
  registryGHPCounts = {} # registry -> # projects in that registry
  langGHPCounts = {} # language -> # projects in that registry

  # Process each GHP list
  libLF.log('Loading regexes from {} GHP lists'.format(len(ghpLists)))
  for githubProjectList in ghpLists:
    ghps = getGHPs(githubProjectList, ghpCurPrefix, ghpNewPrefix)

    libLF.log("{}: Computing outlier projects whose regexes we should skip".format(ghps[0].registry))
    staticGHPsToSkip = findProjectsAboveCountPercentileCutoff(ghps, libLF.Regex.USE_TYPE_STATIC, countPercentileCutoff)
    dynamicGHPsToSkip = findProjectsAboveCountPercentileCutoff(ghps, libLF.Regex.USE_TYPE_DYNAMIC, countPercentileCutoff)

    uniqueGHPURLs = set()
    for i, ghp in enumerate(ghps):
      if ghp.registry not in registryGHPCounts:
        registryGHPCounts[ghp.registry] = 0
      registryGHPCounts[ghp.registry] += 1
      uniqueGHPURLs.add("{}/{}".format(ghp.owner, ghp.name))

      skipStatic = ghp in staticGHPsToSkip
      skipDynamic = ghp in dynamicGHPsToSkip
      processOneGitHubProject(i, regexTypes, skipStatic, skipDynamic, ghp, # inputs
        # outputs
        pattern2Regex, registry2nRegexUsages, registry2nUniqueRegexes,
        registry2nModules, registry2nModulesWithRegexes, pattern_to_reg2modules
        )
      registries.add(ghp.registry)
    
    libLF.log("Got {} ghps in {}; {} unique".format(len(ghps), ghps[0].registry, len(uniqueGHPURLs)))

  for registry, count in registryGHPCounts.items():
    langGHPCounts[reg2lang[registry.lower()]] = count

  # Process each InternetSource list
  libLF.log('Cross-referencing with possible-patterns in InternetSource\'s')
  for internetSourceList in intSrcLists:
    isl = getInternetSourceList(internetSourceList)
    for internetSource in isl:
      processOneInternetSource(internetSource, pattern2Regex)
      internetSourceTypes.add(internetSource.type)
  
  #### Reports

  makeReport_uniqueRegexesPerRegistry(registries, pattern2Regex)
  makeReport_staticDynamicRegexCorpus(registries, pattern_to_reg2modules, registry2nModules, registry2nModulesWithRegexes)

  if makeDuplReports:
    libLF.log("Generating duplication reports")
    makeReport_duplicatedRegexes(registries, pattern2Regex, visDir)
    makeReport_modulesWithDuplicatedRegexes(langGHPCounts, pattern2Regex, pattern_to_reg2modules, visDir)
    makeReport_mostDuplicatedRegexes(pattern2Regex)
  else:
    libLF.log("Skipping duplication reports")
  
  #### Emit Regex lists

  libLF.log('Emitting the {} unique regexes found in the GHPs to {}'.format(len(pattern2Regex), uniqueRegexFile))
  with open(uniqueRegexFile, 'w') as outStream:           
      for pattern in pattern2Regex:
          outStream.write(pattern2Regex[pattern].toNDJSON() + '\n')

  # TODO If we need to do this more than once,
  # split it out into a separate script to analyze the uniqueRegexFile
  regexesInMultipleRegistries = [
    pattern2Regex[pattern]
    for pattern in pattern2Regex
    if len(pattern2Regex[pattern].registriesUsedIn()) > 1
  ]
  libLF.log('Emitting the {} unique regexes found in multiple registries to {}'.format(len(regexesInMultipleRegistries), uniqueXRegistryRegexFile))
  with open(uniqueXRegistryRegexFile, 'w') as outStream:
      for regex in regexesInMultipleRegistries:
          outStream.write(regex.toNDJSON() + '\n')

  #### Intra-registry measurements
  libLF.log("That's all for the DR paper. Below we used to produce some visualizations for LF but we didn't include them in the manuscript.")
  return
  
  ## Per registry: Visualize regex distributions
  registryOrderByMoreRegexUsage = sorted(registry2nRegexUsages.keys(),
    # Sort by median first, then by 3Q as a tiebreaker
    key=lambda reg: (np.percentile(registry2nRegexUsages[reg], 50),
                      np.percentile(registry2nRegexUsages[reg], 75)),
    reverse=True)
  libLF.log('order: {}'.format(registryOrderByMoreRegexUsage))

  # Boxplot: distribution of count of 'new Regex()'-type declarations, by module
  regAndNumsTuples_raw = [(reg, registry2nRegexUsages[reg]) for reg in registryOrderByMoreRegexUsage]
  perRegistryBoxPlots(
    regAndNumsTuples_raw,
    'Regex creation sites in modules in different registries', 'Number of regex creation sites',
    os.path.join(visDir, 'regex-creation-sites-by-module.png'))

  # Boxplot: distribution of unique patterns declared, by module
  regAndNumsTuples_unique = [(reg, registry2nUniqueRegexes[reg]) for reg in registryOrderByMoreRegexUsage]
  perRegistryBoxPlots(
    regAndNumsTuples_unique,
    'Unique regexes in modules in different registries', 'Number of unique patterns',
    os.path.join(visDir, 'unique-regex-creations-by-module.png'))

  # Boxplot: distribution of regex duplication counts, by regex
  uniqueRegexes = pattern2Regex.values()
  regAndNumsTuples_regexDupl = []
  for registry in registryOrderByMoreRegexUsage:
    # Only consider regexes that appeared at least once in this registry
    uniqRegexModuleAppearances = [
      regex.useCount_registry_to_nModules[registry]
      for regex in uniqueRegexes
      if (registry in regex.useCount_registry_to_nModules \
          and 0 < regex.useCount_registry_to_nModules[registry])
    ]
    uniqRegexModuleAppearances.sort(reverse=True)
    regAndNumsTuples_regexDupl.append((registry, uniqRegexModuleAppearances))
    #libLF.log('registry {}:\nduplication counts:\n  {}'.format(registry, regAndNumsTuples_regexDupl))
  perRegistryBoxPlots(
    regAndNumsTuples_regexDupl,
    'Intra-registry regex duplication', 'Regex duplication count',
    os.path.join(visDir, 'intra-registry-regex-duplication-by-module.png'),
    showOutliers=True, logScaleY=True)

  #sys.exit(1)

  # Per registry: Visualize intra-registry regex duplication

  #### Calculate duplicates

  regexList = pattern2Regex.values()

  # Initialize
  registryDupDegree2nRegexes = {} # 0 -> 0, 1 -> n regexes in 1 registry, 2 -> n regexes in 2 registries, ...
  for degree in range(1, len(registries) + 1):
      registryDupDegree2nRegexes[degree] = 0

  registryDupDegree2nRegexesAndInternet = {} # 0 -> 0, 1 -> n regexes in 1 registry and SO or REL, 2 -> n regexes in 2 registries and SO or REL, ...
  for degree in range(1, len(registries) + 1):
      registryDupDegree2nRegexesAndInternet[degree] = 0 

  registry2overlapDict = {} # 'cpan' -> { 'cpan': X, 'npm': Y, ... }
  for base in registries:
    registry2overlapDict[base] = {}
    for rel in registries:
        registry2overlapDict[base][rel] = 0

  registry2GloballyUniqueCount = {} # 'cpan -> X'
  for base in registries:
    registry2GloballyUniqueCount[base] = 0

  # Populate
  libLF.log('Calculating intersections')
  for regex in regexList:
    # Every regex is in at least one registry
    registryCounts = regex.useCount_registry_to_nModules # Might be 0's in here
    registriesIn = [reg for reg in registryCounts if registryCounts[reg] > 0]

    # Count # registries
    registryDupDegree2nRegexes[len(registriesIn)] += 1

    #count degree but also on internet
    if len(regex.useCount_IStype_to_nPosts) > 0:
      registryDupDegree2nRegexesAndInternet[len(registriesIn)] += 1

    # Mark the pairwise duplicates 
    for base in registriesIn:
      for rel in registriesIn:
          registry2overlapDict[base][rel] += 1

    # Count globally unique
    for base in registriesIn:
      if len(regex.useCount_registry_to_nModules) == 1 and base in regex.useCount_registry_to_nModules:
        registry2GloballyUniqueCount[base] += 1  

  #### Visualization

  # Make sure plot labels are readable 
  font = {'family' : 'normal',
        'weight' : 'normal',
        'size'   : 14}
  matplotlib.rc('font', **font)

  # Setup/produce graphs
  degreeDuplication = []
  for degree in range(1, len(registries) + 1):
    degreeDuplication.append((degree, registryDupDegree2nRegexes[degree]))
  visualizeBar(degreeDuplication,
    'Degree of Regex Duplication', 'Number of Registries', 'Count',
    os.path.join(visDir, 'degreeCountViz.png'),
    logAxis=True)
  
  registry2GloballyUniquePercent = []
  for base in registries:
    registry2GloballyUniquePercent.append((base, registry2GloballyUniqueCount[base]/registry2overlapDict[base][base]))
  visualizeBar(registry2GloballyUniquePercent,
    'Percentage of Registry Regex Globally Unique', '', 'Percent Globally Unique',
    os.path.join(visDir, 'percentGlobalUniqueByRegistry.png'),
    logAxis=False, rotate=True)

  regUniqueCountAndSizeTuples = [] # elts are (reg, # unique regexes, # modules in registry)
  for registry in registryGHPCounts:
    if registry in registry2overlapDict:
      regUniqueCountAndSizeTuples.append((registry, registry2overlapDict[registry][registry], registryGHPCounts[registry]))
  visualizeUniqueRegexPerRegistryCountsPerModule(regUniqueCountAndSizeTuples,
    'Unique Regexes per Registry',
    os.path.join(visDir, 'perRegistryUniqueViz.png'))
      
  degreeDuplicationAndInternet = []
  for degree in range(1, len(registries) + 1):
    degreeDuplicationAndInternet.append((degree, registryDupDegree2nRegexesAndInternet[degree]))
  visualizeBar(degreeDuplicationAndInternet,
    'Degree of Internet Regex Duplication', 'Number of Registries', 'Count',
    os.path.join(visDir, 'degreeCountInternetViz.png'))
  
  ## Emit
  
  # registryDupDegree2nRegexes as a list
  print('--------------------------------')
  print('Registry duplication degree')
  print('--------------------------------')
  print()
  print('Registry duplication degree'.ljust(30), 'n regexes')
  nAllRegexes = 0
  allRegexes_nMoreThanOneReg = 0
  for degree in range(1, len(registries) + 1):
    nAllRegexes += registryDupDegree2nRegexes[degree]
    print('{}'.format(degree).ljust(30) + '{}'.format(registryDupDegree2nRegexes[degree]))
    if degree > 1:
      allRegexes_nMoreThanOneReg += registryDupDegree2nRegexes[degree]
  print('\n  {} ({:.2f}%) of all {} regexes appeared in > 1 registry'.format(allRegexes_nMoreThanOneReg, 100 * (allRegexes_nMoreThanOneReg / nAllRegexes), nAllRegexes))
  print()
  print()
  print()

  # degreeDuplicationAndInternet as a list
  print('--------------------------------')
  print('Registry duplication degree for Internet Regexes')
  print('--------------------------------')
  print()
  print('Internet regex: registry duplication degree'.ljust(30), 'n regexes')
  nInternetRegexes = 0
  internetRegexes_nMoreThanOneReg = 0
  for degree, count in degreeDuplicationAndInternet:
    nInternetRegexes += count
    print('{}'.format(degree).ljust(30) + '{}'.format(count))
    if degree > 1:
      internetRegexes_nMoreThanOneReg += count
  if nInternetRegexes:
    print('\n  {} ({:.2f}%) of the {} regexes that exactly match an internet regex appeared in > 1 registry'.format(internetRegexes_nMoreThanOneReg, 100 * (internetRegexes_nMoreThanOneReg / nInternetRegexes), nInternetRegexes))
  print()
  print()
  print()

  # registry2overlapDict as an reg x reg table
  print('--------------------------------')
  print('Pairwise regex duplication')
  print('--------------------------------')
  print()
  sys.stdout.write(''.ljust(10))
  for base in registries:
    sys.stdout.write(base.ljust(10))
  sys.stdout.write('\n')

  for base in registries:
    sys.stdout.write(base.ljust(10))
    for rel in registries:
      sys.stdout.write('{}'.format(registry2overlapDict[base][rel]).ljust(10))
    sys.stdout.write('\n')
  print()
  print()
  print()

#####################################################

# Parse args
parser = argparse.ArgumentParser(description='De-duplication, metrics, and visualizations for regexes. Includes optional regex re-use/duplication analyses')
parser.add_argument('--regex-types', nargs='+', type=str, help='Type(s) of regexes to analyze -- {static|dynamic}', required=True,
  dest='regexTypes')
parser.add_argument('--github-project-lists', nargs='+', type=str, help='Files: GitHub project lists with extracted regexes to examine regexes', required=True, default=[],
  dest='ghpLists')
parser.add_argument('--internet-source-lists', nargs='+', type=str, help='Files: List of InternetRegexSource to examine regexes that may coming from the internet', required=False, default=[],
  dest='intSrcLists')
parser.add_argument('--cur-prefix', help='In: If there is a problem with GHP regexPaths, list current prefix', required=False, default=None,
  dest='ghpCurPrefix')
parser.add_argument('--new-prefix', help='In: If there is a problem with GHP regexPaths, list new prefix', required=False, default=None,
  dest='ghpNewPrefix')
parser.add_argument('--count-percentile-cutoff', help='Exclude regexes from projects at or above this percentile. This is computed on a per-ghp-list (i.e. per-registry) basis and on a per-type (static/dynamic) basis. Percentile is computed only among those projects in which we found >0 regexes. 98%% or 99%% is probably a good choice. Give 100 to exclude none (default)', required=False, type=int, default=101,
  dest='countPercentileCutoff')
parser.add_argument('--unique-regex-file', help='Out: Where to save the list of unique Regexes', required=False, default='/tmp/unique-regex-file.json',
  dest='uniqueRegexFile')
parser.add_argument('--unique-cross-registry-regexes', help='Out: Where to save the list of unique Regexes that occurred in multiple Registries', required=False, default='/tmp/unique-regex-file.json',
  dest='uniqueXRegistryRegexFile')
parser.add_argument('--make-dupl-reports', help='In: Make duplication reports, or just dedup regexes?', required=False, default=False, action='store_true',
  dest='makeDuplReports')
parser.add_argument('--vis-dir', help='Out: Where to save plots?', required=False, default='/tmp',
  dest='visDir')
args = parser.parse_args()

VALID_REGEX_TYPES = [libLF.Regex.USE_TYPE_STATIC, libLF.Regex.USE_TYPE_DYNAMIC]
args.regexTypes = [t.lower() for t in args.regexTypes]
for t in args.regexTypes:
  if t not in VALID_REGEX_TYPES:
    libLF.log("Must provide regexType from {} (you gave invalid type {})".format(VALID_REGEX_TYPES, t))
    sys.exit(1)

if (args.ghpCurPrefix is None) ^ (args.ghpNewPrefix is None):
  libLF.log('Must provide both GHP prefixes or neither')
  sys.exit(1)

# Here we go!
main(args.regexTypes, args.ghpLists, args.intSrcLists, args.ghpCurPrefix, args.ghpNewPrefix, args.countPercentileCutoff, args.uniqueRegexFile, args.uniqueXRegistryRegexFile, args.makeDuplReports, args.visDir)
