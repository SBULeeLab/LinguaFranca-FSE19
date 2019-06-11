#!/usr/bin/env python3
# Analyze the results of testing a bunch of libLF.Regex's for semantic behavior.

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

import re

import itertools

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

matplotlib.rcParams.update({
  'axes.labelsize': 'x-large',
  'axes.titlesize': 'xx-large',
  'xtick.labelsize': 'x-large',
  'ytick.labelsize': 'x-large',
  'font.family': 'normal',
  'legend.fontsize': 'x-large',
})

##########
# Globals
##########

NO_WITNESS = "no witness"
ANY_WITNESS = "any witness"
MATCH_WITNESS = "match witness"
SUBSTRING_WITNESS = "substring witness"
CAPTURE_WITNESS = "capture witness"
WITNESS_TYPES = [
  NO_WITNESS,
  ANY_WITNESS,
  MATCH_WITNESS,
  SUBSTRING_WITNESS,
  CAPTURE_WITNESS
]

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

lcLang2lang = {
  "javascript": "JavaScript",
  "rust": "Rust",
  "php": "PHP",
  "python": "Python",
  "ruby": "Ruby",
  "perl": "Perl",
  "java": "Java",
  "go": "Go",
}

def allLangs():
  return sorted(reg2lang.values())

def nick2full(lang):
  return lcLang2lang[lang]

# Ordered by module counts at time of study, most to least
PLOT_LANG_ORDER = ["JavaScript", "Java", "PHP", "Python", "Ruby", "Go", "Perl", "Rust"]

################
# Ingest: Loading a (very large) file of libLF.Regex's
#         with the semanticDifferenceWitnesses field populated
################

class MyTask(libLF.parallel.ParallelTask):
  def __init__(self, lines):
    self.lines = lines
  
  def run(self):
    regexes = []
    for line in self.lines:
      try:
        # Build a libLF.Regex
        regex = libLF.Regex().initFromNDJSON(line)
        regexes.append(regex)
      except KeyboardInterrupt:
        raise
      except BaseException as err:
        libLF.log('Exception parsing line:\n  {}\n  {}'.format(line, err))
        traceback.print_exc()
    libLF.log("Worker: Converted {} lines to NDJSON".format(len(self.lines)))
    return regexes

def lines2tasks(lines, nChunks):
  """Return list of lists of tasks, divided into chunks.

  The lists of tasks do not have the same order as the original lines.
  """
  lineLists = []
  for w in range(nChunks):
    lineLists.append([])
  
  i = 0
  for line in lines:
    lineLists[i].append(line)
    i = (i + 1) % nChunks
  
  tasks = [
    MyTask(lineList) for lineList in lineLists
  ]
  return tasks

def loadRegexFile(regexFile):
  """Return libLF.Regex[]"""
  libLF.log('Loading regexes from {}'.format(regexFile))
  lines = []
  with open(regexFile, 'r') as inStream:
    for line in inStream:
      line = line.strip()
      if len(line) == 0:
        continue
      lines.append(line) 
  
  libLF.log('Converting the {} regex NDJSON lines to libLF.Regex objects'.format(len(lines)))
  nCPUs = os.cpu_count()
  tasks = lines2tasks(lines, 2*nCPUs) # Break into extra pieces in case some take longer than others

  results = libLF.parallel.map(tasks, libLF.parallel.CPUCount.CPU_BOUND,
    libLF.parallel.RateLimitEnums.NO_RATE_LIMIT, libLF.parallel.RateLimitEnums.NO_RATE_LIMIT,
    jitter=False)
  
  regexes = []
  for subList in results:
    regexes += subList

  libLF.log('Loaded {} regexes from {}'.format(len(regexes), regexFile))
  return regexes

################
# Analysis: Distribution of the number of unique inputs tested for each regex
################

def makeReport_distributionOfInputs(regexes):
  df = pd.DataFrame.from_records(
        data=[(regex.nUniqueInputsTested,) for regex in regexes],
        columns=["NumInputs"]
  )
  libLF.log("Distribution of the number of inputs used for the {} regexes".format(len(regexes)))
  print(df.describe())

################
# Analysis: Classifying regexes by distinct witness types
################

def makeReport_classifyWitnesses(allRegexes):
  regexCounts = countRegexesByWitnesses(allRegexes)

  nRegexesWithAnyWitness = len(allRegexes) - regexCounts[NO_WITNESS]

  # Summarize high-level categories
  print("\n--------------------------------\n")
  print("{}/{} ({:.2f}%) of the regexes have witnesses of any kind" \
    .format(nRegexesWithAnyWitness, len(allRegexes), 100 * (nRegexesWithAnyWitness/len(allRegexes))))

  formatStr = "%-45s %30s %20s"
  print(formatStr % ("Type of regex", "Number of regexes", "Percent of regexes"))
  print(formatStr % ("-"*45, "-"*30, "-"*20))
  # Print in a sensible order
  for regexType in WITNESS_TYPES:
    print(formatStr % ("# regexes with {}".format(str(regexType)),
                       regexCounts[regexType],
                       "{:.1f}".format(100*regexCounts[regexType]/len(allRegexes))))

def countRegexesByWitnesses(regexes):
  """Returns regexCount: { MATCH_WITNESS: nRegexesWithAnyMatchWitneses, ... }

  The sum of the categories is >= len(regexes) because a regex may have
  more than one type of witness.
  """
  regexCount = {
    NO_WITNESS: 0,
    ANY_WITNESS: 0,
    MATCH_WITNESS: 0,
    SUBSTRING_WITNESS: 0,
    CAPTURE_WITNESS: 0,
  }
  for regex in regexes:
    nWitnessTypes = 0

    # Existence of witness
    if len(regex.semanticDifferenceWitnesses) == 0:
      regexCount[NO_WITNESS] += 1
      nWitnessTypes += 1
    else:
      regexCount[ANY_WITNESS] += 1
      nWitnessTypes += 1

    # Type of witness
    if regexHasMatchWitness(regex):
      regexCount[MATCH_WITNESS] += 1
      nWitnessTypes += 1
    if regexHasSubstringWitness(regex):
      regexCount[SUBSTRING_WITNESS] += 1
      nWitnessTypes += 1
    if regexHasCaptureWitness(regex):
      regexCount[CAPTURE_WITNESS] += 1
      nWitnessTypes += 1

    if nWitnessTypes == 0:
      raise ValueError("Error, did not find any witness types?? regex: {}".format(regex.toNDJSON()))
  return regexCount

def regexHasMatchWitness(regex):
  """Returns True if regex has a Match Witness among its witnesses

  Match witness: An input where two languages disagree about the existence of a match
  """
  # Check if any of the SDWs indicated a mismatch
  for sdw in regex.semanticDifferenceWitnesses:
    anyLangMatched = False
    anyLangMismatched = False

    for matchResult in sdw.matchResultToLangs:
      if matchResult.matched:
        anyLangMatched = True
      else:
        anyLangMismatched = True

    # Must have been at least one outcome!
    assert(anyLangMatched or anyLangMismatched)
    # If we found such an input, keep the regex
    if anyLangMatched and anyLangMismatched:
      #libLF.log("Match witness: {}".format(sdw.toNDJSON()))
      return True
  return False

