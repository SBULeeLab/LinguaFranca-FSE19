#!/usr/bin/env python3
# Driver for rex
# You must have 'wine' available

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
import itertools
import json

################
# Dependencies
################

WINE_PATH = shutil.which("wine")
REX_PATH = os.path.join(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT'], 'bin', 'RexInputGenerator.exe')
libLF.checkShellDependencies([REX_PATH, WINE_PATH], mustBeExecutable=False)

DELETE_TMP_FILES = True

################
# Settings
################

# Peipei Wang from Katie Stolee's group says they use this invocation of Rex:
#for type_encode in ['ASCII','Unicode']:                
#            fileInputs="inputs/"+str(index)+"_"+type_encode        
#            if seed is None:
#                cmd=[rex_path,"/k:"+str(k), "/file:"+fileInputs,"/encoding:"+type_encode,regextemp]
#            else:
#                cmd=[rex_path,"/k:"+str(k), "/file:"+fileInputs,"/encoding:"+type_encode,str_seed,regextemp]
#
# We use both encoding flavors as well as exploring various interesting-sounding rexOptions

encodings = ['ASCII', 'Unicode']

# Compute a power set of the options of interest
rexOptionsToTry = ['IgnoreCase','ECMAScript','CultureInvariant']
rexOptionsPowerSet = list(itertools.chain.from_iterable(itertools.combinations(rexOptionsToTry, r) for r in range(len(rexOptionsToTry)+1)))

################
# Helpers
################

# This will run for each of a set of option combinations 
def getRexInputs(pattern, seed, nInputs, timeout):
  """Return stringsByProducer for use as an RPAI member"""
  nModes = len(encodings) * len(rexOptionsPowerSet)
  inputsPerMode = int(nInputs / nModes)

  stringsByProducer = {}
  for encoding in encodings:
    for rexOptions in rexOptionsPowerSet:

      libLF.log("Encoding: {}".format(encoding))
      libLF.log("Options: {}".format(rexOptions))

      with tempfile.NamedTemporaryFile(prefix='GenInput-QueryRex-RegexFile-', suffix='.dat', delete=DELETE_TMP_FILES) as rexInFile, \
          tempfile.NamedTemporaryFile(prefix='GenInput-QueryRex-ResponseFile-', suffix='.dat', delete=DELETE_TMP_FILES) as rexOutFile:

        # Build input file
        libLF.writeToFile(rexInFile.name, pattern)
        # Build command to run
        cmd = [WINE_PATH, REX_PATH,
               "/regexfile:"+rexInFile.name, "/k:"+str(inputsPerMode),
               "/encoding:"+encoding, "/seed:"+str(seed),
               "/file:"+rexOutFile.name]
        for opt in rexOptions:
          cmd.append("/options:"+opt)
        libLF.log('cmd: ' + " ".join(cmd))
        #inputs = []
        #producerName = 'rex-Encoding{}-Options{}'.format(encoding, '-'.join(rexOptions)) 
        #stringsByProducer[producerName] = inputs
        #continue

        # Get inputs, guarded by a timeout
        tmo = None if timeout < 0 else timeout
        inputs = []
        try:
          completedProcess = subprocess.run(cmd, timeout=tmo)
          rc = completedProcess.returncode
          libLF.log("rc: " + str(rc))
          if rc == 0:
            inputs = processRexOutFile(rexOutFile.name)
        except subprocess.TimeoutExpired:
          libLF.log("Rex timed out")
          try:
            libLF.log("Salvaging any strings streamed by Rex before the timeout")
            inputs = processRexOutFile(rexOutFile.name)
          except Exception:
            pass
        except Exception as err:
          libLF.log("Exception: " + str(err))
        libLF.log("{} inputs from: encoding {} options {}".format(len(inputs), encoding, rexOptions))
        producerName = 'rex-Encoding{}-Options{}'.format(encoding, '-'.join(rexOptions)) 
        stringsByProducer[producerName] = inputs
  return stringsByProducer

def processRexOutFile(rawRexFile):
  inputs = set()
  with open(rawRexFile, 'r') as inStream:
    for line in inStream:
      # Format is: "string-to-try"
      line = line.strip()
      #libLF.log('LINE: {}'.format(line))
      try:
        recommendedString = line[1:-1]
        inputs.add(recommendedString)
      except:
        pass
  return sorted(list(inputs))

################
# Main
################
      
def main(regexFile, outFile, seed, nInputs, timeout):
  libLF.log('regexFile {} outFile {} seed {} nInputs {} timeout {}' \
    .format(regexFile, outFile, seed, nInputs, timeout))

  # Get the libLF.Regex
  with open(regexFile, 'r') as inStream:
    regex = libLF.Regex().initFromNDJSON(inStream.read())
  libLF.log('Generating inputs for regex /{}/'.format(regex.pattern))
  
  # Query Rex
  stringsByProducer = getRexInputs(regex.pattern, seed, nInputs, timeout)

  # Emit
  rpai = libLF.RegexPatternAndInputs().initFromRaw(regex.pattern, stringsByProducer)
  libLF.log('Rex generated {} unique inputs for regex /{}/ ({} including duplicates)' \
    .format(len(rpai.getUniqueInputs()), regex.pattern, rpai.getNTotalInputs()))
  with open(outFile, 'w') as outStream:
    outStream.write(rpai.toNDJSON())

################################

# Parse args
parser = argparse.ArgumentParser(description='Given a libLF.Regex, ask Rex for inputs to try')
parser.add_argument('--regex-file', help='File containing a libLF.Regex', required=True,
  dest='regexFile')
parser.add_argument('--out-file', type=str, help='Out: File of one libLF.RegexPatternAndInputs object containing the inputs found using rex', required=True,
  dest='outFile')
parser.add_argument('--seed', type=int, help='Seed to use for reproducibility (default: random)', required=False, default=-1,
  dest='seed')
parser.add_argument('--num-inputs', type=int, help='Rough estimate of the total number of input strings to create, divided across various modes (default: 1K)', required=False, default=1000,
  dest='nInputs')
parser.add_argument('--timeout', type=float, help='Maximum time to run for, in seconds (default 30, -1 means no limit)', required=False, default=30,
  dest='timeout')

args = parser.parse_args()
# Here we go!
main(args.regexFile, args.outFile, args.seed, args.nInputs, args.timeout) 
