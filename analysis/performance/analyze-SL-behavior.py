#!/usr/bin/env python3
# Analyze the results of testing a bunch of libLF.Regex's for SL behavior.

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

from matplotlib.colors import LinearSegmentedColormap

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

def nick2full(lang):
  return lcLang2lang[lang]

def allRegistries():
  return sorted(reg2lang.keys())

def allSLTestLanguages():
  return sorted(reg2lang.values())

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

# Ordered by module counts at time of study, most to least
PLOT_LANG_ORDER = ["JavaScript", "Java", "PHP", "Python", "Ruby", "Go", "Perl", "Rust"]

def langsInPlotOrder(langs):
  ret = []
  for lang in PLOT_LANG_ORDER:
    if lang in langs:
      ret.append(lang)
  return ret

################
# Ingest: Loading a file of libFL.SLRA's
################

def loadSLRAFile(slraFile):
  """Return a list of libLF.SLRegexAnalysis's"""
  slras = []
  libLF.log('Loading regexes from {}'.format(slraFile))
  nLines = 0
  with open(slraFile, 'r') as inStream:
    for line in inStream:
      nLines += 1
      if nLines % 10000 == 0:
        libLF.log('  Processed {} lines'.format(nLines))
      line = line.strip()
      if len(line) == 0:
        continue
      
      try:
        # Build an SLRA
        slra = libLF.SLRegexAnalysis()
        slra.initFromNDJSON(line)

        slras.append(slra)
      except KeyboardInterrupt:
        raise
      except BaseException as err:
        libLF.log('Exception parsing line:\n  {}\n  {}'.format(line, err))
        traceback.print_exc()

    libLF.log('Loaded {} slras from {}'.format(len(slras), slraFile))
    return slras

def getTimedOutSet(slras):
  return set(
    filter(lambda slra: slra.everTimedOut(),
           slras)
    )

def getCrossRegistrySet(slras):
  return set(
    filter(lambda slra: len(slra.regex.registriesUsedIn()) > 1,
           slras)
    )

def makeReport_detectorEffectiveness(allSLRAs):
  print("\nReport: Detector effectiveness\n")

  # Count the number of "is vulnerable" reports per detector
  # Ignore false positives, let's just see the ballpark # of reports.
  detector2nReports = {}
  for slra in allSLRAs:
    for do in slra.detectorOpinions:
      if not do.timedOut and do.canAnalyze and do.isVuln: 
        if do.detectorName not in detector2nReports:
          detector2nReports[do.detectorName] = 0
        detector2nReports[do.detectorName] += 1

  formatStr = "%30s %30s"
  print(formatStr % ("Detector", "Num reported vulnerabilities"))
  print(formatStr % ("-"*30, "-"*30))
  for detectorName, numReports in detector2nReports.items():
    print(formatStr % (detectorName, str(numReports)))