def regexHasSubstringWitness(regex):
  """Returns True if regex has a Subtring Witness among its witnesses

  Substring witness: An input where
    - two languages agree on a match, but
    - disagree on the matching substring
  """
  # Check if any of the SDWs disagreed about the contents of a match
  for sdw in regex.semanticDifferenceWitnesses:
    # Did any two sets of languages find different substrings to match?
    uniqueMatchingSubstrings = set([
      mr.matchContents.matchedString
      for mr in sdw.matchResultToLangs
      if mr.matched
    ])
    if len(uniqueMatchingSubstrings) > 1:
      #libLF.log("Substring witness: {}".format(sdw.toNDJSON()))
      #libLF.log("  Unique matching substrings: {}".format(uniqueMatchingSubstrings))
      return True
  return False

def regexHasCaptureWitness(regex):
  """Returns True if regex has a Capture Witness among its witnesses

  Capture witness: An input where
    - some pair of languages agrees on a match and the matched substring, but
    - disagrees on the capture group contents
  """
  # Check if any of the SDWs disagreed about the capture groups for a match
  for sdw in regex.semanticDifferenceWitnesses:
    # Get the substrings matched
    uniqueMatchingSubstrings = set([
      mr.matchContents.matchedString
      for mr in sdw.matchResultToLangs
      if mr.matched
    ])
    #libLF.log("  uniqueMatchingSubstrings: {}".format(uniqueMatchingSubstrings))

    # For each substring, see if multiple capture groups were found
    for matchedString in uniqueMatchingSubstrings:
      distinctCaptureGroupsForString = [
        mr.matchContents.captureGroups
        for mr in sdw.matchResultToLangs
        if mr.matchContents.matchedString == matchedString
      ]
      if len(distinctCaptureGroupsForString) > 1:
        #libLF.log("  {} distinct capture groups for matchedString {}" \
        #  .format(len(distinctCaptureGroupsForString), matchedString))
        #libLF.log("Capture witness: {}".format(sdw.toNDJSON()))
        return True
  return False

################
# Analysis: Language disagreements
################

class AnalyzeLanguageDifferences:
  """Feed all regexes to one of these, then inspect langPair2witnessCounts"""
  def __init__(self, languages):
    self.languages = languages
    
    # Keyed by tuples returned by langs2pair: (lang1, lang2)
    # This way we don't count both A-B and B-A.
    self.langPair2witnessCounts = {}
    for lang1 in self.languages:
      for lang2 in self.languages:
        if lang1 == lang2:
          continue
        pair = self.langs2pair(lang1, lang2)
        self.langPair2witnessCounts[pair] = LanguagePairWitnessCounts(lang1, lang2)
  
  def analyzeRegexForLanguageDifferences(self, regex):
    # Only count a difference witness type between pairs once for each regex
    # Otherwise we may N-count it, once for each SDW in some (hypothesized)
    # equivalence class of inputs, e.g. "Misbehavior on any Unicode character".
    langPair_to_witnessTypesCountedForThisRegex = {}

    for sdw in regex.semanticDifferenceWitnesses:
      for mr1, langs1 in sdw.matchResultToLangs.items():
        # Compare the behavor of mr1 to the behavior of mr2
        # After identifying the witness type, update all of the pairs
        # by pairing mr1 langs with mr2 langs (so we count each pair once).
        for mr2, langs2 in sdw.matchResultToLangs.items():
          if mr1 is mr2:
            continue
          witnessType = self.identifyWitnessType(mr1, mr2)

          for langs1_lang in langs1:
            for langs2_lang in langs2:
              pair = self.langs2pair(nick2full(langs1_lang), nick2full(langs2_lang))

              # Initialize if we have not seen this language pair before
              if pair not in langPair_to_witnessTypesCountedForThisRegex:
                langPair_to_witnessTypesCountedForThisRegex[pair] = set()

              # Skip if we have already counted this witnessType for this language pair for this regex,
              if witnessType in langPair_to_witnessTypesCountedForThisRegex[pair]:
                continue

              # Note a new instance of this type of witness for this pair
              self.langPair2witnessCounts[pair].addWitness(witnessType)
              # Ensure we only mark this language pair once for this regex
              langPair_to_witnessTypesCountedForThisRegex[pair].add(witnessType)
  
  def identifyWitnessType(self, matchResult1, matchResult2):
    if matchResult1.matched != matchResult2.matched:
      return MATCH_WITNESS
    elif matchResult1.matched and matchResult2.matched:
      # Both agree on the existence of a match

      # Do they agree on the matched string?
      if matchResult1.matchContents.matchedString != matchResult2.matchContents.matchedString:
        return SUBSTRING_WITNESS
      else:
        # Yes they do. I hope the capture groups don't match...
        if matchResult1.matchContents.captureGroups == matchResult2.matchContents.captureGroups:
          libLF.log("mr1: {}".format(matchResult1.toNDJSON()))
          libLF.log("mr2: {}".format(matchResult2.toNDJSON()))
          raise ValueError("Error, mr1 and mr2 agree on matched, matchedString, and captureGroups. No witness!")
        return CAPTURE_WITNESS
    else:
      raise ValueError("Error, how can this be a difference witness? Neither matched!")
  
  def langs2pair(self, lang1, lang2):
    langList = sorted([lang1, lang2])
    return (langList[0], langList[1])

class LanguagePairWitnessCounts:
  def __init__(self, langA, langB):
    self.langA = langA
    self.langB = langB

    self.witnessType2count = {}
    for wt in WITNESS_TYPES:
      self.witnessType2count[wt] = 0
  
  def addWitness(self, witnessType):
    if witnessType == MATCH_WITNESS or \
      witnessType == SUBSTRING_WITNESS or \
      witnessType == CAPTURE_WITNESS:
      self.witnessType2count[witnessType] += 1
    else:
      raise ValueError("Error, unexpected witnessType '{}'".format(witnessType))
  
  def getNMatchWitnesses(self):
    return self.witnessType2count[MATCH_WITNESS]

  def getNSubstringWitnesses(self):
    return self.witnessType2count[SUBSTRING_WITNESS]

  def getNCaptureWitnesses(self):
    return self.witnessType2count[CAPTURE_WITNESS]
  
  def getNAllWitnesses(self):
    return self.getNMatchWitnesses() + \
            self.getNSubstringWitnesses() + \
            self.getNCaptureWitnesses()

#####################
# Report: Language pair disagreements
#####################

