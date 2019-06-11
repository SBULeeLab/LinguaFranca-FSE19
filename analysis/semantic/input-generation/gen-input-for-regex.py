#!/usr/bin/env python3
# Generate input strings for a set of regexes

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
import shutil
import random

#######################

# If user does not request a number of inputs, we need to tell Rex something
DEFAULT_REX_NUM_INPUTS = 1000

DELETE_TMP_FILES = True

#######################

# Python-y wrappers for the input generators
class Generator:
  """Represents one of the generators we query"""
  def __init__(self, name, driver):
    self.name = name
    self.driver = driver

  def driverExists(self):
    return shutil.which(self.driver) is not None
  
  def queryHelper(self, regex, commandToRunFmt):
    """query() might benefit from this

    regex: the libLF.regex to query
    commandToRunFmt: format string with the invocation
      We apply commandToRun.format(inFile, outFile)
      inFile: contains a libLF.Regex, NDJSON formatted
      outFile: contains a libLF.RegexPatternAndInput, NDJSON formatted
    @returns: GeneratorQueryResponse[]
    """
    libLF.log('queryHelper for {}:\n  regex /{}/\n  command {}' \
      .format(self.name, regex.pattern, commandToRunFmt))
    gqrs = []
    with tempfile.NamedTemporaryFile(prefix='GenInput-DriverQueryFile-',
                                     suffix='.json',
                                     delete=DELETE_TMP_FILES) as inFile, \
          tempfile.NamedTemporaryFile(prefix='GenInput-DriverOutFile-',
                                     suffix='.json',
                                     delete=DELETE_TMP_FILES) as outFile:
      libLF.writeToFile(inFile.name, regex.toNDJSON())
      rc, out = libLF.runcmd(commandToRunFmt.format(inFile.name, outFile.name))
      if rc == 0:
        with open(outFile.name, 'r') as inStream:
          contents = inStream.read()
          rpai = libLF.RegexPatternAndInputs().initFromNDJSON(contents)
          for producer in rpai.stringsByProducer:
            gqr = GeneratorQueryResponse(producer, rpai.stringsByProducer[producer])
            gqrs.append(gqr)
    return gqrs

  def query(self, regex, rngSeed, inputsPerGenerator, generatorTimeout):
    """Override me. I suggest you use queryHelper.
    
    regex: a libLF.Regex
    rngSeed: if generator supports it, use this seed
    inputsPerGenerator: return at most this many inputs
    generatorTimeout: if generator supports it, ask it to take no more than this long

    @return GeneratorQueryResponse[]
    """
    libLF.log('Error, you must override query for {}'.format(self.name))
    sys.exit(1)

class GeneratorQueryResponse:
  def __init__(self, name, inputs):
    self.name = name
    self.inputs = inputs

class Generator_Rex(Generator):
  def query(self, regex, rngSeed, inputsPerGenerator, generatorTimeout):
    if inputsPerGenerator < 0:
      inputsPerGenerator = DEFAULT_REX_NUM_INPUTS
    return self.queryHelper(regex, '{} --regex-file {{}} --out-file {{}} --seed 1 --num-inputs {} --seed {} --timeout {} 2>/tmp/gen-input.log' \
        .format(self.driver, inputsPerGenerator, rngSeed, generatorTimeout))

class Generator_EGRET(Generator):
  def query(self, regex, rngSeed, inputsPerGenerator, generatorTimeout):
    # rngSeed: AFAIK EGRET is deterministic
    return self.queryHelper(regex, '{} --regex-file {{}} --out-file {{}} --timeout {} 2>/tmp/gen-input.log' \
        .format(self.driver, generatorTimeout))

class Generator_ReScue(Generator):
  def query(self, regex, rngSeed, inputsPerGenerator, generatorTimeout):
    # TODO: ReScue does not support RNG
    return self.queryHelper(regex, '{} --regex-file {{}} --out-file {{}} --timeout {} 2>/tmp/gen-input.log' \
        .format(self.driver, generatorTimeout))

class Generator_MutRex(Generator):
  def query(self, regex, rngSeed, inputsPerGenerator, generatorTimeout):
    # TODO: MutRex does not support RNG
    return self.queryHelper(regex, '{} --regex-file {{}} --out-file {{}} --timeout {} 2>/tmp/gen-input.log' \
        .format(self.driver, generatorTimeout))

class Generator_Brics(Generator):
  def query(self, regex, rngSeed, inputsPerGenerator, generatorTimeout):
    return self.queryHelper(regex, '{} --regex-file {{}} --out-file {{}} --seed {} --timeout {} 2>/tmp/gen-input.log' \
        .format(self.driver, rngSeed, generatorTimeout))

