#!/usr/bin/env python3
# Extract regexes from a typescript file.
# Approach:
# 1. Use tsc to transpile to a JS file.
# 2. Use our JS regex extractor on the resulting JS.

# Import libLF
import os
import sys
import re
sys.path.append(os.path.join(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT'], 'lib'))
import libLF

import argparse
import shutil
import tempfile

transpiler = os.path.join(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT'],
                          'ecosystems',
                          'per-module',
                          'extract-regexps',
                          'static',
                          'ts',
                          'transpile-ts2js-tsc.js')

# TODO Switch to regex-extractor.py. Once it supports JS extraction this should work fine.
# If we switch, we will need to consume its output and then convert it to the expected format for a lang-specific extractor.
#regexExtractorCmd = os.path.join(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT'], 'ecosystems', 'per-module', 'regex-extractor.py')
regexExtractor = os.path.join(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT'],
                              'ecosystems',
                              'per-module',
                              'extract-regexps',
                              'static',
                              'js',
                              'extract-regexps.js')

def checkDependencies(deps):
    for dep in deps:
        if shutil.which(transpiler) is None:
            raise AssertionError("Error, could not find dependency in PATH: {}".format(dep))

def transpile(tsSrc, jsDest):
    """Transpile TypeScript: from tsSrc into jsDest"""
    # ./node_modules/.bin/babel --out-file /tmp/x.js --presets @babel/preset-typescript test/apps/Hitchhiker/client/src/store.ts 
    cmd = "'{}' '{}' > '{}'".format(transpiler, tsSrc, jsDest)
    libLF.chkcmd(cmd)

def extractRegexesFromJS(jsFile):
    """Extract regexes from this JS file.

    Returns a libLF.SimpleFileWithRegexes object.
    """

    # Extract
    cmd = "'{}' '{}'".format(regexExtractor, jsFile)
    out = libLF.chkcmd(cmd)

    # Object-ify
    sfwr = libLF.SimpleFileWithRegexes()
    sfwr.initFromNDJSON(out)
    return sfwr

def main(tsFile):
    checkDependencies([transpiler, regexExtractor])
    _, jsTmpFile = tempfile.mkstemp(suffix='.js')

    sfwr = libLF.SimpleFileWithRegexes()
    try:
        # Get regexes from JS version
        transpile(tsFile, jsTmpFile)
        sfwr = extractRegexesFromJS(jsTmpFile)

        # Tweak result a bit -- real file name, not temp file
        sfwr.fileName = tsFile

        # Clean up
        os.remove(jsTmpFile)
    except BaseException as err:
        libLF.log('Error: {}'.format(err))
        sfwr.initFromRaw(fileName=tsFile, language='typescript', couldParse=0, regexes=[])
    print(sfwr.toNDJSON())

###############################################

# Parse args
parser = argparse.ArgumentParser(description='Extract regexes from a TypeScript file')
parser.add_argument('file_to_extract', help='TypeScript file from which to extract regexes')

args = parser.parse_args()
# Here we go!
main(args.file_to_extract)