# See https://matplotlib.org/gallery/images_contours_and_fields/image_annotated_heatmap.html
def heatmap(data, row_labels, col_labels,
            fig=None, ax=None,
            cbar_kw={}, cbarlabel="", **kwargs):
    """
    Create a heatmap from a numpy array and two lists of labels.

    Arguments:
        data       : A 2D numpy array of shape (N,M)
        row_labels : A list or array of length N with the labels
                     for the rows
        col_labels : A list or array of length M with the labels
                     for the columns
    Optional arguments:
        ax         : A matplotlib.axes.Axes instance to which the heatmap
                     is plotted. If not provided, use current axes or
                     create a new one.
        cbar_kw    : A dictionary with arguments to
                     :meth:`matplotlib.Figure.colorbar`.
        cbarlabel  : The label for the colorbar
    All other arguments are directly passed on to the imshow call.
    """

    if not ax:
      ax = plt.gca()

    # Plot the heatmap
    im = ax.imshow(data, **kwargs)

    # Create colorbar
    cbar = ax.figure.colorbar(im, ax=ax, **cbar_kw)
    cbar.ax.set_ylabel(cbarlabel, rotation=-90, va="bottom")

    # We want to show all ticks...
    ax.set_xticks(np.arange(data.shape[1]))
    ax.set_yticks(np.arange(data.shape[0]))
    # ... and label them with the respective list entries.
    ax.set_xticklabels(col_labels)
    ax.set_yticklabels(row_labels)

    # Let the horizontal axes labeling appear on top.
    ax.tick_params(top=True, bottom=False,
                   labeltop=True, labelbottom=False)

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=-30, ha="right",
             rotation_mode="anchor")

    # Turn spines off and create white grid.
    for edge, spine in ax.spines.items():
      spine.set_visible(False)

    ax.set_xticks(np.arange(data.shape[1]+1)-.5, minor=True)
    ax.set_yticks(np.arange(data.shape[0]+1)-.5, minor=True)
    ax.grid(which="minor", color="w", linestyle='-', linewidth=10, axis='y') # Sep b/t rows
    ax.grid(which="minor", color="w", linestyle='-', linewidth=1, axis='x') # Sep b/t cols
    ax.tick_params(which="minor", bottom=False, left=False)

    for i, yminor in enumerate(ax.yaxis.get_minorticklocs()):
      if i == 0:
        continue
      ax.axhline(yminor, color="dimgrey", linewidth=1.5)
    #ax.grid(which="minor", color="k", linestyle='-', linewidth=10, axis='y') # Sep b/t rows

    return im, cbar

def annotate_heatmap(im, dataAnnot=None, valfmt="{x:.2f}",
                     textcolors=["black", "white"],
                     threshold=None, **textkw):
    """
    A function to annotate a heatmap.

    Arguments:
        im         : The AxesImage to be labeled.
    Optional arguments:
        data       : Data used to annotate. If None, the image's data is used.
        valfmt     : The format of the annotations inside the heatmap.
                     This should either use the string format method, e.g.
                     "$ {x:.2f}", or be a :class:`matplotlib.ticker.Formatter`.
        textcolors : A list or array of two color specifications. The first is
                     used for values below a threshold, the second for those
                     above.
        threshold  : Value in data units according to which the colors from
                     textcolors are applied. If None (the default) uses the
                     middle of the colormap as separation.


    Further arguments are passed on to the created text labels.
    """

    if not isinstance(dataAnnot, (list, np.ndarray)):
      dataAnnot = im.get_array()

    # Set default alignment to center, but allow it to be
    # overwritten by textkw.
    kw = dict(horizontalalignment="center",
              verticalalignment="center")
    kw.update(textkw)

    # Normalize the threshold to the images color range.
    dataPlotted = im.get_array()
    if threshold is not None:
      threshold = im.norm(threshold)
    else:
      threshold = im.norm(dataPlotted.max())/2.

    # Set default alignment to center, but allow it to be
    # overwritten by textkw.
    kw = dict(horizontalalignment="center",
              verticalalignment="center")
    kw.update(textkw)

    # Get the formatter in case a string is supplied
    if isinstance(valfmt, str):
      valfmt = matplotlib.ticker.StrMethodFormatter(valfmt)

    # Loop over the data and create a `Text` for each "pixel".
    # Change the text's color depending on the data.
    texts = []
    for i in range(dataAnnot.shape[0]):
      for j in range(dataAnnot.shape[1]):
        kw.update(color=textcolors[im.norm(dataPlotted[i, j]) > threshold])
        text = im.axes.text(j, i, valfmt(dataAnnot[i, j], None), fontsize=13, **kw)
        texts.append(text)

    return texts

def makeReport_languageDisagreements(allRegexes, visDir):
  # Analyze each regex
  analyzer = AnalyzeLanguageDifferences(allLangs())
  for regex in allRegexes:
    analyzer.analyzeRegexForLanguageDifferences(regex)
  
  # Print raw numbers in case we need those.
  formatStr = "%-45s %30s %30s %30s %30s"
  print(formatStr % ("Language pair",
                     "# regexes with ANY witnesses",
                     "# regexes with match witnesses",
                     "# regexes with substring witnesses",
                     "# regexes with capture witnesses",
  ))
  print(formatStr % ("-"*45, "-"*30, "-"*30, "-"*30, "-"*30))
  for pair in analyzer.langPair2witnessCounts:
    nMatchWitnesses = analyzer.langPair2witnessCounts[pair].getNMatchWitnesses()
    nSubstringWitnesses = analyzer.langPair2witnessCounts[pair].getNSubstringWitnesses()
    nCaptureWitnesses = analyzer.langPair2witnessCounts[pair].getNCaptureWitnesses()
    nWitnesses = nMatchWitnesses + nSubstringWitnesses + nCaptureWitnesses
    # Don't print boring stuff
    if nWitnesses == 0:
      continue
    print(formatStr % (
      str(pair),
      str(nWitnesses),
      str(nMatchWitnesses),
      str(nSubstringWitnesses),
      str(nCaptureWitnesses),
    ))
  
  ##
  # Visualize as a heatmap
  ##

  # Create a 2D array from the langPair2witnessCounts
  witnessCounts = {} # Sum of witnesses for each language
  labels = {} # Use labels (text in each cell) to provide more info -- breakdown by witness types as a PERCENTAGE of all regexes
  for lang1 in allLangs():
    witnessCounts[lang1] = {}
    labels[lang1] = {}

  labelsFmt = "{:.0f}% M\n{:.0f}% S\n{:.0f}% C"
  #labelsFmt = "{:.0f}{:.0f}{:.0f}"
  for lang1 in allLangs():
    for lang2 in allLangs():
      if lang1 == lang2:
        witnessCounts[lang1][lang2] = 0 # No disagreement possible within a language
        labels[lang1][lang2] = ""
      else:
        # Record the total score of this language pair
        pair = analyzer.langs2pair(lang1, lang2)
        witnessCounts[lang1][lang2] = analyzer.langPair2witnessCounts[pair].getNAllWitnesses()
        # A-B and B-A are the same
        witnessCounts[lang2][lang1] = witnessCounts[lang1][lang2] 

        labels[lang1][lang2] = labelsFmt \
          .format(100 * analyzer.langPair2witnessCounts[pair].getNMatchWitnesses() / len(allRegexes),
                  100 * analyzer.langPair2witnessCounts[pair].getNSubstringWitnesses() / len(allRegexes),
                  100 * analyzer.langPair2witnessCounts[pair].getNCaptureWitnesses() / len(allRegexes))
        labels[lang2][lang1] = labels[lang1][lang2] 

  # Data as ndarray for heatmap()
  # The plot is symmetric, so it doesn't matter which order we fill the array in
  witnessCounts_arr = np.empty((len(PLOT_LANG_ORDER), len(PLOT_LANG_ORDER)), dtype=float)
  labels_arr = np.empty((len(PLOT_LANG_ORDER), len(PLOT_LANG_ORDER)), dtype=object)
  for i, i_lang in enumerate(PLOT_LANG_ORDER):
    for j, j_lang in enumerate(PLOT_LANG_ORDER):
      witnessCounts_arr[i][j] = witnessCounts[i_lang][j_lang]
      labels_arr[i][j] = labels[i_lang][j_lang]
  
  print("Raw numbers")
  print('---------------')
  print('witnessCounts')
  print(witnessCounts_arr)
  print('---------------')
  print('labels')
  print(labels_arr)

  # Make the plot
  fig, ax = plt.subplots()
  fig.set_size_inches(11,8) # Make sure large numbers in cells show up OK

  im, cbar = heatmap(witnessCounts_arr, PLOT_LANG_ORDER, PLOT_LANG_ORDER,
               ax=ax,
               cmap='gray_r', cbarlabel='Sum of {M,S,C} witnesses')

  ax.set_title("Semantic differences", pad=75)
  ax.set_ylabel("Destination language", labelpad=0)

  texts = annotate_heatmap(im, dataAnnot=labels_arr, valfmt=lambda x, pos: x)
  plt.tight_layout()

  outFile = os.path.join(visDir, 'semantic-porting-heatmap.png')
  libLF.log('Saving plot to {}'.format(outFile))
  plt.savefig(outFile, bbox_inches='tight', pad_inches=0)