def makeReport_variantEffectiveness(allSLRAs):
  print("\nReport: Variant effectiveness\n")

  # Count the number of regexes for which the original is not vulnerable
  # and some variant is vulnerable.
  # Ignore false positives, let's just see the ballpark # of reports.
  ORIG_VULN_VARIANT_NOTVULN = 'orig vuln, no variant vuln'
  ORIG_VULN_VARIANT_VULN = 'orig vuln, some variant vuln'
  ORIG_NOTVULN_VARIANT_VULN = 'orig not vuln, some variant vuln' # < -- This is the exciting on
  ORIG_NOTVULN_VARIANT_NOTVULN = 'orig not vuln, no variant vuln'
  case2nReports = { # lists: (countReported, countActuallyVulnInJS)
    ORIG_VULN_VARIANT_NOTVULN: [0, 0],
    ORIG_VULN_VARIANT_VULN: [0, 0],
    ORIG_NOTVULN_VARIANT_VULN: [0, 0],
    ORIG_NOTVULN_VARIANT_NOTVULN: [0, 0],
  }

  for slra in allSLRAs:
    # Aggregate across all detectors
    origReportedVuln = False
    someVariantReportedVuln = False
    regexActuallyVulnInJavaScript = False
    for do in slra.detectorOpinions:
      if not do.timedOut and do.canAnalyze:
        if do.isVuln: 
          if do.patternVariant == slra.regex.pattern:
            # detector said original is vulnerable
            origReportedVuln = True
          else:
            # detector said variant is vulnerable
            someVariantReportedVuln = True
    if slra.predictedPerformanceInLang("JavaScript") == libLF.SLRegexAnalysis.PREDICTED_PERFORMANCE['POW'] or \
       slra.predictedPerformanceInLang("JavaScript") == libLF.SLRegexAnalysis.PREDICTED_PERFORMANCE['EXP']:
      regexActuallyVulnInJavaScript = True

    reportType = None
    if origReportedVuln and someVariantReportedVuln:
      reportType = ORIG_VULN_VARIANT_VULN
    elif origReportedVuln and not someVariantReportedVuln:
      reportType = ORIG_VULN_VARIANT_NOTVULN
    elif not origReportedVuln and someVariantReportedVuln:
      reportType = ORIG_NOTVULN_VARIANT_VULN
    elif not origReportedVuln and not someVariantReportedVuln:
      reportType = ORIG_NOTVULN_VARIANT_NOTVULN

    case2nReports[reportType][0] += 1
    if regexActuallyVulnInJavaScript:
      case2nReports[reportType][1] += 1

  formatStr = "%45s %30s %35s"
  print(formatStr % ("Case", "Num reported vulnerabilities", "Num actual vulnerabilities in JS"))
  print(formatStr % ("-"*45, "-"*30, "-"*35))
  for case, report in case2nReports.items():
    nPredicted, nVulnInJS = report
    print(formatStr % (case, str(nPredicted), "{} ({:.0f}%)".format(nVulnInJS, 100*nVulnInJS/nPredicted)))

