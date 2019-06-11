#!/usr/bin/env python3
# Driver for MutMutRex

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

MUTREX_PATH = os.path.join(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT'], 'bin', 'MutRexInputGenerator.jar')
libLF.checkShellDependencies([MUTREX_PATH], mustBeExecutable=False)

################
# Helpers
################

def getMutRexInputs(pattern, timeout):
  """Return inputs: str[]"""

  # Build command to run
  cmd = ["java", "-jar", MUTREX_PATH, pattern]
  libLF.log('cmd: ' + " ".join(cmd))

  # Get inputs, guarded by a timeout
  tmo = None if timeout < 0 else timeout
  inputs = []
  try:
    completedProcess = subprocess.run(cmd, stdout=subprocess.PIPE, timeout=tmo)
    libLF.log('rc {}'.format(completedProcess.returncode))
    if completedProcess.returncode == 0:
      inputs = processMutRexOutput(completedProcess.stdout.decode('utf-8'))
  except subprocess.TimeoutExpired:
    libLF.log("MutRex timed out")
    try:
      libLF.log("Salvaging any strings streamed by MutRex before the timeout")
      inputs = processMutRexOutput(tmo.stdout.decode('utf-8'))
    except Exception:
      pass
  except Exception as err:
    libLF.log('Exception: ' + str(err))
  return inputs

def processMutRexOutput(outputFromMutRex):
  inputs = set()
  # "..." (REJECT) or "..." (CONF) (may include newlines)
  libLF.log('processMutRexOut: out: \n' + outputFromMutRex)
  for match in re.findall(r"^\"(.*?)\" \((?:REJECT|CONF)\)", outputFromMutRex, re.MULTILINE|re.DOTALL):
    libLF.log("match: <{}>".format(match))
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
  
  # Query MutRex
  mutRexInputs = getMutRexInputs(regex.pattern, timeout)
  libLF.log('MutRex generated {} inputs for regex /{}/'.format(len(mutRexInputs), regex.pattern))

  # Emit
  stringsByProducer = { "MutRex": mutRexInputs }
  with open(outFile, 'w') as outStream:
    rpai = libLF.RegexPatternAndInputs().initFromRaw(regex.pattern, stringsByProducer)
    outStream.write(rpai.toNDJSON())

################################

# Parse args
parser = argparse.ArgumentParser(description='Given a libLF.Regex, ask MutRex for inputs to try')
parser.add_argument('--regex-file', help='File containing a libLF.Regex', required=True,
  dest='regexFile')
parser.add_argument('--out-file', type=str, help='Out: File of one libLF.RegexPatternAndInputs object containing the inputs found using rex', required=True,
  dest='outFile')
parser.add_argument('--timeout', type=float, help='Maximum time to run for, in seconds (default 30, -1 means no limit)', required=False, default=30,
  dest='timeout')

args = parser.parse_args()
# Here we go!
main(args.regexFile, args.outFile, args.timeout) 
