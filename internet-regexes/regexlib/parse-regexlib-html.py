#!/usr/bin/env python3
# Description:
#   Extracts regexes from the HTML served by RegExLib.com
#   Writes them in JSON format to outFile.

# Import libLF
import os
import sys
sys.path.append('{}/lib'.format(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT']))
import libLF

import argparse
import re
import html

# Class to extract InternetSource objects from a www.regexlib.com HTML page.
class RegexExtractor:
  def __init__(self):
    pass

  # input: html string from one of the regexlib pages
  # output: InternetSource[]
  def getInternetSources(self, html):
    internetSources = []

    stringAtBeginningOfEachEntry = '<table border="0" cellspacing="0" cellpadding="0" class="searchResultsTable">'
    entries = html.split(stringAtBeginningOfEachEntry)
    # Remove leading entry which does not contain a table
    entries.pop(0)
    for e in entries:
      fullEntry = stringAtBeginningOfEachEntry + e
      try:
        source = self._getInternetSourceFromEntry(fullEntry)
        libLF.log('Got source! {}'.format(source.toNDJSON()))
        internetSources.append(source)
      except ValueError as err:
        libLF.log('Extraction failed: {}'.format(str(err)))
    return internetSources

  def _getInternetSourceFromEntry(self, entry):
    libLF.log('Entry: {}'.format(entry))
    uri = None
    uriAliases = []
    patterns = []

    # uri and uriAliases
    match = re.search(r"href='(REDetails.aspx\?regexp_id=\d+)'", entry)
    if match:
      uri = 'http://www.regexlib.com/' + match.group(1)
      uriAliases.append('http://regexplib.com/' + match.group(1))
    else:
      raise ValueError('Could not find uri in entry: {}'.format(entry))

    # pattern
    # Sometimes long patterns are split across multiple lines, so we use DOTALL.
    # The resulting pattern is not always a valid pattern.
    # This is user-generated input so we do the best we can.
    # Counter-examples:
    #   1. Truncated regex: http://www.regexlib.com/REDetails.aspx?regexp_id=3058
    #   2. Two regexes: http://www.regexlib.com/REDetails.aspx?regexp_id=3114
    match = re.search(r"class=\"expressionDiv\">(.+?)</div></td>", entry, re.DOTALL)
    if match:
      pattern = match.group(1)

      # Un-escape special HTML characters like < and >.
      pattern = html.unescape(pattern)

      # If they included a leading and trailing slash, remove them.
      pattern = libLF.perlStyleToPattern(pattern)

      patterns.append(pattern)
    else:
      raise ValueError('Could not find pattern in entry: {}'.format(entry))

    internetSource = libLF.RegExLibRegexSource()
    internetSource.initFromRaw(uri, uriAliases, patterns)
    return internetSource

def main(htmlDir, outFile):
  i = 1
  libLF.log('Output will go to file {}'.format(outFile))
  with open(outFile, 'w') as outStream:
    # Handle each html file.
    for f in os.listdir(htmlDir):
      if f.endswith('.html'):
        filePath = os.path.join(htmlDir, f)

        # Extract regexes from this file.
        libLF.log("Working on file {}: {}".format(i, filePath))
        with open(filePath, "r") as inStream:
          rx = RegexExtractor()
          internetSources = rx.getInternetSources(inStream.read())
          # Write out.
          for internetSource in internetSources:
            outStream.write(internetSource.toNDJSON() + '\n')
        i = i + 1

###############################################

# Parse args
parser = argparse.ArgumentParser(description='Extract regexes from an HTML dump of www.regexlib.com')
parser.add_argument('--html-dir', help='Dir containing .html files of pages from www.regexlib.com', required=True)
parser.add_argument('--out-file', '-o', help='Where to write ndjson results?', required=True)

args = parser.parse_args()

# Here we go!
main(args.html_dir, args.out_file)
