#!/usr/bin/env python3
# Driver for MutBrics

# Import libLF
import os
import sys
import re
sys.path.append('{}/lib'.format(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT']))
import libLF
import subprocess
import tempfile
import argparse
import shutil
import shlex

import re
import subprocess

################
# Dependencies
################

BRICS_PATH = os.path.join(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT'], 'bin', 'BricsInputGenerator.jar')
libLF.checkShellDependencies([BRICS_PATH], mustBeExecutable=False)

MAX_STRING_LEN = 128
PROB_EXCESSIVE_STRINGS = 0

################
# Helpers
################

def convertPatternToBrics(pattern):
  """Convert to Brics style
  
  The Brics language is fairly minimal:
    http://www.brics.dk/automaton/doc/index.html?dk/brics/automaton/RegExp.html
  In particular, it supports *no* character classes like \d or \s.
  This converts all such character classes to an explicit list of members based on Python 3 syntax.
    https://docs.python.org/3/library/re.html
  """
  return pattern \
    .replace("\\d", "[0123456789]") \
    .replace("\\D", "[^0123456789]") \
    .replace("\\s", "[ \\t\\n\\r\\f\\v]") \
    .replace("\\S", "[^ \\t\\n\\r\\f\\v]") \
    .replace("\\w", "[a-zA-Z0-9_]") \
    .replace("\\W", "[^a-zA-Z0-9_]")

def getBricsInputs(pattern, seed, timeout):
  """Return inputs: str[]"""
  # Use subprocess.run directly instead of libLF.runcmd because the regex is delivered on command line
  # and might be unescaped, contain newlines, etc.
  # Also, we want to be able to capture stderr cleanly with a timeout.
  bricsPattern = convertPatternToBrics(pattern)
  libLF.log('Pattern conversion:\n before /{}/\n after  /{}/'.format(pattern, bricsPattern))
  # (My fork of) Brics treats -1 as "no seed internally"
  cmd = ["java", "-jar", BRICS_PATH, bricsPattern, str(MAX_STRING_LEN), str(PROB_EXCESSIVE_STRINGS), str(seed)]
  libLF.log('Command: ' + str(cmd))

  rc = 0
  inputs = []
  try:
    tmo = None if timeout < 0 else timeout
    completedProcess = subprocess.run(
      cmd,
      stderr=subprocess.PIPE, timeout=tmo)
    rc = completedProcess.returncode
    libLF.log('rc: {}'.format(rc))
    if rc == 0:
      inputs = processBricsOutput(completedProcess.stderr.decode('utf-8'))
  except subprocess.TimeoutExpired as to:
    libLF.log("Timeout, let's see if we can salvage using the stderr stream")
    try:
      inputs = processBricsOutput(to.stderr.decode('utf-8'))
    except:
      pass
  except Exception as err:
    libLF.log('Exception: {}'.format(err))
  return inputs

def processBricsOutput(outputFromBrics):
  inputs = set()
  # RAND STR: "..."
  #  (The "..." is JSON-formatted)
  #libLF.log('processBricsOutput: out: \n' + outputFromBrics)
  for match in re.findall(r"^\(\w+\) getRandomString\w+: STR: \"(.*?)\"$", outputFromBrics, re.MULTILINE):
    libLF.log("match: <{}>".format(match))
    inputs.add(match)
  return sorted(list(inputs))

################
# Main
################
      
def main(regexFile, outFile, seed, timeout):
  libLF.log('regexFile {} outFile {} seed {} timeout {}' \
    .format(regexFile, outFile, seed, timeout))

  # Get the libLF.Regex
  with open(regexFile, 'r') as inStream:
    regex = libLF.Regex().initFromNDJSON(inStream.read())
  libLF.log('Generating inputs for regex /{}/'.format(regex.pattern))
  
  # Query Brics
  bricsInputs = getBricsInputs(regex.pattern, seed, timeout)
  libLF.log('Brics generated {} inputs for regex /{}/'.format(len(bricsInputs), regex.pattern))

  # Emit
  stringsByProducer = { "Brics": bricsInputs }
  with open(outFile, 'w') as outStream:
    rpai = libLF.RegexPatternAndInputs().initFromRaw(regex.pattern, stringsByProducer)
    outStream.write(rpai.toNDJSON())

################################

# Parse args
parser = argparse.ArgumentParser(description='Given a libLF.Regex, ask Brics for inputs to try')
parser.add_argument('--regex-file', help='File containing a libLF.Regex', required=True,
  dest='regexFile')
parser.add_argument('--out-file', type=str, help='Out: File of one libLF.RegexPatternAndInputs object containing the inputs found using rex', required=True,
  dest='outFile')
parser.add_argument('--seed', type=int, help='Seed to use for reproducibility (default: random)', required=False, default=-1,
  dest='seed')
parser.add_argument('--timeout', type=int, help='Maximum time to run Brics for, in seconds (default: 10; -1: no limit)', required=False, default=10,
  dest='timeout')

args = parser.parse_args()
# Here we go!
main(args.regexFile, args.outFile, args.seed, args.timeout) 
