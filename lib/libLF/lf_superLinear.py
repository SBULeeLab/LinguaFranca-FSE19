"""Lingua Franca: Super linear regex classes

These are wrappers for the scripts in vuln-regex-detector/.
"""

import libLF
import json

import os
import tempfile

class PumpPair:
  """Represents a prefix + pump pair as part of a libLF.EvilInput"""
  def __init__(self):
    self.prefix = None
    self.pump = None
  
  def initFromRaw(self, prefix, pump):
    self.prefix = prefix
    self.pump = pump
    return self
  
  def initFromNDJSON(self, jsonStr):
    obj = libLF.fromNDJSON(jsonStr)
    return self.initFromDict(obj)

  def initFromDict(self, obj):
    self.prefix = obj['prefix']
    self.pump = obj['pump']
    return self
  
  def toNDJSON(self):
    _dict = {
      'prefix': self.prefix,
      'pump': self.pump
    }
    return json.dumps(_dict)
  
class EvilInput:
  """Represents regex input intended to trigger super-linear behavior"""
  def __init__(self):
    self.couldParse = False
    self.pumpPairs = None
    self.suffix = None

  def initFromRaw(self, couldParse, pumpPairs=None, suffix=None):
    self.couldParse = couldParse
    if self.couldParse:
      self.pumpPairs = pumpPairs
      self.suffix = suffix
    else:
      self.pumpPairs = None
      self.suffix = None
    return self
  
  def initFromDict(self, obj):
    self.couldParse = obj['couldParse']
    if self.couldParse:
      self.pumpPairs = [
          PumpPair().initFromDict(ppDict) for ppDict in obj['pumpPairs']
      ]
      self.suffix = obj['suffix']
    return self

  def initFromNDJSON(self, jsonStr):
    obj = libLF.fromNDJSON(jsonStr)
    return self.initFromDict(obj)

  def toNDJSON(self):
    _dict = {
      'couldParse': self.couldParse
    }
    if self.couldParse:
      _dict['pumpPairs'] =  [json.loads(p.toNDJSON()) for p in self.pumpPairs]
      _dict['suffix'] = self.suffix
    
    return json.dumps(_dict)

class SLRegexDetectorOpinion:
  """Represents an SL regex detector's opinion

  detectorName: str
  pattern: str
  timedOut: bool
  canAnalyze: bool
  isVuln: bool

  if not timedOut:
    patternVariant: str: pattern analyzed by this detector
    if isVuln:
      evilInputs: EvilInput[]
  """
  def __init__(self):
    self.pattern = 'UNINITIALIZED'
    self.detectorName = 'UNINITIALIZED'
    self.timedOut = False
    self.canAnalyze = False
    self.isVuln = False
 
  def initFromRaw(self, pattern=None, rawOpinion=None):
    libLF.log('SLRDO: rawOpinion {}'.format(rawOpinion))
    self.pattern = pattern
    self.detectorName = rawOpinion['name']

    if rawOpinion['opinion'] == 'TIMEOUT':
      self.timedOut = True
      self.canAnalyze = False
      self.isVuln = False
    elif rawOpinion['opinion'] == 'INTERNAL-ERROR':
      self.timedOut = False
      self.canAnalyze = False
      self.isVuln = False
    else:
      self.patternVariant = rawOpinion['patternVariant']

      self.canAnalyze = rawOpinion['opinion']['canAnalyze'] == 1

      if self.canAnalyze:
        self.isVuln = rawOpinion['opinion']['isSafe'] == 0
      else:
        self.isVuln = False

      if self.isVuln:
        self.evilInputs = []
        for rawEI in rawOpinion['opinion']['evilInput']:
          if type(rawEI) is str:
            ei = EvilInput().initFromRaw(False)
          else:
            pumpPairs = [
              PumpPair().initFromRaw(rawPP['prefix'], rawPP['pump']) 
              for rawPP in rawEI['pumpPairs']
            ]
            ei = EvilInput().initFromRaw(True, pumpPairs, rawEI['suffix'])
          self.evilInputs.append(ei)
    return self

  def toNDJSON(self):
    _dict = {
      'detectorName': self.detectorName,
      'pattern': self.pattern,
      'canAnalyze': self.canAnalyze,
      'timedOut': self.timedOut,
      'isVuln': self.isVuln
    }

    if not self.timedOut:
      _dict['patternVariant'] = self.patternVariant
      if self.isVuln:
        _dict['evilInputs'] = [json.loads(ei.toNDJSON()) for ei in self.evilInputs]
    return json.dumps(_dict)
  
  def initFromNDJSON(self, jsonStr):
    obj = libLF.fromNDJSON(jsonStr)
    return self.initFromDict(obj)
  
  def initFromDict(self, obj):
    self.detectorName = obj['detectorName']
    self.pattern = obj['pattern']
    self.canAnalyze = obj['canAnalyze']
    self.timedOut = obj['timedOut']
    self.isVuln = obj['isVuln']

    if not self.timedOut:
      self.patternVariant = obj['patternVariant']
      if self.isVuln:
        self.evilInputs = [
          EvilInput().initFromDict(eiDict) for eiDict in obj['evilInputs']
        ]
    return self

