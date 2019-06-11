#!/usr/bin/env python3
# Driver for EGRET

# Import libLF
import os
import sys
import re
sys.path.append('{}/lib'.format(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT']))
import libLF
import subprocess
import tempfile
import argparse
import re
import json

################
# Dependencies
################

EGRET_PATH = os.path.join(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT'], 'bin', 'EgretInputGenerator.py')
libLF.checkShellDependencies([EGRET_PATH], mustBeExecutable=False)

################
# Globals
################

DELETE_TMP_FILES = True

################
# Helpers
################

def getEGRETInputs(pattern, timeout):
  """Return inputs: str[]"""
  with tempfile.NamedTemporaryFile(prefix='GenInput-QueryEGRET-RegexFile-',
                                  suffix='.dat',
                                  delete=DELETE_TMP_FILES) as inFile, \
       tempfile.NamedTemporaryFile(prefix='GenInput-QueryEGRET-ResponseFile-',
                                   suffix='.dat',
                                   delete=DELETE_TMP_FILES) as outFile:
    # Build input file
    libLF.writeToFile(inFile.name, pattern)
    # Build command to run
    cmd = ["python3", EGRET_PATH, "--file", inFile.name, "--output_file", outFile.name]
    libLF.log('cmd: ' + " ".join(cmd))

    # Get inputs, guarded by a timeout
    tmo = None if timeout < 0 else timeout
    inputs = []
    try:
      completedProcess = subprocess.run(cmd,
        timeout=tmo)
      rc = completedProcess.returncode
      libLF.log("rc: " + str(rc))

      if rc == 0:
        inputs = processEGRETOutFile(outFile.name)
    except subprocess.TimeoutExpired:
      libLF.log("EGRET timed out")
      try:
        libLF.log("Salvaging any strings streamed by EGRET before the timeout")
        inputs = processEGRETOutFile(outFile.name)
      except Exception:
        pass
    except Exception as err:
      libLF.log('Exception: ' + str(err))
    return inputs

def processEGRETOutFile(rawEGRETFile):
  inputs = set()
  with open(rawEGRETFile, 'r') as f:
    for line in f:
      line = line.strip()
      libLF.log('LINE: {}'.format(line))
      if line.startswith("Matches:") or line.startswith("Non-matches:"):
        match = re.search(r"^[\w\-]+atches: (\[.*\])$", line)
        if match:
          inputs.update(json.loads(match.group(1)))
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
  
  # Query Rex
  inputs = getEGRETInputs(regex.pattern, timeout)
  libLF.log('EGRET generated {} inputs for regex /{}/'.format(len(inputs), regex.pattern))

  # Emit
  stringsByProducer = { "EGRET": inputs }
  with open(outFile, 'w') as outStream:
    rpai = libLF.RegexPatternAndInputs().initFromRaw(regex.pattern, stringsByProducer)
    outStream.write(rpai.toNDJSON())

################################

# Parse args
parser = argparse.ArgumentParser(description='Given a libLF.Regex, ask EGRET for inputs to try')
parser.add_argument('--regex-file', help='File containing a libLF.Regex', required=True,
  dest='regexFile')
parser.add_argument('--out-file', type=str, help='Out: File of one libLF.RegexPatternAndInputs object containing the inputs found using rex', required=True,
  dest='outFile')
parser.add_argument('--timeout', type=float, help='Maximum time to run for, in seconds (default 30, -1 means no limit)', required=False, default=30,
  dest='timeout')

args = parser.parse_args()
# Here we go!
main(args.regexFile, args.outFile, args.timeout)

args = parser.parse_args()