################
# Analysis: Explaining the cause of difference witnesses
################

class SDWExplainer:
  """These are heuristics, not perfect explanations.
  
  For example:
    - CAUSE_TRAILING_CAPTURE_GROUPS guesses about dropped capture groups
    - CAUSE_CARET_DOLLAR_LINE_ANCHORS guesses that anchors are the problem
  """
  # Are trailing capture groups defined (and converted by our tools to ""), or dropped? PHP.
  CAUSE_TRAILING_CAPTURE_GROUPS = "Trailing unused capture groups were dropped"
  # 1. Do ^ and $ apply per input or per line?
  # 2. In Ruby, Java, PHP, Perl, Python, $ also matches before a final line terminator, though
  #    the precise definition of "line terminator" varies between Java (\r) and the others (\n or \r\n).
  #    See also Oracle bug report 9059182 and https://bugs.openjdk.java.net/browse/JDK-8059325.
  # These are hard to differentiate via heuristic so I capture them together.
  CAUSE_CARET_DOLLAR_LINE_ANCHORS = "Anchor madness. Either ^/$ are per line, or $ matches before the final newline (or CR [Java], or CRLF?) character"
  # In Python, \s includes (undocumented?) \u001f (dec 31), i.e. the "unit separator" character.
  # This occurs when you use \x or \u but not chr(31) I think.
  # I guess this might really be interpreted as "different thresholds for entering Unicode mode"?
  CAUSE_WHITESPACE_CHARCLASS = "Whitespace character class definition varies" 
  # In Java, PHP, Go (, and Perl, ...?) , \Q...\E means "Quote between these". In others languages, \Q and \E in a regex are just Q and E.
  CAUSE_INNER_QUOTE_QE = "Different interpretations of \Q and \E as, respectively, Q and E or an internal quote directive" 
  # In Perl, PHP, Ruby, and Java, \G means something like "beginning of previous match in m//g mode".
  # In Python and JS, \G matches a literal G.
  CAUSE_POS_G = "Different interpretations of \G, as a literal G or as the begin-at-previous-match assertion" 
  # In everything but JavaScript, \A...\Z means ^ and $ for full string. In JS they are interpreted as regular chars, like \Q and \E.
  CAUSE_BOL_EOL_A_Z = "Different interpretations of \A and \Z as, respectively, A and Z or ^/$ (less possible trailing newline) for input" 
  # In everything but JavaScript and Python, \z means true end of string. In JS and Python it means a literal z.
  CAUSE_EOL_z = "Different interpretations of \z, respectively, z or the true end of line"
  # In JavaScript, \g is a literal.
  # In Perl, \g1, \g{1}, and \g{name} are both valid (as is \k<name>)
  # In Ruby, \g<name> and \g{1} are both valid.
  # In Python, (?P=name), and in the repl arg to re.sub \g<X> and \g<1> are also valid.
  # ...
  CAUSE_BACKREF_g = "Different interpretations of \g, respectively, g or a backreference notation"
  # In Perl, Ruby, and PHP, \K means "reset match start"
  CAUSE_MATCH_RESTART_K = "Different interpretations of \K, respectively, K or 'Reset match start'"
  # In everything but JavaScript and Python, \p denotes POSIX character classes.
  # In Ruby you can use \p{L} but not \pL; other languages permit this shorthand.
  CAUSE_UNICODE_PROPERTY_NOTATION = "Different interpretations of Unicode Properties, denoted \p{X} and \pL, as, respectively, the class or the literal p{X}"
  # PHP and Go and ...? support these
  CAUSE_POSIX_CHAR_CLASS_NOTATION = "Different interpretations of POSIX/ASCII character classes, denoted e.g. [[:space:]]"
  # Ruby: hex char
  # Perl, Java, etc.: horizontal whitespace
  # Others: literal whitespace
  CAUSE_ESCAPED_h = "Different interpretations of \h as, respectively, hex, horizontal space, or a literal h"
  # \x{...} is valid in Perl, PHP, Go, Rust, ... (but not Python or JS)
  CAUSE_HEX_WITH_BRACKETS = "Different interpretations of \\x{...} as a valid means of hex encoding"
  # JavaScript, Python, Rust, Go(?): literal
  # Others: Escape character (ESC)
  CAUSE_ESCAPED_e = "Different interpretations of \e as, respectively, escape or a literal e"
  # Python treats \cA as a literal c and a literal A. Similar to \Q\E.
  CAUSE_ESCC_FOR_CONTROL_CHAR = "Whether or not \cX indicates, respectively, control char X or just a literal c and a literal X"
  # In Rust, a backreference like \1 is interpreted as an octal escape for, e.g. \u0001, leading to supported regexes
  #   but with "alternative" match/mismatch behavior.
  # In all other languages this notation is permitted.
  CAUSE_RUST_BACKREFERENCES_AS_OCTAL = "In Rust, a backreference like \\1 is interpreted as an octal escape for, e.g. \\u0001"
  # Mixing named and unnamed groups in Ruby results in the loss (??) of the unnamed groups.
  # Ruby docs say: "Note: A regexp can't use named backreferences and numbered backreferences simultaneously."
  # This might be related.
  CAUSE_RUBY_MIX_NAMED_AND_UNNAMED_GROUPS = "Mixing named and unnamed groups in Ruby is strange. Possibly undefined behavior according to the docs." 
  # In every language but JS you can set/unset regex flags inline using e.g. (?i) [set] or (?-ms) [unset]
  # In Python the notation for *unset* is different from others
  CAUSE_INLINE_FLAGS = "Different interpretations of (?i...) -- is it inline regex flag notation?"

  # This actually is not a normal SDW but a Rust bug. See https://github.com/rust-lang/regex/issues/517#issuecomment-464271880.
  #   old: In Rust, \b matches the end of the string. In others it only matches at (non-empty) \w-\W boundaries.
  #   old: UPDATE: Looks like the distinction is more subtle than I thought.
  #CAUSE_BOUNDARY_CHAR_EOL = "Different interpretations of \\b: does it also match at the end of the input?"

  # Rust does not have possessive quantifiers
  CAUSE_POSSESSIVE_QUANTIFIERS = "Different interpretations of possessive quantifier constructs like ++, *+, ?+"
  # Ruby "mibehaves" on {n}?, interpreting the ? as optional instead of non-greedy.
  CAUSE_RUBY_OPTIONAL_QUANTIFIED = "Different interpretations of {n}? notation: is {n} non-greedy or optional?"
  # JS permits empty CCC though as far as I can tell they are impossible to satisfy.
  # Python tries hard not to have empty CCC: greedy acceptance of closing ] but only once the group is non-empty.
  # This means in Python []] is "CCC with ]" while [}]] is "CCC with }, followed by a ]".
  # Not sure if this is true --> Most (all?) other languages reject the regex as invalid -- fails syntax cehck
  CAUSE_EMPTY_CCC = "Disagreement on whether an empty CCC [] is permitted"
  # Disagreement between {Python, Ruby, PHP, Java, Perl} and {JS, Go, Rust} on ((a*)+), ((a*)*), and similar.
  CAUSE_QUANTIFIED_STAR = "Different interpretations of the ((*)+) and variant constructs with * inside"
  # Bug in PHP driver -- can't handle "/" in regex patterns.
  # TODO The new version is OK though, so these should go away.
  CAUSE_PHP_FORWARDSLASH_DRIVER_BUG = "ERROR: My driver doesn't work when a regex pattern contains a forward slash"
  # Bug in PHP driver -- doesn't notice too-large {} limit
  # TODO The new version is OK though, so these should go away.
  CAUSE_PHP_BIG_QUANTIFIER_DRIVER_BUG = "ERROR: My driver doesn't work when a regex pattern contains an over-large quantifier -- {,70000} or biger"

  # This is a catch-all. Not a cause, just a clue.
  CAUSE_NON_ASCII_INPUT = "The input contained non-ASCII character(s)"
  # This is a catch-all. Not a cause, just a clue.
  CAUSE_NON_ASCII_PATTERN = "The pattern contained non-ASCII character(s)"

  CAUSE_UNKNOWN = "Unknown"

  def __init__(self):
    # These are generally ordered in a mix of (more to less precise) aka (easy to hard)
    self.causesAndTesters = [
      # Embarrassing
      (SDWExplainer.CAUSE_PHP_FORWARDSLASH_DRIVER_BUG, self._isPHPForwardSlashDriverBug),
      (SDWExplainer.CAUSE_PHP_BIG_QUANTIFIER_DRIVER_BUG, self._isPHPBigQuantifierDriverBug),

      # Least precise
      (SDWExplainer.CAUSE_NON_ASCII_INPUT,            self._isNonAsciiInput),
      (SDWExplainer.CAUSE_NON_ASCII_PATTERN,          self._isNonAsciiPattern),

      # Pretty confident about these
      (SDWExplainer.CAUSE_TRAILING_CAPTURE_GROUPS,    self._isTrailingCaptureGroups),
      #(SDWExplainer.CAUSE_WHITESPACE_CHARCLASS,       self._isWhitespaceCharClass),
      (SDWExplainer.CAUSE_INNER_QUOTE_QE,             self._isInnerQuoteQE),
      (SDWExplainer.CAUSE_POS_G,                      self._isPOS_G),
      (SDWExplainer.CAUSE_BOL_EOL_A_Z,                self._isBOL_EOL_AZ),
      (SDWExplainer.CAUSE_EOL_z,                      self._isEOL_z),
      (SDWExplainer.CAUSE_BACKREF_g ,                 self._isBackref_g),
      (SDWExplainer.CAUSE_MATCH_RESTART_K,            self._isMatchRestart_K),
      (SDWExplainer.CAUSE_UNICODE_PROPERTY_NOTATION,  self._isUnicodePropertyNotation),
      (SDWExplainer.CAUSE_POSIX_CHAR_CLASS_NOTATION,  self._isPosixCharClassNotation),
      (SDWExplainer.CAUSE_ESCAPED_h,                  self._isEscapedH),
      (SDWExplainer.CAUSE_HEX_WITH_BRACKETS,          self._isHexWithBrackets),
      (SDWExplainer.CAUSE_ESCAPED_e,                  self._isEscapedE),
      (SDWExplainer.CAUSE_ESCC_FOR_CONTROL_CHAR,      self._isControlChar),
      (SDWExplainer.CAUSE_RUST_BACKREFERENCES_AS_OCTAL, self._isRustBackreference),
      (SDWExplainer.CAUSE_RUBY_MIX_NAMED_AND_UNNAMED_GROUPS,  self._isRubyMixedNamedAndUnnamedGroups),
      (SDWExplainer.CAUSE_INLINE_FLAGS,          self._isInlineFlags),
      (SDWExplainer.CAUSE_POSSESSIVE_QUANTIFIERS,     self._isPossessiveQuantifiers),
      (SDWExplainer.CAUSE_RUBY_OPTIONAL_QUANTIFIED,   self._isRubyOptionalQuantified),
      (SDWExplainer.CAUSE_EMPTY_CCC,                  self._isEmptyCCC),
      (SDWExplainer.CAUSE_CARET_DOLLAR_LINE_ANCHORS,  self._isCaretDollarLineAnchors),
      (SDWExplainer.CAUSE_QUANTIFIED_STAR,            self._isQuantifiedStar),
    ]

    self.cause2count = {
      SDWExplainer.CAUSE_UNKNOWN: 0
    }
    for cause, _ in self.causesAndTesters:
      self.cause2count[cause] = 0
  
  def explainSDW(self, sdw, mr1, mr2):
    """Explain why mr1 and mr2 differ. Returns one of SDWExplainer.CAUSES

    sdw: SemanticDifferenceWitness
    mr1: MatchResult
    mr2: MatchResult
    """
    libLF.log("explainSDW:\n  sdw: {}\n  mr1 (langs {}): {}\n  mr2 (langs {}): {}" \
      .format(sdw.toNDJSON(),
              sdw.matchResultToLangs[mr1], mr1.toNDJSON(),
              sdw.matchResultToLangs[mr2], mr2.toNDJSON(),
              ))

    # Evaluate these in order since there are some catch-alls at the bottom
    cause = SDWExplainer.CAUSE_UNKNOWN
    for _cause, tester in self.causesAndTesters:
      try:
        if tester(sdw, mr1, mr2):
          cause = _cause
          break
      except Exception as e:
        # Bug in some explainer. NBD.
        libLF.log("Explainer bug on /{}/: {}".format(sdw.pattern, e))
        traceback.print_exc()

    libLF.log("explainSDW: cause: {}".format(cause))
    self.cause2count[cause] += 1
    return cause
  
  def _isCaretDollarLineAnchors(self, sdw, mr1, mr2):
    # Pattern must have ^ or $
    # Must have a newline to trigger the line anchor vs. string anchor question
    # Likely has one match and the other not, though TODO alternative arrangements are possible I guess
    if ("^" in sdw.pattern or "$" in sdw.pattern) and \
        ("\r" in sdw.input or "\n" in sdw.input) and \
        (mr1.matched ^ mr2.matched or ("java" in sdw.matchResultToLangs[mr1] or "java" in sdw.matchResultToLangs[mr2])):
      return True
    return False
  
  def _isWhitespaceCharClass(self, sdw, mr1, mr2):
    whitespaceCharClasses = ["\\s", "\\S"] # Gation and Negation both affect this
    unexpectedWhitespaceChars = [
      "\u001c", "\u001d", "\u001e", "\u001f" # ASCII 28-31: file/group/record/unit separator
    ]
    for lang in ["python"]:
      if lang in sdw.matchResultToLangs[mr1] or lang in sdw.matchResultToLangs[mr2]:
        for charClass in whitespaceCharClasses:
          # See if this charClass is in the pattern
          if charClass in sdw.pattern:
            # See if any of the "unexpected" whitespace chars is in the input
            if any(wsc in sdw.input for wsc in unexpectedWhitespaceChars):
              return True
    return False

  def _isHexWithBrackets(self, sdw, mr1, mr2):
    return re.search(r"\\x\{[a-fA-F0-9]+\}", sdw.pattern) is not None
  
  def _jsonStringAsTrueString(self, string):
    if re.search(r"\\u(?:\d{2}|\d{4})", string):
      return bytes(string, "utf-8").decode("unicode_escape")
    else:
      return string
  
  def _isAsciiString(self, string):
    try:
      # If this throws, it cannot be encoded as ASCII
      string.encode("ascii", errors="strict")
      return True
    except UnicodeEncodeError as err:
      return False

  def _looksLikeUnicodeAsJson(self, string):
    # Convert to JSON and see if there are unicode characters
    return re.search(r"\\u\{?[a-fA-F0-9]{2,6}", json.dumps(string)) is not None # Rust supports 2-char version

  def _isNonAsciiInput(self, sdw, mr1, mr2):
    libLF.log("input: <{}>".format(sdw.input))
    return self._looksLikeUnicodeAsJson(sdw.input)

    # The sdw.input is a JSON-style string that may contain e.g. "\u1234" as [slash, u, 1, 2, 3, 4]
    # This is because of the I/O format for libLF.Regex, which converts the SDW to/from a string.
    # It should contain no literal unicode characters, so unicode_escape should be well-behaved.
    try:
      unescapedString = self._jsonStringAsTrueString(sdw.input)
      libLF.log("unescapedString : <{}>".format(unescapedString))
      isAscii = self._isAsciiString(unescapedString)
      return not isAscii
    except (UnicodeDecodeError, UnicodeEncodeError) as err:
      # Presumably failures would occur because of non-ASCII stuff
      return True

  def _isNonAsciiPattern(self, sdw, mr1, mr2):
    libLF.log("pattern: <{}>".format(sdw.pattern))
    return self._looksLikeUnicodeAsJson(sdw.pattern)

    # The sdw.input is a JSON-style string that may contain e.g. "\u1234" as [slash, u, 1, 2, 3, 4]
    # This is because of the I/O format for libLF.Regex, which converts the SDW to/from a string.
    # It should contain no literal unicode characters, so unicode_escape should be well-behaved.
    try:
      unescapedString = self._jsonStringAsTrueString(sdw.pattern)
      libLF.log("unescapedString : <{}>".format(unescapedString))

      isAscii = self._isAsciiString(unescapedString)
      return not isAscii
    except (UnicodeDecodeError, UnicodeEncodeError) as err:
      # Presumably failures would occur because of non-ASCII stuff
      return True
  
  def _hasEscapedPat(self, haystack, needle):
    """Find ESCAPED needle, e.g. "Q" -> "\Q" but not "\\Q" (escaped \ and then a literal Q)"""
    # Either preceded by an even number of escaped backslashes, or
    # preceded by NO backslash
    pat = r"((\\\\)*|(?<!\\))\\" + needle
    return re.search(pat, haystack) is not None

  def _isInnerQuoteQE(self, sdw, mr1, mr2):
    # The effect of \Q \E differences are match vs. mismatch
    # The Perl language driver has problems with \Q and \E (but not other directives like \A and \Z?),
		# so if ONLY perl complains than disqualify this as a witness. 
    return re.search(r"((\\\\)*|(?<!\\))\\Q.*((\\\\)*|(?<!\\))\\E", sdw.pattern) is not None \
      and mr1.matched ^ mr2.matched and \
			(sdw.matchResultToLangs[mr1] != ["Perl"] and sdw.matchResultToLangs[mr2] != ["Perl"])

  def _isPOS_G(self, sdw, mr1, mr2):
    for literalGLang in ["python", "javascript"]:
      if literalGLang in sdw.matchResultToLangs[mr1] or literalGLang in sdw.matchResultToLangs[mr2]:
        return self._hasEscapedPat(sdw.pattern, "G")

  def _isRubyMixedNamedAndUnnamedGroups(self, sdw, mr1, mr2):
    if "ruby" in sdw.matchResultToLangs[mr1] or "ruby" in sdw.matchResultToLangs[mr2]:
      hasNamedGroup = False
      hasUnnamedGroup = False

      escaped = False
      cccDepth = 0
      for i, c in enumerate(sdw.pattern):
        # Identify escaping
        if c == "\\":
          escaped = True
          continue
        # Ignore escaped chars
        if escaped:
          escaped = False
          continue

        # Looking for (), but these have different meaning inside Custom Char Classes -- []'s
        if c == "[":
          cccDepth += 1
          continue
        if cccDepth > 0 and c == "]":
          cccDepth -= 1
          continue

        if c == "(":
          remainderOfPattern = sdw.pattern[i+1:]
          # Non-capturing group: (?:...)
          if re.search(r"^\?:", remainderOfPattern):
            pass
          # Named group notation in Ruby: (?<name>...) or (?'name'...)
          elif re.search(r"^\?((<\w+>)|('\w+'))", remainderOfPattern):
            hasNamedGroup = True
          # Otherwise we must have a named group
          else:
            hasUnnamedGroup = True
      return hasNamedGroup and hasUnnamedGroup
    return False

  def _isBOL_EOL_AZ(self, sdw, mr1, mr2):
    # \A and \Z differences manifest in JS
    for literalAZLang in ["javascript"]:
      if literalAZLang in sdw.matchResultToLangs[mr1] or literalAZLang in sdw.matchResultToLangs[mr2]:
        return self._hasEscapedPat(sdw.pattern, r"(A|Z)")
          
    return False

  def _isEOL_z(self, sdw, mr1, mr2):
    # \z differences manifest in Python and JS
    for literal_z_Lang in ["javascript", "python"]:
      if literal_z_Lang in sdw.matchResultToLangs[mr1] or literal_z_Lang in sdw.matchResultToLangs[mr2]:
        return self._hasEscapedPat(sdw.pattern, "z")
    return False

  def _isBackref_g(self, sdw, mr1, mr2):
    # \g differences manifest in many places with many forms: \g1 ,\g'name', \g{...}, \g<...>
    # \k is an alternative in Perl and PHP, though I'm not sure whether it's used in our corpus.
    # Add it if I ever see it used.
    # I anticipate these will only manifest when there is a mismatch, so add that to be conservative.
    if mr1.matched ^ mr2.matched:
      return re.search(r"""((\\\\)*|(?<!\\))\\g[{<'"\d]""", sdw.pattern) is not None
    return False

  def _isMatchRestart_K(self, sdw, mr1, mr2):
    # \K is treated specially in Ruby, Perl, and PHP: Restart match mid-way.
    # I anticipate these will only manifest when there is a mismatch, so add that to be conservative.
    if mr1.matched ^ mr2.matched:
      for reset_k_lang in ["ruby", "perl", "php"]:
        if reset_k_lang in sdw.matchResultToLangs[mr1] or reset_k_lang in sdw.matchResultToLangs[mr2]:
          return self._hasEscapedPat(sdw.pattern, "K")
    return False

  def _isUnicodePropertyNotation(self, sdw, mr1, mr2):
    # \p differences manifest against Python and JS (no \p support) and Ruby (\p{...} but not \pL shorthand
    for literal_p_Lang in ["javascript", "python", "ruby"]:
      if literal_p_Lang in sdw.matchResultToLangs[mr1] or literal_p_Lang in sdw.matchResultToLangs[mr2]:
        return re.search(r"((\\\\)*|(?<!\\))\\[pP]([A-Z]|\{.+\})", sdw.pattern) is not None
    return False

  def _isPosixCharClassNotation(self, sdw, mr1, mr2):
    # Some languages support [[:posix:]], others do not
    return re.search(r"\[.*\[:\w+:\].*\]", sdw.pattern) is not None

  def _isEscapedH(self, sdw, mr1, mr2):
    # \h differences manifest between Python, JS, and Ruby
    for literal_h_Lang in ["javascript", "python"]:
      if literal_h_Lang in sdw.matchResultToLangs[mr1] or literal_h_Lang in sdw.matchResultToLangs[mr2]:
        return self._hasEscapedPat(sdw.pattern, "h")

    for whitespace_lang in ["perl", "java"]:
      if whitespace_lang in sdw.matchResultToLangs[mr1] or whitespace_lang in sdw.matchResultToLangs[mr2]:
        return self._hasEscapedPat(sdw.pattern, "h")

    for hex_lang in ["ruby"]:
      if hex_lang in sdw.matchResultToLangs[mr1] or hex_lang in sdw.matchResultToLangs[mr2]:
        return self._hasEscapedPat(sdw.pattern, "h")
    
    # Hmm, not sure what else might happen here.
    return False

  def _isEscapedE(self, sdw, mr1, mr2):
    # \e differences manifest between Python, JS, Rust, Go, and the others
    for literal_e_Lang in ["javascript", "python", "rust", "go"]:
      if literal_e_Lang in sdw.matchResultToLangs[mr1] or literal_e_Lang in sdw.matchResultToLangs[mr2]:
        return self._hasEscapedPat(sdw.pattern, "e")
    
    return False

  def _isRustBackreference(self, sdw, mr1, mr2):
    # Backrefernce (\1, \2, etc.) differences manifest in Rust
    for lang in ["rust"]:
      if lang in sdw.matchResultToLangs[mr1] or lang in sdw.matchResultToLangs[mr2]:
        return self._hasEscapedPat(sdw.pattern, r"\d")
    return False

  def _isControlChar(self, sdw, mr1, mr2):
    # \c differences manifest in Python
    for literal_c_Lang in ["python"]:
      if literal_c_Lang in sdw.matchResultToLangs[mr1] or literal_c_Lang in sdw.matchResultToLangs[mr2]:
        return self._hasEscapedPat(sdw.pattern, r"c[a-zA-Z]")
    return False

  def _isInlineFlags(self, sdw, mr1, mr2):
    # Most languages permit some form of inline flags: (?FLAGS), where each flag may be preceded by - to unset it
    # e.g. in Rust the valid flags are: i m s U u x
    # - JS does not support this notation.
    # - Python does not support the "unset" version.
    for lang in ["javascript", "python"]:
      if lang in sdw.matchResultToLangs[mr1] or lang in sdw.matchResultToLangs[mr2]:
        return re.search(r"\(\?[-imsUux]+.*\)", sdw.pattern) is not None
    return False

  def _isPossessiveQuantifiers(self, sdw, mr1, mr2):
    # Rust does not have possessive quantifiers
    for rust in ["rust"]:
      if sdw.matchResultToLangs[mr1] == [rust] or sdw.matchResultToLangs[mr2] == [rust]:
        return re.search(r"[+*?]\+", sdw.pattern) is not None
    return False
  
  def _isRubyOptionalQuantified(self, sdw, mr1, mr2):
    # Ruby handles {n}? differently from other languages
    for ruby in ["ruby"]:
      if sdw.matchResultToLangs[mr1] == [ruby] or sdw.matchResultToLangs[mr2] == [ruby]:
        return re.search(r"\{\d+\}\?", sdw.pattern) is not None
    return False

  def _isEmptyCCC(self, sdw, mr1, mr2):
    # JS permits empty [], others do not
    for lang in ["javascript"]:
      if lang in sdw.matchResultToLangs[mr1] or lang in sdw.matchResultToLangs[mr2]:
        return re.search(r"\[\]", sdw.pattern) is not None
    return False