def makeReport_perRegistryTimeouts(allSLRAs, visDir):
  print('\nReport: per registry timeouts\n')
  ###
  # Table
  ###

  registry2slras = {} # { 'npm' -> set(slras for regexes that appeared in npm), ... }
  for slra in allSLRAs:
    for registry in slra.regex.registriesUsedIn():
      if registry not in registry2slras:
        registry2slras[registry] = set()
      registry2slras[registry].add(slra)
  
  registries = set()
  for slra in allSLRAs:
    registries |= set(slra.regex.registriesUsedIn())
  libLF.log(registries)
  

  tableFormat = '%15s %20s %20s %20s'
  print('------------------\n\nTimeouts for regexes in the languages they were actually used in\n\n-----------------')
  print(tableFormat % ('Language', 'Total regexes', 'Num timed out', 'Percent timed out'))
  print(tableFormat % ('-'*15, '-'*20, '-'*20, '-'*20))
  for registry in sorted(registries):
    # Find those that timed out *in this registry*
    registry_timedOut = set(filter(
      lambda slra: slra.timedOutInLang((registryToSLTestLanguage(registry))),
      registry2slras[registry]
    ))
    percTimedOut = int(100 * len(registry_timedOut) / len(registry2slras[registry]))
    print(tableFormat %
      (registryToSLTestLanguage(registry), len(registry2slras[registry]), len(registry_timedOut), percTimedOut))

  ###
  # Grouped barplots: Proportion of each type by language
  ###
  cols =  {
    "Pattern": "pat",
    "Language": "lang",
    "Predicted performance": "Predicted performance",
    "Count": "Count",
    "Proportion": "Proportion",
    "Percentage": "Percentage"
  }

  # Make two plots:
  #   1. Performance in languages the regexes were actually used in
  #      This tells us about the distribution of regex performance
  #      in each registry and allows comparison to the FSE'18 work.
  #
  #   2. Performance across all languages ("what if?").
  #      This tells us about the potential for performance porting problems.
  pred2pretty = { 'EXP': 'Exponential', 'POW': 'Polynomial', 'LIN': 'Linear' }
  plotInfos = [
    { 'title': '"Real" regex performance',
      'outFile': os.path.join(visDir, 'SL-type-proportion-real.png'),
      'df': pd.DataFrame.from_records(
              data=[ (slra.regex.pattern, nick2full(lang), pred2pretty[slra.predictedPerformanceInLang(lang)])
                    for slra in allSLRAs
                    for lang in slra.lang_pump2timedOut.keys()
                    # Restrict to the languages of the registries that the regex actually appeared in.
                    if (lang in [registryToSLTestLanguage(r).lower() for r in slra.regex.registriesUsedIn()]) and \
                    # Restrict to the languages this regex is syntactically valid in
                      (lang in slra.regex.supportedLangs and \
                       slra.predictedPerformanceInLang(lang) != libLF.SLRegexAnalysis.INVALID_PATTERN)
                  ],
              columns=[cols["Pattern"], cols["Language"], cols["Predicted performance"]]
      )
    },
    { 'title': '"What-if" regex performance',
      'outFile': os.path.join(visDir, 'SL-type-proportion-whatif.png'),
      'df': pd.DataFrame.from_records(
              data=[ (slra.regex.pattern, nick2full(lang), pred2pretty[slra.predictedPerformanceInLang(lang)])
                    for slra in allSLRAs
                    for lang in slra.lang_pump2timedOut.keys()
                    # Restrict to the languages this regex is syntactically valid in
                    if lang in slra.regex.supportedLangs and \
                       slra.predictedPerformanceInLang(lang) != libLF.SLRegexAnalysis.INVALID_PATTERN
                  ],
              columns=[cols["Pattern"], cols["Language"], cols["Predicted performance"]]
      )
    }
  ]

  for plotInfo in plotInfos:
    df = plotInfo['df']

    # Calculate the proportion of each performance by language

    # (lang, perf) -> count of each type
    langCounts = (df
                  .groupby([cols['Language'], cols['Predicted performance']])
                  ["lang"]
                  .count()
                  # Include "0" so we don't lose Rust
                  .unstack(fill_value=0).stack()
                )
    print("\n------------------\n\n  Data for: {}\n\n------------------------".format(plotInfo["title"]))
    print("Broken down by language counts")             
    print(langCounts)

    # [ lang, perf, prop ]
    percs = (langCounts
            .groupby(level=0) # Grouped by language, go through each perf count
            .apply(lambda x: 100 * (x / float(x.sum())) ) # x / sum(xs): proportion for each perf in this lang
            .rename(cols["Percentage"]) # Give it a name
            .reset_index() # Flatten 
            )

    noLin = percs[ (percs[cols["Predicted performance"]] != pred2pretty["LIN"]) ]
    print("Per-lang perf percentages (without linear)")             
    print(noLin)

    plt.cla()
    ax = sns.barplot(x=cols["Language"], y=cols["Percentage"], hue=cols["Predicted performance"],
                    #data=percs,
                    data=noLin,
                    order=PLOT_LANG_ORDER,
                    ci=None, orient="v",
                    palette='gray')
    plt.gcf().set_size_inches(11,8) # Make sure large numbers in cells show up OK
    ax.set_xlabel('')
    #ax.xaxis.set_tick_params(fontsize='x-large')
    ax.set_xticklabels(PLOT_LANG_ORDER, rotation=45)
    ax.set_ylabel('Percent of regexes')
    #for tick in ax.yaxis.get_major_ticks():
    #  tick.label.set_fontsize('x-large')
    ax.set_title(plotInfo['title'])
    #ax.legend(fontsize='x-large')
    plt.xticks(rotation=45)
    plt.tight_layout()
    #plt.show()
    libLF.log('Saving plot to {}'.format(plotInfo['outFile']))
    plt.savefig(plotInfo['outFile'], bbox_inches='tight', pad_inches=0)

################
# Report: Portability (SL issues moving from A to B)
################

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
    #cbar.ax.tick_params(labelsize='large')
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
    #for i, xminor in enumerate(ax.xaxis.get_minorticklocs()):
    #  #if i == 0:
    #  #  continue
    #  print("Drawing vline at {}".format(xminor))
    #  ax.axvline(xminor, color="black", linewidth=1.5)
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
#    print("THRESHOLD: {}".format(threshold))
#    print("dataPlotted:")
#    print(dataPlotted)

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
        text = im.axes.text(j, i, valfmt(dataAnnot[i, j], None), fontsize='large', **kw)
        texts.append(text)

    return texts

