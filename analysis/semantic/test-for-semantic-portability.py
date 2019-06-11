#!/usr/bin/env python3
# Given a regex, check if it exhibits different behavior in different languages.
# This analysis can run single-node many-core.

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
import random
import subprocess

##########

DELETE_TMP_FILES = True
MAX_REGEX_QUERY_TIME_SEC = 30 # Querying a lot of inputs is still quite fast. Any timeouts are due to SL behavior.

# Dependencies
INPUT_GENERATOR = os.path.join(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT'], 'bin', 'gen-input-for-regex.py')
libLF.log('Config:\n  INPUT_GENERATOR {}'.format(INPUT_GENERATOR))

langCLIDir = os.path.join(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT'], 'bin')
lang2cli = {
  'go':     os.path.join(langCLIDir, 'check-regex-behavior-in-go'),
  'java':   os.path.join(langCLIDir, 'check-regex-behavior-in-java.pl'),
  'javascript':   os.path.join(langCLIDir, 'check-regex-behavior-in-node.js'),
  'perl':   os.path.join(langCLIDir, 'check-regex-behavior-in-perl.pl'),
  'php':    os.path.join(langCLIDir, 'check-regex-behavior-in-php.php'),
  'python': os.path.join(langCLIDir, 'check-regex-behavior-in-python.py'),
  'ruby':   os.path.join(langCLIDir, 'check-regex-behavior-in-ruby.rb'),
  'rust':   os.path.join(langCLIDir, 'check-regex-behavior-in-rust'),
}
libLF.log('Config:\n  language CLIs: {}'.format(json.dumps(lang2cli)))

libLF.checkShellDependencies([INPUT_GENERATOR] + list(lang2cli.values()))

class MyTask(libLF.parallel.ParallelTask):
  def __init__(self, regex, maxInputsPerGenerator, rngSeed, timeoutPerGenerator):
    self.regex = regex
    self.maxInputsPerGenerator = maxInputsPerGenerator
    self.rngSeed = rngSeed
    self.timeoutPerGenerator = timeoutPerGenerator

  def _queryRegexInLang(self, pattern, queryFile, language):
    """Query behavior of <pattern, input[]> in language

    pattern: str: regex pattern
    queryFile: str: name of file containing the query to use
    language: str: name of language to test in

    @returns libLF.RegexEvaluationResult[]
    May throw a timeout exception
    """
    language = language.lower()
    driver = lang2cli[language]

    # The output can be quite verbose when using lists of inputs,
    # so redirect to a temp file to ensure buffering and piping aren't problematic
    # in the shell. 
    with tempfile.NamedTemporaryFile(prefix='SemanticAnalysis-queryRegexInLang-OutFile-', 
                                     suffix='.json',
                                     delete=DELETE_TMP_FILES) as outFile:
      cmd = [driver, queryFile]
      libLF.log("Command: {} > {}".format(" ".join(cmd), outFile.name))
      # This may throw -- catch higher up
      completedProcess = subprocess.run(cmd, stdout=outFile, stderr=subprocess.DEVNULL, timeout=MAX_REGEX_QUERY_TIME_SEC)
      outFile.seek(0) # Rewind so we can read

      libLF.log("language {} rc {}".format(language, completedProcess.returncode))
      if completedProcess.returncode == 0:
        queryResult = json.loads(outFile.read().decode('utf-8'))

        rers = []
        for result in queryResult["results"]:
          matched = result["matched"]
          if matched:
            rawMC = result["matchContents"]
          else:
            rawMC = { "matchedString": "", "captureGroups": [] }

          mc = libLF.MatchContents().initFromRaw(rawMC["matchedString"], rawMC["captureGroups"])
          matchResult = libLF.MatchResult().initFromRaw(matched, mc)
          rer = libLF.RegexEvaluationResult(pattern, result["input"], language, matchResult)
          rers.append(rer)
        return rers
      else:
        return []
  
  def _getInputs(self):
    """inputs: unique str[], collapsing the result from INPUT_GENERATOR"""

    # For testing
    #return ["abc"] # TODO
    #return [" ", "\t", "\r", "\n", "\v"] # Whitespace -- Go does not include \n ?
    #return ["aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa!"] # For SL testing

    # Query from tempfile
    with tempfile.NamedTemporaryFile(prefix='SemanticAnalysis-genInputs-', suffix='.json', delete=DELETE_TMP_FILES) as queryFile, \
         tempfile.NamedTemporaryFile(prefix='SemanticAnalysis-outFile-', suffix='.json', delete=DELETE_TMP_FILES) as outFile:
      libLF.writeToFile(queryFile.name, self.regex.toNDJSON())
      rc, out = libLF.runcmd("'{}' --regex-file '{}' --out-file '{}' --parallelism 1 --seed {} --max-inputs-per-generator {} --generator-timeout {} 2>/dev/null" \
        .format(INPUT_GENERATOR, queryFile.name, outFile.name,
                self.rngSeed, # Propagate reproducibility into the generators
                self.maxInputsPerGenerator, # Reduce the size of intermediate tmp files
                self.timeoutPerGenerator, # Ensure reasonable time is taken
                ))
      out = out.strip()
      rpaiFileContents = outFile.read().decode("utf-8")
      #libLF.log('Got rc {} scriptOut {} rpai as JSON {}'.format(rc, out, rpaiFileContents))
    # This should never fail
    assert(rc == 0)

    rpai = libLF.RegexPatternAndInputs().initFromNDJSON(rpaiFileContents)
    inputs = []
    libLF.log('_getInputs: The {} producers yielded {} total inputs' \
      .format(len(rpai.stringsByProducer), len(rpai.getUniqueInputs())))
    for producer in rpai.stringsByProducer:
      # Apply per-generator input limit
      producerInputs = rpai.stringsByProducer[producer]
      if 0 < self.maxInputsPerGenerator and self.maxInputsPerGenerator < len(producerInputs):
        libLF.log('_getInputs: producer {} yielded {} inputs, reducing to {}' \
          .format(producer, len(producerInputs), self.maxInputsPerGenerator))
        producerInputs = random.sample(producerInputs, self.maxInputsPerGenerator)

      # Add these inputs
      inputs += producerInputs
    return list(set(inputs + ["a"])) # Always test at least one string

  def _evaluateRegex(self, pattern, testStrings, languages):
    """Evaluate this regex with these strings in this language
    
    pattern: str
    testStrings: str[]
    languages: str[]
    @returns dict { lang: libLF.RegexEvaluationResult[], ... } for this request
    """
    with tempfile.NamedTemporaryFile(prefix='SemanticAnalysis-evaluateRegex-queryFile-',
                                     suffix='.json',
                                     delete=DELETE_TMP_FILES) as queryFile:
      # We can use the same queryFile for each language
      query = {
        "pattern": pattern,
        "inputs": testStrings,
      }
      libLF.writeToFile(queryFile.name, json.dumps(query))

      lang2rers = {}
      for lang in languages:                                    
        try: # Might time out -- if so, just ignore the language 
          lang2rers[lang] = self._queryRegexInLang(pattern, queryFile.name, lang)
        except Exception as err:
          libLF.log('_evaluateRegex: exception in {}: {}'.format(lang, err))

      return lang2rers
  
  def run(self):
    try:
      libLF.log('Working on regex /{}/'.format(self.regex.pattern))

      # Get inputs
      inputs = self._getInputs()

      libLF.log('  Got {} inputs to test'.format(len(inputs)))
      libLF.log('  Testing each input in {} langs'.format(len(self.regex.supportedLangs)))

      # Check its behavior on each input in each lang
      #lang2rers = self._evaluateRegex(self.regex.pattern, inputs, ["python", "perl", "php", "ruby", "javascript", "java", "go", "rust"]) # TODO
      lang2rers = self._evaluateRegex(self.regex.pattern, inputs, self.regex.supportedLangs)

      # Build SDW's based on each RER
      possibleWitnesses = {} # keyed by inputString
      for testString in inputs:
        possibleWitnesses[testString] = libLF.SemanticDifferenceWitness().initFromRaw(self.regex.pattern, testString)

      for _, rers in lang2rers.items():
        for rer in rers:
          possibleWitnesses[rer.input].addRER(rer)

      # See if there were any true witnesses
      trueWitnesses = []
      for _, pw in possibleWitnesses.items():
        if pw.isTrueWitness():
          libLF.log("  Got a witness!")
          trueWitnesses.append(pw)
      
      self.regex.nUniqueInputsTested = len(inputs)
      self.regex.semanticDifferenceWitnesses = trueWitnesses

      # Return
      libLF.log('Completed regex /{}/ ({} witnesses out of {} inputs)' \
        .format(self.regex.pattern, len(self.regex.semanticDifferenceWitnesses), self.regex.nUniqueInputsTested))
      sys.stderr.flush()
      return self.regex
    except KeyboardInterrupt:
      raise
    except BaseException as err:
      libLF.log('Error handling regex /{}/: {}'.format(self.regex.pattern, err))
      sys.stderr.flush()
      return err

################

def getTasks(regexFile, maxInputsPerGenerator, rngSeed, generatorTimeout):
  regexes = loadRegexFile(regexFile)
  tasks = [MyTask(regex, maxInputsPerGenerator, rngSeed, generatorTimeout) for regex in regexes]
  libLF.log('Prepared {} tasks'.format(len(tasks)))
  return tasks

def loadRegexFile(regexFile):
  """Return a list of Regex's"""
  regexes = []
  libLF.log('Loading regexes from {}'.format(regexFile))
  with open(regexFile, 'r', encoding='utf-8') as inStream:
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

def main(regexFile, outFile, parallelism, maxInputsPerGenerator, rngSeed, generatorTimeout):
  libLF.log('regexFile {} outFile {} parallelism {} maxInputsPerGenerator {} rngSeed {} generatorTimeout {}' \
    .format(regexFile, outFile, parallelism, maxInputsPerGenerator, rngSeed, generatorTimeout))

  #### Load data
  libLF.log('\n\n-----------------------')
  libLF.log('Loading regexes from {}'.format(regexFile))

  tasks = getTasks(regexFile, maxInputsPerGenerator, rngSeed, generatorTimeout)
  nRegexes = len(tasks)

  #### Process data
  libLF.log('\n\n-----------------------')
  libLF.log('Testing for semantic portability problems')

  # CPU-bound, no limits
  libLF.log('Submitting to map')
  results = libLF.parallel.map(tasks, parallelism,
    libLF.parallel.RateLimitEnums.NO_RATE_LIMIT, libLF.parallel.RateLimitEnums.NO_RATE_LIMIT,
    jitter=False)

  #### Emit results

  libLF.log('\n\n-----------------------')
  libLF.log('Writing results to {}'.format(outFile))
  nSuccesses = 0
  nExceptions = 0
  completedRegexes = []
  with open(outFile, 'w') as outStream:
    for regex in results:
        # Emit
        if type(regex) is libLF.Regex:
          nSuccesses += 1
          outStream.write(regex.toNDJSON() + '\n')
          completedRegexes.append(regex)
        else:
          nExceptions += 1
  libLF.log('Successfully performed cross-language semantic equivalence testing on {} regexes, {} exceptions'.format(nSuccesses, nExceptions))

  #### Analyze the successful XXX's for a quick summary

  libLF.log('\n\n-----------------------')
  libLF.log('Generating a quick summary of regex cross-language semantic equivalence')

  libLF.log('--------------------')
  libLF.log('Summary')
  libLF.log('--------------------')

  nRegexesWithDifferences = 0
  for regex in completedRegexes:
    if len(regex.semanticDifferenceWitnesses) > 0:
      nRegexesWithDifferences += 1
  libLF.log('\n  {} ({:.2f}%) of the {} completed regexes had at least one witness for different behavior' \
    .format(nRegexesWithDifferences, 100 * (nRegexesWithDifferences/len(completedRegexes)), len(completedRegexes)))

#####################################################

# Parse args
parser = argparse.ArgumentParser(description='Test a set of libLF.Regex\'s for different behavior in different languages')
parser.add_argument('--regex-file', type=str, help='In: File of libLF.Regex objects that have supportedLangs populated', required=True,
  dest='regexFile')
parser.add_argument('--out-file', type=str, help='Out: File of libLF.Regex objects with the semanticDifferenceWitnesses field populated', required=True,
  dest='outFile')
parser.add_argument('--parallelism', type=int, help='Maximum cores to use', required=False, default=libLF.parallel.CPUCount.CPU_BOUND,
  dest='parallelism')
parser.add_argument('--max-inputs-per-generator', type=int, help='Maximum inputs to use from each generator (default 100; -1 means "all")', required=False, default=100,
  dest='maxInputsPerGenerator')
parser.add_argument('--rngSeed', type=int, help='Seed to use for reproducibility (default -1: random seed)', required=False, default=-1,
  dest='rngSeed')
parser.add_argument('--generator-timeout', type=float, help='Time out input generators if they takes more than T seconds, and scrape the output for the strings generated so far (default 10, give -1 for no limit)', required=False, default=10,
  dest='generatorTimeout')
args = parser.parse_args()

if args.rngSeed != -1:
  libLF.log("SEED: {}".format(args.rngSeed))
  random.seed(args.rngSeed)

# Here we go!
main(args.regexFile, args.outFile, args.parallelism, args.maxInputsPerGenerator, args.rngSeed, args.generatorTimeout)