#  def _isReluctantQuantifiers(self, sdw, mr1, mr2):
#    # Rust does not seem to have reluctant (non-greedy) quantifers like others do
#    for lang in ["rust"]:
#      if sdw.matchResultToLangs[mr1] == [lang] or sdw.matchResultToLangs[mr2] == [lang]:
#        return re.search(r"[+*?]\?", sdw.pattern) is not None
#    return False

  def _isPHPBigQuantifierDriverBug(self, sdw, mr1, mr2):
    # Problems with {...,HUGE_NUMBER} should manifest ONLY in my PHP driver
    ROUGH_PHP_LIMIT = 70000 # PHP is OK at 65K and complains at 70K
    if sdw.matchResultToLangs[mr1] == ["php"] or sdw.matchResultToLangs[mr2] == ["php"]:
      for match in re.finditer(r"\{(?:\d+)?,(\d+)\}", sdw.pattern):
        if int(match.group(1)) > ROUGH_PHP_LIMIT:
          return True
    return False

  def _isPHPForwardSlashDriverBug(self, sdw, mr1, mr2):
    # Problems with / should manifest ONLY in my PHP driver
    if sdw.matchResultToLangs[mr1] == ["php"] or sdw.matchResultToLangs[mr2] == ["php"]:
      return re.search(r"/", sdw.pattern) is not None
    return False
  
  def _isQuantifiedStar(self, sdw, mr1, mr2):
    libLF.log("_isQuantifiedStar: pattern /{}/".format(sdw.pattern))
    # The (*)+ difference (usually) manifests as missing or different-sized capture witnesses.
    if (mr1.matched and mr2.matched) and \
        (mr1.matchContents.matchedString == mr2.matchContents.matchedString):
      # Does the pattern contain a quantified star? (*)+, (*)*, (*){5}, ((a*))+, ((a*)bc)?, etc.

      hasQuantifiedStar = False # Success flag
      quantifierChars = ["*", "+", "?", "{"]
      escaped = False # For handling escape chars
      cccDepth = 0
      subPattern = "" # Debugging
      # Stack of Booleans: When we close a group with a star, check if the group itself was quantified.
      # Any * colors all groups below it: ((a*))+ counts too.
      groupHasStar = []

      for i, c in enumerate(sdw.pattern):
        #libLF.log(c)
        subPattern += c

        # Identify escaping
        if c == "\\":
          escaped = True
          continue
        # Ignore escaped chars
        if escaped:
          escaped = False
          continue

        # Looking for (), but these have different meaning inside Custom Char Classes -- []'s
        if c == "[":
          cccDepth += 1
          continue
        if cccDepth > 0 and c == "]":
          cccDepth -= 1
          continue

        if cccDepth == 0:
          if c == "(":
            groupHasStar.append(False)
          elif c == ")":
            # We are closing a group. If the group had a star and the newly-closed group is quantified, the condition is met.
            if (len(groupHasStar) and groupHasStar[-1]) \
               and i + 1 < len(sdw.pattern) and sdw.pattern[i+1] in quantifierChars:
              libLF.log("Has nested quantifier! subpattern /{}/".format(subPattern + sdw.pattern[i+1]))
              hasQuantifiedStar = True
              break
            # RIP group
            groupHasStar.pop()

          if c == "*" and len(groupHasStar) > 0:
            # Color this and all groups below
            groupHasStar = [True for x in groupHasStar]
      return hasQuantifiedStar
    return False
  
  def _isTrailingCaptureGroups(self, sdw, mr1, mr2):
    # Both must match and agree on the matched substring
    if (mr1.matched and mr2.matched) and \
        (mr1.matchContents.matchedString == mr2.matchContents.matchedString):
      # Must be different-length capture groups
      if len(mr1.matchContents.captureGroups) != len(mr2.matchContents.captureGroups):
        if len(mr1.matchContents.captureGroups) < len(mr2.matchContents.captureGroups):
          shorterCGs = mr1.matchContents.captureGroups 
          longerCGs = mr2.matchContents.captureGroups 
        else:
          shorterCGs = mr2.matchContents.captureGroups 
          longerCGs = mr1.matchContents.captureGroups 
        
        # Must agree up until the shorter one runs out
        for cg_shorter, cg_longer in zip(shorterCGs, longerCGs):
          if cg_shorter != cg_longer:
            return False

        # The longer one must contain only empty strings after that
        for i in range(len(shorterCGs) + 1, len(longerCGs)):
          if longerCGs[i] != "":
            return False
        
        return True
    return False