def makeReport_portability(allSLRAs, visDir):
  libLF.log('Report: portability\n')
  # Build porting dicts

  # { 'js' -> { 'perl': sum of porting scores from js to perl, 'ruby': ... } }
  totalPortingScores = {}
  # { 'js' -> { 'perl': # regexes considered from js to perl, 'ruby': ... } }
  numRegexesConsidered = {}
  # { 'js' -> { 'perl': num that got better when moving from js to perl, ...
  numBetter = {}
  # { 'js' -> { 'perl': [num that became poly, num that became exp] when moving FROM js TO perl, ...
  NUM_WORSE_POW_IX = 0
  NUM_WORSE_EXP_IX = 1
  numWorse = {}

  numEverSuperLinear = 0 # If super-linear AT ALL, note it once
  numWorseInAnyPair = 0 # If worse AT ALL, note it once


  # If porting does not affect performance:
  #   - totalPortingScores is not affected (incremented by 0)
  #   - counts is incremented by one (enabling normalization)
  #   - numBetter, numWorse is not incremented

  # Initialize
  for src in allSLTestLanguages():
    totalPortingScores[src] = {}
    numRegexesConsidered[src] = {}
    numBetter[src] = {}
    numWorse[src] = {}

  for src in allSLTestLanguages():
    for dst in allSLTestLanguages():
      totalPortingScores[src][dst] = 0
      numRegexesConsidered[src][dst] = 0
      numBetter[src][dst] = 0
      numWorse[src][dst] = [0, 0]

  # Update the various dictionaries based on each SLRA
  for slra in allSLRAs:
    # Ever super-linear?
    if slra.everTimedOut():
      numEverSuperLinear += 1

    # Check for pairwise differences
    worseInAnyPair = False
    for src in allSLTestLanguages():
      for dst in allSLTestLanguages():
        portingScore = slra.predictedPerformancePortingScore(src, dst)

        simplePortingScore = 0
        if portingScore is not None:
          if portingScore > 0:
            simplePortingScore = 1
            # Count once
            if not worseInAnyPair:
              worseInAnyPair = True
              numWorseInAnyPair += 1
          elif portingScore < 0:
            simplePortingScore = -1
            # Count once
            if not worseInAnyPair:
              worseInAnyPair = True
              numWorseInAnyPair += 1
          else:
            # No difference
            pass
        
        # For debugging
        #   Q: Why would this happen?
        #   A: 500K pumps is too many for perl to efficiently decode_json() in some cases.
        #      In the next run I am using 100K pumps instead, which should help.
        #if 0 < simplePortingScore:
        #  if src.lower() == "perl" and dst.lower() == "javascript":
        #    libLF.log("Performance improved from perl -> js for regex /{}/".format(slra.regex.pattern))

        totalPortingScores[src][dst] += simplePortingScore
        numRegexesConsidered[src][dst] += 1

        if 0 < simplePortingScore:
          numBetter[src][dst] += 1
        elif simplePortingScore < 0:
          predPerf = slra.predictedPerformanceInLang(dst)
          if predPerf == libLF.SLRegexAnalysis.PREDICTED_PERFORMANCE['POW']:
            numWorse[src][dst][NUM_WORSE_POW_IX] += 1
          elif predPerf == libLF.SLRegexAnalysis.PREDICTED_PERFORMANCE['EXP']:
            numWorse[src][dst][NUM_WORSE_EXP_IX] += 1
          else:
            libLF.log("?????")
            sys.exit(-1)
            raise ValueError("How could simplePortingScore from {} to {} be {} if predicted perf in {} is {}?" \
              .format(src, dst, simplePortingScore, dst, predPerf))
  
  # As ndarray for heatmap()
  # Rows are destinations, cols are sources, so need to transpose from the original
  tps_arr = np.empty((len(PLOT_LANG_ORDER), len(PLOT_LANG_ORDER)), dtype=float)
  sumWorse_arr = np.empty((len(PLOT_LANG_ORDER), len(PLOT_LANG_ORDER)), dtype=float)
  labels_arr = np.empty((len(PLOT_LANG_ORDER), len(PLOT_LANG_ORDER)), dtype=object)

  for i, i_lang in enumerate(PLOT_LANG_ORDER):
    for j, j_lang in enumerate(PLOT_LANG_ORDER):
      # We are transposing, so use [j][i] for tps_arr and labels_arr
      if i == j:
        labels_arr[j][i] = ""
        tps_arr[j][i] = 0
        sumWorse_arr[j][i] = 0
      else:
        tps_arr[j][i] = totalPortingScores[i_lang][j_lang]
        sumWorse_arr[j][i] = sum(numWorse[i_lang][j_lang])
        #labels_arr[j][i] = "{:.1f}% P\n{:.1f}% E" \
        #  .format(100 *  numWorse[i_lang][j_lang][NUM_WORSE_POW_IX] / numRegexesConsidered[i_lang][j_lang],
        #          100 *  numWorse[i_lang][j_lang][NUM_WORSE_EXP_IX] / numRegexesConsidered[i_lang][j_lang],
        #  )
        labels_arr[j][i] = "{:.1f}%" \
          .format(100 *  sum(numWorse[i_lang][j_lang]) / numRegexesConsidered[i_lang][j_lang])
  