# Verify that the generators can be found
DRIVER_PATH = os.path.join(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT'], 'analysis', 'semantic', 'input-generation', 'generators', 'drivers')
INPUT_GENERATORS = [
  Generator_Rex('Rex', os.path.join(DRIVER_PATH, 'query-rex.py')),
  Generator_EGRET('EGRET', os.path.join(DRIVER_PATH, 'query-egret.py')),
  Generator_ReScue('ReScue', os.path.join(DRIVER_PATH, 'query-rescue.py')),
  Generator_MutRex('MutRex', os.path.join(DRIVER_PATH, 'query-mutrex.py')),
  Generator_Brics('Brics', os.path.join(DRIVER_PATH, 'query-brics.py')),
]
for inputGen in INPUT_GENERATORS:
  if not inputGen.driverExists():
    libLF.log('Error, cannot find driver for {} ({})'.format(inputGen.name, inputGen.driver))
    sys.exit(1)

##########

class MyTask(libLF.parallel.ParallelTask):
  def __init__(self, regex, rngSeed, inputsPerGenerator, generatorTimeout):
    self.regex = regex
    self.rngSeed = rngSeed
    self.inputsPerGenerator = inputsPerGenerator
    self.generatorTimeout = generatorTimeout
  
  def run(self):
    try:
      libLF.log('Working on regex: /{}/'.format(self.regex.pattern))

      # Drive the various input generators
      stringsByProducer = {}
      nStrings = 0
      for inputGen in INPUT_GENERATORS:
        libLF.log('Getting inputs from {}'.format(inputGen.name))
        # Query the generator
        gqrs = inputGen.query(self.regex, self.rngSeed, self.inputsPerGenerator, self.generatorTimeout)
        # Unpack the responses
        for gqr in gqrs:
          # Enforce inputsPerGenerator
          _inputs = gqr.inputs
          if len(_inputs) > self.inputsPerGenerator:
            _inputs = random.sample(_inputs, self.inputsPerGenerator)

          stringsByProducer['{}-{}'.format(inputGen.name, gqr.name)] = _inputs
          nStrings += len(_inputs)
          libLF.log('Got {} inputs from {}-{}'.format(len(_inputs), inputGen.name, gqr.name))

      #libLF.log('sbp = {}'.format(stringsByProducer))
      # TODO Consider introducing mutants here
      rpai = libLF.RegexPatternAndInputs().initFromRaw(self.regex.pattern, stringsByProducer)
      #libLF.log('rpai {}: {}'.format(rpai, rpai.toNDJSON()))

      # Return
      libLF.log('Completed regex /{}/ -- {} inputs'.format(self.regex.pattern, nStrings))
      return rpai
    except KeyboardInterrupt:
      raise
    except BaseException as err:
      libLF.log('ERROR')
      Sys.exit(1)
      libLF.log(err)
      return err

################

def getTasks(regexFile, rngSeed, inputsPerGenerator, generatorTimeout):
  regexes = loadRegexFile(regexFile)
  tasks = [MyTask(regex, rngSeed, inputsPerGenerator, generatorTimeout) for regex in regexes]
  libLF.log('Prepared {} tasks'.format(len(tasks)))
  return tasks

def loadRegexFile(regexFile):
  """Return a list of Regex's"""
  regexes = []
  libLF.log('Loading regexes from {}'.format(regexFile))
  with open(regexFile, 'r') as inStream:
    for line in inStream:
      line = line.strip()
      if len(line) == 0:
        continue
      
      try:
        # Build a Regex
        regex = libLF.Regex()
        regex.initFromNDJSON(line)

        regexes.append(regex)
      except KeyboardInterrupt:
        raise
      except BaseException as err:
        libLF.log('Exception parsing line:\n  {}\n  {}'.format(line, err))
        traceback.print_exc()

    libLF.log('Loaded {} regexes from {}'.format(len(regexes), regexFile))
    return regexes

################

def main(regexFile, outFile, parallelism, rngSeed, inputsPerGenerator, generatorTimeout):
  libLF.log('regexFile {} outFile {} parallelism {} rngSeed {} inputsPerGenerator {} generatorTimeout {}' \
    .format(regexFile, outFile, parallelism, rngSeed, inputsPerGenerator, generatorTimeout))
  
  if 0 <= rngSeed:
    random.seed(rngSeed)

  #### Load data
  tasks = getTasks(regexFile, rngSeed, inputsPerGenerator, generatorTimeout)
  nRegexes = len(tasks)

  #### Process data

  # CPU-bound, no limits
  libLF.log('Submitting to map')
  results = libLF.parallel.map(tasks, parallelism,
    libLF.parallel.RateLimitEnums.NO_RATE_LIMIT, libLF.parallel.RateLimitEnums.NO_RATE_LIMIT,
    jitter=False)
  
  #### Emit results

  libLF.log('Writing results to {}'.format(outFile))
  nSuccesses = 0
  nExceptions = 0
  with open(outFile, 'w') as outStream:
    for rpai in results:
        # Emit
        if type(rpai) is libLF.RegexPatternAndInputs:
          nSuccesses += 1
          libLF.log('  Generated {} unique inputs for regex /{}/' \
            .format(len(rpai.getUniqueInputs()), rpai.pattern))
          outStream.write(rpai.toNDJSON() + '\n')
        else:
          nExceptions += 1
  libLF.log('Successfully performed input generation for {} regexes, {} exceptions'.format(nSuccesses, nExceptions))

#####################################################

# Parse args
parser = argparse.ArgumentParser(description='Generate input strings for a set of libLF.Regex\'s.')
parser.add_argument('--regex-file', type=str, help='In: File of libLF.Regex objects', required=True,
  dest='regexFile')
parser.add_argument('--out-file', type=str, help='Out: File of libLF.RegexPatternAndInputs objects', required=True,
  dest='outFile')
parser.add_argument('--parallelism', type=int, help='Maximum cores to use', required=False, default=libLF.parallel.CPUCount.CPU_BOUND,
  dest='parallelism')
parser.add_argument('--seed', type=int, help='RNG seed to use, where supported (default 1. -1: no seed) ', required=False, default=1,
  dest='seed')
parser.add_argument('--max-inputs-per-generator', type=int, help='At most N inputs per generator. If exceeded, a random subset is chosen (default 1000; -1 means no limit)', required=False, default=1000,
  dest='inputsPerGenerator')
parser.add_argument('--generator-timeout', type=float, help='Time out generator if it takes more than T seconds, and scrape the output for the strings generated so far (default 10, give -1 for no limit)', required=False, default=10,
  dest='generatorTimeout')
args = parser.parse_args()

# Here we go!
main(args.regexFile, args.outFile, args.parallelism, args.seed, args.inputsPerGenerator, args.generatorTimeout)