class SLRegexValidation:
  """Represents the result of validating a DetectorOpinion in a language

  pattern: str
  evilInput: EvilInput
  language: str
  validPattern: bool <-- if false, pattern is not supported in this language
  nPumps: int
  timeLimit: int
  timedOut: bool
  """

  def __init__(self, pattern, evilInput, rawValidationResult):
    self.pattern = pattern
    self.evilInput = evilInput

    libLF.log('SLRV: rawVR: {}'.format(rawValidationResult))

    self.language = rawValidationResult['language']
    self.validPattern = rawValidationResult['validPattern'] 
    self.nPumps = rawValidationResult['nPumps']
    self.timeLimit = rawValidationResult['timeLimit'] == 1
    self.timedOut = rawValidationResult['timedOut'] == 1

class SLRegexAnalysis:
  # TODO Break this into separate SLRA and SLRAPerformer classes.
  """Performs and also represents analysis of a regex for SL behavior

  If you are using this to perform analysis:
    Members get initialized by various methods:
    
    init:
      regex: a libLF.Regex
    After, you can call:

    queryDetectors:
      detectorOpinions[] : SLRegexDetectorOpinion[]
    After, you can call:
    
    validateDetectorOpinionsInLang:
      lang_validPattern{} : { 'JavaScript' -> False, 'Perl' -> True, ... }
      lang_pump2timedOut{} : { 'JavaScript' -> { 100: False, 500000 : True }, ... }
      (Call with multiple languages as needed)

      This gives a simple way to check whether this pattern has super-linear behavior:
        lang_validPattern[lang] and True in lang_pump2timedOut[lang].values()
      and for exp-time behavior:
        lang_validPattern[lang] and lang_pump2timedOut[lang][SLRegexAnalysis.EXP_PUMPS]

  If you are using this to represent analysis:
    The SLRA analysis must have been completely performed.
    If so, use initFromNDJSON() and access the members described above.
  """

  DEFAULT_VULN_REGEX_DETECTOR_ROOT = \
    os.path.join(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT'], 'analysis', 'performance', 'vuln-regex-detector')
  
  MATCH_TIMEOUT_SEC = 5

  EXP_PUMPS = 1 * 100 # This triggers all the true exp vulns I've seen
  POW_PUMPS = 500 * 1000 # This triggers most power vulns I've seen

  SUPPORTED_LANGS = [
    'javascript',
    'php',
    'ruby',
    'rust',
    'perl',
    'python',
    'go',
    'java'
  ]

  PREDICTED_PERFORMANCE = {
    'LIN': 'LIN',
    'POW': 'POW',
    'EXP': 'EXP'
  }

  INVALID_PATTERN = 'INVALID PATTERN'

  def __init__(self, regex=None, slTimeout=MATCH_TIMEOUT_SEC, powerPumps=POW_PUMPS, vrdPath=DEFAULT_VULN_REGEX_DETECTOR_ROOT):
    """Two purposes: (1) performing analysis, (2) understanding results
    
    Args:
      regex: libLF.Regex: provide if you want to do analysis.
      slTimeout: int: Threshold to declare a match super-linear (seconds)
      powerPumps: int: Number of pumps to use to identify power SL behavior (e.g. quadratic)
      VRD_PATH: str: Where to find .../vuln-regex-detector/ ?
    
    If you already did analysis and want to understand results,
      call this with defaults and use initFromNDJSON().
    """
    self.regex = regex
    self.slTimeout = slTimeout
    self.powerPumps = powerPumps
    self.vrdPath = vrdPath

    self.queryDetectorsScript = os.path.join(vrdPath, 'src', 'detect', 'detect-vuln.pl')
    self.testInLanguageScript = os.path.join(vrdPath, 'src', 'validate', 'validate-vuln.pl')

    self.detectorOpinions = []
    self.lang_validPattern = {}
    # TODO Instead of tracking pumps we should just say "EXP" or "LIN" directly.
    self.lang_pump2timedOut = {}

  def toNDJSON(self):
    _dict = {
      'regex': json.loads(self.regex.toNDJSON()),
      'slTimeout': self.slTimeout,
      'powerPumps': self.powerPumps,
      'detectorOpinions': [json.loads(do.toNDJSON()) for do in self.detectorOpinions],
      'lang_validPattern': self.lang_validPattern,
      'lang_pump2timedOut': self.lang_pump2timedOut
    }
    return json.dumps(_dict)
  
  def initFromNDJSON(self, jsonStr):
    obj = libLF.fromNDJSON(jsonStr)
    self.regex = libLF.Regex().initFromDict(obj['regex'])

    if 'slTimeout' in obj:
      self.slTimeout = obj['slTimeout']
    else:
      self.slTimeout = self.MATCH_TIMEOUT_SEC
    if 'powerPumps' in obj:
      self.powerPumps = obj['powerPumps']
    else:
      self.powerPumps = self.POW_PUMPS

    self.detectorOpinions = [
      SLRegexDetectorOpinion().initFromDict(doDict) for doDict in obj['detectorOpinions']
    ]

    # Get the lang_validPattern dict.
    # The keys are bools, easy conversion.
    self.lang_validPattern = obj['lang_validPattern']

    # Get the lang_pump2timedOut dict.
    # The keys on pump2timedOut should be integers, but they may have been
    # converted to strings. Convert back again.
    self.lang_pump2timedOut = obj['lang_pump2timedOut']
    for lang in self.lang_pump2timedOut:
      pump2timedOut = self.lang_pump2timedOut[lang]
      for k in pump2timedOut:
        if type(k) is str:
          pump2timedOut[int(k)] = pump2timedOut[k]
          del pump2timedOut[k]
  
  def queryDetectors(self):
    """Query detectors. Returns self"""

    # Build query
    query = {
      'pattern': self.regex.pattern,
      'timeLimit': 60, # Num seconds each detector gets to make a decision about this regex.
      'memoryLimit': 2048*1024, # KB each detector gets to use to make a decision. TODO Update VRD docs which say 'in MB'? But cf. detect-vuln.pl:59
    }

    # Query from tempfile
    with tempfile.NamedTemporaryFile(prefix='SLRegexAnalysis-queryDetectors-', suffix='.json', delete=True) as ntf:
      libLF.writeToFile(ntf.name, json.dumps(query))
      rc, out = libLF.runcmd("VULN_REGEX_DETECTOR_ROOT={} '{}' '{}' 2>>/tmp/err" \
        .format(self.vrdPath, self.queryDetectorsScript, ntf.name))
      out = out.strip()
    libLF.log('Got rc {} out\n{}'.format(rc, out))

    # TODO Not sure if this can go wrong.
    assert(rc == 0)

    self.detectorOpinions = self._qd_convOutput2DetectorOpinions(out)
    # TODO Not sure if this can go wrong.
    assert(self.detectorOpinions is not None)

    maybeVuln_exact = False
    maybeVuln_variant = False
    for do in self.detectorOpinions:
      if do.isVuln and len(list(filter(lambda ei: ei.couldParse, do.evilInputs))) > 0:
        if do.pattern == do.patternVariant:
          maybeVuln_exact = True
        else:
          maybeVuln_variant = True
    libLF.log('Maybe vuln: exact {} variant {}'.format(maybeVuln_exact, maybeVuln_variant))

    try:
      os.remove(queryFile)
      pass
    except:
      pass

    return self
    
  def _qd_convOutput2DetectorOpinions(self, queryDetectorsOutput):
    try:
      detectorOpinions = []
      obj = json.loads(queryDetectorsOutput)
      for rawDO in obj['detectorOpinions']:
        do = SLRegexDetectorOpinion().initFromRaw(obj['pattern'], rawDO)
        detectorOpinions.append(do)
      return detectorOpinions
    except BaseException as err:
      # TODO Not sure if this can go wrong.
      libLF.log('Could not parse queryDetectorsOutput: <{}> --> {}'.format(err, queryDetectorsOutput))
      return None

  def validateDetectorOpinionsInLang(self, lang):
    """Test the DOs in this language. Returns self"""
    lang = lang.lower()
    if lang not in self.SUPPORTED_LANGS:
      raise ValueError('Unsupported language {}'.format(lang))
    libLF.log('Validating detector opinions for <{}> in {}'.format(self.regex.pattern, lang))

    self.lang_pump2timedOut[lang] = {}
    for do in self.detectorOpinions:
      if do.isVuln:
        for ei in do.evilInputs:
          if ei.couldParse:
            # Try this EvilInput from this SLRegexDetectorOpinion
            slrvs = self._testEvilInputInLang(ei, lang)
            for slrv in slrvs:
              # Is this a valid pattern?
              if slrv.validPattern:
                self.lang_validPattern[lang] = True
                # Did we get a timeout this time?
                if slrv.nPumps not in self.lang_pump2timedOut[lang]:
                  # Never tried this nPumps before, keep whatever we got
                  self.lang_pump2timedOut[lang][slrv.nPumps] = slrv.timedOut
                elif self.lang_pump2timedOut[lang][slrv.nPumps] is False:
                  # Tried this nPumps before but didn't get a timeout, keep whatever we got
                  self.lang_pump2timedOut[lang][slrv.nPumps] = slrv.timedOut
                else:
                  # We have tried this nPumps before and have seen it timeout, so don't care
                  pass
              else:
                # Invalid pattern, mark it as such
                self.lang_validPattern[lang] = False

    libLF.log('validateDetectorOpinionsInLang: regex <{}> lang_pump2timedOut[{}] = {}'.format(self.regex.pattern, lang, self.lang_pump2timedOut[lang]))
    return self
  
  def _testEvilInputInLang(self, evilInput, lang):
    """Returns an SLRegexValidation[] with EXP and POW pumps"""
    # Build query
    query = {
      'language': lang.lower(),
      'pattern': self.regex.pattern,
      'evilInput': json.loads(evilInput.toNDJSON()),
      'nPumps': -1, # Needs a valid value
      'timeLimit': self.slTimeout,
    }

    slRegexVals = []
    for nPumps in [self.EXP_PUMPS, self.powerPumps]:
      query['nPumps'] = nPumps
      libLF.log('query: {}'.format(json.dumps(query)))
      with tempfile.NamedTemporaryFile(prefix='SLRegexAnalysis-validateOpinion-', suffix='.json', delete=True) as ntf:
        libLF.writeToFile(ntf.name, json.dumps(query))
        rc, out = libLF.runcmd("VULN_REGEX_DETECTOR_ROOT={} '{}' '{}' 2>>/tmp/err" \
          .format(self.vrdPath, self.testInLanguageScript, ntf.name))
        out = out.strip()
      libLF.log('Got rc {} out\n{}'.format(rc, out))
      slRegexVals.append(SLRegexValidation(self.regex.pattern, evilInput, json.loads(out)))

    return slRegexVals

  def predictedPerformanceInLang(self, lang):
    """PREDICTED_PERFORMANCE in this lang

    If not attempted (presumably either due to no DO said it was vulnerable or could process it),
      we treat this as a LIN pattern. A negative, true or false.
      IMPORTANT: This assumes that every pattern is tested in the lang being queried.

    Returns self.INVALID_PATTERN if not supported
    """
    lang = lang.lower()

    try:
      if not self.lang_validPattern[lang]:
        return self.INVALID_PATTERN
      p2to = self.lang_pump2timedOut[lang]
    except:
      # Key error if we never attempted.
      # This should only occur if none of the DOs said it was vulnerable...
      for do in self.detectorOpinions:
        #libLF.log(do.toNDJSON())
        assert(not do.canAnalyze or not do.isVuln or not do.evilInputs[0].couldParse)
      # ...in which case this regex is linear.
      return self.PREDICTED_PERFORMANCE['LIN']

    # EXP, POW: Did we try this many pumps, and did it time out?
    if self.EXP_PUMPS in p2to and p2to[self.EXP_PUMPS]:
      #libLF.log('Predicted behavior in {}: {}'.format(lang, self.PREDICTED_PERFORMANCE['EXP']))
      return self.PREDICTED_PERFORMANCE['EXP']
    elif self.powerPumps in p2to and p2to[self.powerPumps]:
      #libLF.log('Predicted behavior in {}: {}'.format(lang, self.PREDICTED_PERFORMANCE['POW']))
      return self.PREDICTED_PERFORMANCE['POW']
    
    # Either we never attempted pumps (because no detector had a guess)
    # or we attempted them and they did not time out (because detector was wrong).
    #libLF.log('Predicted behavior in {}: {}'.format(lang, self.PREDICTED_PERFORMANCE['LIN']))
    # TODO What about languages in which the regex could not be constructed?
    return self.PREDICTED_PERFORMANCE['LIN']

  def everTimedOut(self):
    for lang in self.lang_pump2timedOut:
      # Did we predict super-linear behavior in any language?
      if self.timedOutInLang(lang):
        #libLF.log('Timed out in {}'.format(lang))
        return True
    return False
  
  def timedOutInLang(self, lang):
    return self.predictedPerformanceInLang(lang) is self.PREDICTED_PERFORMANCE['POW'] \
           or self.predictedPerformanceInLang(lang) is self.PREDICTED_PERFORMANCE['EXP']

  def predictedPerformancePortingScore(self, sourceLang, destLang):
    """Returns a "performance porting score" from sourceLang to destLang
    
    The larger the absolute value of the score, the greater the change in performance.
    Positive scores indicate faster performance in destLang compared to sourceLang.
    A score of zero means no difference.
    Negative scores indicate slower peformance in destLang compared to sourceLang.

    A score of None means that no comparison was possible.
    This indicates that the regex was not supported in sourceLang and/or destLang.
      (or not tested in one of them, but don't do that!)
    """

    # The more desirable the performance, the higher the score
    # If we go from worse to better performance, (new - old) is positive.
    # If we go from better to worse performance, (new - old) is negative.
    # Larger jumps (e.g. EXP -> LIN) are weighted more than smaller jumps (e.g. EXP -> POW).
    measured_perf2val = {
      self.PREDICTED_PERFORMANCE['LIN']: 3,
      self.PREDICTED_PERFORMANCE['POW']: 2,
      self.PREDICTED_PERFORMANCE['EXP']: 1
    }

    # None if we don't have a prediction in one of the langs
    for lang in [sourceLang, destLang]:
      if self.predictedPerformanceInLang(lang) not in measured_perf2val.keys():
        return None

    score = measured_perf2val[self.predictedPerformanceInLang(destLang)] - \
            measured_perf2val[self.predictedPerformanceInLang(sourceLang)]
    #libLF.log('{} -> {}: porting score {}' \
    #  .format(self.predictedPerformanceInLang(sourceLang),
    #          self.predictedPerformanceInLang(destLang),
    #          score))
    return score