#  # Set the diagonal to "white"
#  for i, _ in enumerate(PLOT_LANG_ORDER):
#    tps_arr[i][i] = tps_arr.max() # This will be "white" on the greyscale

  print("Raw numbers")
  print('---------------')
  print("{}/{} ({:.2f}%) of regexes were super-linar in some language" \
    .format(numEverSuperLinear, len(allSLRAs), 100 * numEverSuperLinear / len(allSLRAs)))
  print("{}/{} ({:.2f}%) of regexes performed worse between some pair of languages" \
    .format(numWorseInAnyPair, len(allSLRAs), 100 * numWorseInAnyPair / len(allSLRAs)))
  print('---------------')
  print('totalPortingScores')
  print(tps_arr)
  print('---------------')
  print('labels')
  print(labels_arr)

  # Make the plot
          
  plt.cla()
  fig, ax = plt.subplots()
  fig.set_size_inches(11,8)

  im, cbar = heatmap(sumWorse_arr, PLOT_LANG_ORDER, PLOT_LANG_ORDER,
              ax=ax,
              cmap='gray_r', cbarlabel='Number of regexes that got worse')

  ax.set_title("Worst-case regex performance differences", pad=75, fontsize="xx-large")
  ax.set_ylabel("Destination language", labelpad=0, fontsize="xx-large")

  texts = annotate_heatmap(im,
    dataAnnot=labels_arr, valfmt=lambda x, pos: x,
    #textcolors=["white", "black"], # Colormap is reversed
    #threshold=0
    )
  #ax.set_aspect('equal') # Make sure cells are squares
  plt.tight_layout()

  #plt.show()
  outFile = os.path.join(visDir, 'SL-porting-heatmap.png')
  libLF.log('Saving plot to {}'.format(outFile))
  plt.savefig(outFile, bbox_inches='tight', pad_inches=0)

################

def main(slraFile, visDir):
  libLF.log("slraFile {} visDir {}".format(slraFile, visDir))

  #### Load data
  allSLRAs = loadSLRAFile(slraFile)

  allSLRAs_timedOut = getTimedOutSet(allSLRAs)
  libLF.log('{} timed out'.format(len(allSLRAs_timedOut)))

  allSLRAs_crossRegistry = getCrossRegistrySet(allSLRAs)
  libLF.log('{} cross registry'.format(len(allSLRAs_crossRegistry)))

  allSLRAs_crossRegistry_timedOut = allSLRAs_timedOut & allSLRAs_crossRegistry
  libLF.log('{} timed out and cross registry'.format(len(allSLRAs_crossRegistry_timedOut)))

  #### Reports
  libLF.log("Creating reports (to stdout)")

  print("\n\n")
  makeReport_variantEffectiveness(allSLRAs)
  print("\n\n")
  makeReport_detectorEffectiveness(allSLRAs)
  print("\n\n")
  makeReport_perRegistryTimeouts(allSLRAs, visDir)
  print("\n\n")
  makeReport_portability(allSLRAs, visDir)


#####################################################

# Parse args
parser = argparse.ArgumentParser(description='Analyze the results of testing a bunch of libLF.Regex\'s for SL behavior')
parser.add_argument('--slra-file', type=str, help='In: File of libLF.SLRegexAnalysis objects', required=True,
  dest='slraFile')
parser.add_argument('--vis-dir', help='Out: Where to save plots?', required=False, default='/tmp/vis',
  dest='visDir')
# TODO: Filter each regex's results for the language pairs in which the regex is syntax-compatible.
#       Or should we restrict to the syntax-universal regexes?
# TODO: Emit the list of all regexes that timed out in any language
args = parser.parse_args()

# Here we go!
main(args.slraFile, args.visDir)