def makeReport_causeOfDisagreements(allRegexes, visDir):
  regexAndUnexplainedWitnesses = [] # [(regex, sdw[]), ...]

  sdwExplainer = SDWExplainer()
  nRegexesWithAnyWitnesses = 0
  for regex in allRegexes:
    if len(regex.semanticDifferenceWitnesses) == 0:
      continue

    nRegexesWithAnyWitnesses += 1
    libLF.log("Evaluating the {} witnesses for /{}/".format(len(regex.semanticDifferenceWitnesses), regex.pattern))
    unexplainedWitnesses = []
    for sdw in regex.semanticDifferenceWitnesses:
      unexplained = False
      for mrPair in itertools.combinations(sdw.matchResultToLangs.keys(), 2):
        cause = sdwExplainer.explainSDW(sdw, mrPair[0], mrPair[1])
        if cause == SDWExplainer.CAUSE_UNKNOWN:
          unexplained = True
      if unexplained:
        # Note that this may include explained pairs as well...
        unexplainedWitnesses.append(sdw)
    
    if len(unexplainedWitnesses):
      libLF.log("Failed to explain at least one MatchPair for {}/{} witnesses for /{}/" \
          .format(len(unexplainedWitnesses), len(regex.semanticDifferenceWitnesses), sdw.pattern))
      regexAndUnexplainedWitnesses.append((regex, unexplainedWitnesses))
  
  libLF.log("Causes:")
  libLF.log(sdwExplainer.cause2count)
  print("Causes")
  print(json.dumps(sdwExplainer.cause2count, sort_keys=True, indent=4, separators=(",", ": ")))

  # Emit unexplained witnesses for ease of iteration
  libLF.log("Could not explain some witness for {}/{} of the regexes with any witnesses" \
    .format(len(regexAndUnexplainedWitnesses), nRegexesWithAnyWitnesses))
  for regex, unexplainedWitnesses in regexAndUnexplainedWitnesses:
    libLF.log("\n\n-----------------------\n")
    libLF.log("{} unexplained witnesses for regex: /{}/".format(len(unexplainedWitnesses), regex.pattern))
    for sdw in unexplainedWitnesses:
      libLF.log("  Witness input: <{}>".format(sdw.input))
      libLF.log("  Full witness: {}".format(sdw.toNDJSON()))

  return regexAndUnexplainedWitnesses

