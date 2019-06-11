#!/usr/bin/env python3
# Driver for MutReScue

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

RESCUE_PATH = os.path.join(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT'], 'bin', 'ReScueInputGenerator.jar')
libLF.checkShellDependencies([RESCUE_PATH], mustBeExecutable=False)

CROSSOVER_PROBABILITY = 10
MUTATE_PROBABILITY = 10

################
# Helpers
################

def getReScueInputs(pattern, timeout):
  """Return inputs: str[]"""
  # Use subprocess.run directly instead of libLF.runcmd because the regex is delivered on command line
  # and might be unescaped, contain newlines, etc.
  # Also, we want to be able to capture stderr cleanly with a timeout.
  libLF.log('Command: ' + str(["java", "-jar", RESCUE_PATH, "--regex", pattern, "--crossPossibility", CROSSOVER_PROBABILITY, "--mutatePossibility", MUTATE_PROBABILITY]))

  rc = 0
  try:
    tmo = None if timeout < 0 else timeout
    completedProcess = subprocess.run(
      ["java", "-jar", RESCUE_PATH, "--regex", pattern, "--crossPossibility", str(CROSSOVER_PROBABILITY), "--mutatePossibility", str(MUTATE_PROBABILITY)],
      stderr=subprocess.PIPE, timeout=tmo)
    outputToUse = completedProcess.stderr.decode('utf-8')
    rc = completedProcess.returncode
  except subprocess.TimeoutExpired as to:
    libLF.log("Timeout, let's see if we can salvage using the stderr stream")
    outputToUse = to.stderr.decode('utf-8')

  if rc == 0:
    try:
      return processReScueOutput(outputToUse)
    except Exception as err:
      libLF.log('Exception: ' + err)
      return []
  else:
    libLF.log('rc {}'.format(rc))
    return []

def processReScueOutput(outputFromReScue):
  inputs = set()
  # RAND STR: "..."
  #  (The "..." is JSON-formatted)
  #libLF.log('processReScueOutput: out: \n' + outputFromReScue)
  for match in re.findall(r"^Test string: \"(.*?)\"$", outputFromReScue, re.MULTILINE):
    #libLF.log("match: <{}>".format(match))
    inputs.add(match)
  return sorted(list(inputs))

################
# Main
################
      
def main(regexFile, outFile, timeout):
  libLF.log('regexFile {} outFile {} timeout {}' \
    .format(regexFile, outFile, timeout))

  # Get the libLF.Regex
  with open(regexFile, 'r') as inStream:
    regex = libLF.Regex().initFromNDJSON(inStream.read())
  libLF.log('Generating inputs for regex /{}/'.format(regex.pattern))
  
  # Query ReScue
  mutRexInputs = getReScueInputs(regex.pattern, timeout)
  libLF.log('ReScue generated {} inputs for regex /{}/'.format(len(mutRexInputs), regex.pattern))

  # Emit
  stringsByProducer = { "ReScue": mutRexInputs }
  with open(outFile, 'w') as outStream:
    rpai = libLF.RegexPatternAndInputs().initFromRaw(regex.pattern, stringsByProducer)
    outStream.write(rpai.toNDJSON())

################################

# Parse args
parser = argparse.ArgumentParser(description='Given a libLF.Regex, ask ReScue for inputs to try')
parser.add_argument('--regex-file', help='File containing a libLF.Regex', required=True,
  dest='regexFile')
parser.add_argument('--out-file', type=str, help='Out: File of one libLF.RegexPatternAndInputs object containing the inputs found using rex', required=True,
  dest='outFile')
parser.add_argument('--timeout', type=int, help='Maximum time to run ReScue for, in seconds (default 5, -1 means no limit)', required=False, default=5,
  dest='timeout')

args = parser.parse_args()
# Here we go!
main(args.regexFile, args.outFile, args.timeout) 