################

def main(regexFile, outFileRWW, outFileUnknownRWW, visDir):
  libLF.log("regexFile {} outFileRWW {} outFileUnknownRWW {} visDir {}" \
    .format(regexFile, outFileRWW, outFileUnknownRWW, visDir))

  #### Load data
  allRegexes = loadRegexFile(regexFile)
  libLF.log('{} regexes in total'.format(len(allRegexes)))

  #### Analyses

  libLF.log('\n\n')
  libLF.log('Report: Distribution of the number of inputs')
  makeReport_distributionOfInputs(allRegexes)

  libLF.log('\n\n')
  libLF.log('Report: Description of witnesses')
  makeReport_classifyWitnesses(allRegexes)

  libLF.log('\n\n')
  libLF.log('Report: Description of language disagreements')
  makeReport_languageDisagreements(allRegexes, visDir)

  if True:
    libLF.log('\n\n')
    libLF.log('Report: Causes of language disagreements')
    makeReport_causeOfDisagreements(allRegexes, visDir)

  #### Output

  # TODO During the second phase of analysis.
  if False:
    libLF.log("Writing out ALL {} regexes with witnesses to {}".format(len(allRWWs), outFileRWW))
    libLF.writeToFileNDJSON(outFileRWW, allRWWs)

    libLF.log("Writing out the {} UNKNOWN regexes with witnesses to {}".format(len(allRWWs), outFileUnknownRWW))
    libLF.writeToFileNDJSON(outFileUnknownRWW, unknownRWWs)

#####################################################

# Parse args
parser = argparse.ArgumentParser(description='Analyze the results of testing a bunch of libLF.Regex\'s for semantic behavior')
parser.add_argument('--regex-file', type=str, help='In: File of libLF.Regex objects after applying test-for-semantic-portability.py', required=True,
  dest='regexFile')
# TODO During the second phase of analysis.
if False:
  parser.add_argument('--out-file-regexes-with-witnesses', help='Out: Where to put the file of all libLF.Regex objects with witnesses?', required=True,
    dest='outFileRWW')
  parser.add_argument('--out-file-unknown-regexes-with-witnesses', help='Out: Where to put the file of libLF.Regex objects whose witnesses we do not yet understand?', required=True,
    dest='outFileUnknownRWW')
parser.add_argument('--vis-dir', help='Out: Where to save plots?', required=False, default='/tmp/vis',
  dest='visDir')
args = parser.parse_args()

# Here we go!
#main(args.regexFile, args.outFileRWW, args.outFileUnknownRWW, args.visDir)
main(args.regexFile, None, None, args.visDir)
