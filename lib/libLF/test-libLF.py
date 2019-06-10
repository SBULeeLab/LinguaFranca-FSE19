#!/usr/bin/env python3

# Import our lib
import os
import sys
sys.path.append('{}/lib'.format(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT']))
import libLF

import json
import re

import time

import unittest

#####
# Util
#####

class UtilTest(unittest.TestCase):
  def test_log(self):
    libLF.log('Testing log')

  def test_hashString(self):
    str1 = 'abc'
    str2 = 'def'
    self.assertEqual(libLF.hashString(str1), libLF.hashString(str1))
    self.assertEqual(libLF.hashString(str2), libLF.hashString(str2))
    self.assertNotEqual(libLF.hashString(str1), libLF.hashString(str2))

  def test_runcmd(self):
    testFile = os.path.join(os.sep, 'tmp', 'testFile-{}'.format(os.getpid()))

    createCmd = 'touch {}'.format(testFile)
    rc, out = libLF.runcmd(createCmd)
    self.assertEqual(rc, 0)

    destroyCmd = 'rm {}'.format(testFile)
    rc, out = libLF.runcmd(destroyCmd)
    self.assertEqual(rc, 0)

  def test_pathSplitAll(self):
    expPathAll = [os.sep, 'tmp', 'foo', 'bar', 'baz']
    absPath = os.path.join(expPathAll)
    pathAll = libLF.pathSplitAll(absPath)
    self.assertEqual(expPathAll, pathAll)

#####
# InternetRegexSource
#####

irsObj = {
  'uri': 'abc',
  'uriAliases': ['abc', 'abc'],
  'patterns': ['123', '456']
}

relObj = {
  'uri': 'abc',
  'uriAliases': ['abc', 'abc'],
  'patterns': ['123', '456'],
  'type': 'RegExLibRegexSource'
}

soObj = {
  'uri': 'abc',
  'uriAliases': ['abc', 'abc'],
  'patterns': ['123', '456'],
  'type': 'StackOverflowRegexSource'
}

class InternetRegexSourceTest(unittest.TestCase):
  def test_initFromRaw(self):
    internetSource = libLF.InternetRegexSource()
    internetSource.initFromRaw(irsObj['uri'], irsObj['uriAliases'], irsObj['patterns'])

    self.assertEqual(irsObj['uri'], internetSource.uri)
    self.assertEqual(irsObj['uriAliases'], internetSource.uriAliases)
    self.assertEqual(irsObj['patterns'], internetSource.patterns)

  def test_initFromNDJSON(self):
    internetSource = libLF.InternetRegexSource()
    internetSource.initFromNDJSON(json.dumps(irsObj))

    self.assertEqual(irsObj['uri'], internetSource.uri)
    self.assertEqual(irsObj['uriAliases'], internetSource.uriAliases)
    self.assertEqual(irsObj['patterns'], internetSource.patterns)

  def test_toNDJSON(self):
    internetSource = libLF.InternetRegexSource()
    internetSource.initFromNDJSON(json.dumps(relObj))
    obj = json.loads(internetSource.toNDJSON())

    self.assertEqual(irsObj, obj)

  def test_factory(self):
    _is = libLF.InternetRegexSource.factory(libLF.toNDJSON(relObj))
    self.assertEqual(_is.type, relObj['type'])

    _is = libLF.InternetRegexSource.factory(libLF.toNDJSON(soObj))
    self.assertEqual(_is.type, soObj['type'])

class RegExLibRegexSourceTest(unittest.TestCase):
  def test_initFromRaw(self):
    internetSource = libLF.RegExLibRegexSource()
    internetSource.initFromRaw(relObj['uri'], relObj['uriAliases'], relObj['patterns'])

    self.assertEqual(relObj['uri'], internetSource.uri)
    self.assertEqual(relObj['uriAliases'], internetSource.uriAliases)
    self.assertEqual(relObj['patterns'], internetSource.patterns)
    self.assertEqual(relObj['type'], internetSource.type)

  def test_initFromNDJSON(self):
    internetSource = libLF.RegExLibRegexSource()
    internetSource.initFromNDJSON(json.dumps(relObj))

    self.assertEqual(relObj['uri'], internetSource.uri)
    self.assertEqual(relObj['uriAliases'], internetSource.uriAliases)
    self.assertEqual(relObj['patterns'], internetSource.patterns)
    self.assertEqual(relObj['type'], internetSource.type)

  def test_toNDJSON(self):
    internetSource = libLF.RegExLibRegexSource()
    internetSource.initFromNDJSON(json.dumps(relObj))
    obj = json.loads(internetSource.toNDJSON())

    self.assertEqual(obj, relObj)

class StackOverflowRegexSourceTest(unittest.TestCase):
  def test_initFromRaw(self):
    internetSource = libLF.StackOverflowRegexSource()
    internetSource.initFromRaw(soObj['uri'], soObj['uriAliases'], soObj['patterns'])

    self.assertEqual(soObj['uri'], internetSource.uri)
    self.assertEqual(soObj['uriAliases'], internetSource.uriAliases)
    self.assertEqual(soObj['patterns'], internetSource.patterns)
    self.assertEqual(soObj['type'], internetSource.type)

  def test_initFromNDJSON(self):
    internetSource = libLF.StackOverflowRegexSource()
    internetSource.initFromNDJSON(json.dumps(soObj))

    self.assertEqual(soObj['uri'], internetSource.uri)
    self.assertEqual(soObj['uriAliases'], internetSource.uriAliases)
    self.assertEqual(soObj['patterns'], internetSource.patterns)
    self.assertEqual(soObj['type'], internetSource.type)

  def test_toNDJSON(self):
    internetSource = libLF.StackOverflowRegexSource()
    internetSource.initFromNDJSON(json.dumps(soObj))
    obj = json.loads(internetSource.toNDJSON())

    self.assertEqual(obj, soObj)

#####
# RegexUsage
#####

pythonReObj = {
  'pattern': '(a+)+$',
  'flags': ['re.DOTALL', 're.IGNORECASE'],
  'inputs': ['aaa', 'abc'],
  'project': 'https://github.com/markedjs/marked',
  'relPath': 'lib/marked.js',
  'basename': 'marked.js'
}

class RegexUsageTest(unittest.TestCase):
  def test_initFromRaw(self):
    ru = libLF.RegexUsage()
    ru.initFromRaw(
      pythonReObj['pattern'],
      pythonReObj['flags'],
      pythonReObj['inputs'],
      pythonReObj['project'],
      pythonReObj['relPath'],
      pythonReObj['basename']
    )

    self.assertEqual(pythonReObj['pattern'], ru.pattern)
    self.assertEqual(pythonReObj['flags'], ru.flags)
    self.assertEqual(pythonReObj['inputs'], ru.inputs)
    self.assertEqual(pythonReObj['project'], ru.project)
    self.assertEqual(pythonReObj['relPath'], ru.relPath)
    self.assertEqual(pythonReObj['basename'], ru.basename)

  def test_initFromNDJSON(self):
    ru = libLF.RegexUsage()
    ru.initFromNDJSON(libLF.toNDJSON(pythonReObj))

    self.assertEqual(pythonReObj['pattern'], ru.pattern)
    self.assertEqual(pythonReObj['flags'], ru.flags)
    self.assertEqual(pythonReObj['inputs'], ru.inputs)
    self.assertEqual(pythonReObj['project'], ru.project)
    self.assertEqual(pythonReObj['relPath'], ru.relPath)
    self.assertEqual(pythonReObj['basename'], ru.basename)

  def test_toNDJSON(self):
    ru = libLF.RegexUsage()
    ru.initFromNDJSON(libLF.toNDJSON(pythonReObj))
    obj = json.loads(ru.toNDJSON())

    self.assertEqual(obj, pythonReObj)

#####
# regex
#####

class RegexTest(unittest.TestCase):
  def test_perlStyleToPattern(self):
    tests = []
    # Things that should be transformed
    tests.append({ 'before': '/abc/', 'after': 'abc' })
    tests.append({ 'before': 's/abc/', 'after': 'abc' })
    tests.append({ 'before': '/abc/i', 'after': 'abc' })
    tests.append({ 'before': 's/abc/i', 'after': 'abc' })
    tests.append({ 'before': 's/abc/gi', 'after': 'abc' })

    for test in tests:
      self.assertEqual(libLF.perlStyleToPattern(test['before']), test['after'])

    # Things that should be preserved
    tests = []
    tests.append({ 'before': 'abc' })
    tests.append({ 'before': '/abc/def/g' })
    tests.append({ 'before': 'preg_replace("/([A-Z])/", "/<$1>/"' })

    for test in tests:
      self.assertEqual(libLF.perlStyleToPattern(test['before']), test['before'])

  def test_isRegexPattern(self):
    tests = []
    # Things we don't want to consider a regex pattern.
    # Simple strings
    tests.append({ 'string': '', 'result': False })
    tests.append({ 'string': 'a', 'result': False })
    tests.append({ 'string': 'United States of America', 'result': False })
    tests.append({ 'string': 'regex_match()', 'result': False })
    tests.append({ 'string': 'empty brackets[]', 'result': False })
    # Source code-like strings
    tests.append({ 'string': r'new RegExp(/abc/)', 'result': False })
    tests.append({ 'string': r'reti = regcomp', 'result': False })
    tests.append({ 'string': r're.sub(pattern)', 'result': False })

    # Examples taken from Chapman&Stolee ISSTA'16 Table 4
    tests.append({ 'string': r'z+', 'result': True })
    tests.append({ 'string': r'(caught)', 'result': True })
    tests.append({ 'string': r'.*', 'result': True })
    tests.append({ 'string': r'[aeiou]', 'result': True })
    tests.append({ 'string': r'.', 'result': True })
    tests.append({ 'string': r'[a-z]', 'result': True })
    tests.append({ 'string': r'^', 'result': True })
    tests.append({ 'string': r'$', 'result': True })
    tests.append({ 'string': r'[^qwxf]', 'result': True })
    tests.append({ 'string': r'\s', 'result': True })
    tests.append({ 'string': r'a|b', 'result': True })
    tests.append({ 'string': r'\d', 'result': True })
    tests.append({ 'string': r'\w', 'result': True })
    tests.append({ 'string': r'z?', 'result': True })
    tests.append({ 'string': r'z+?', 'result': True })
    tests.append({ 'string': r'z*?', 'result': True })
    tests.append({ 'string': r'a(?:b)c', 'result': True })
    tests.append({ 'string': r'(?P<name>x)', 'result': True })
    tests.append({ 'string': r'z{8}', 'result': True })
    tests.append({ 'string': r'\S', 'result': True })
    tests.append({ 'string': r'z{3,8}', 'result': True })
    tests.append({ 'string': r'(a?!yz)', 'result': True })
    tests.append({ 'string': r'\b', 'result': True })
    tests.append({ 'string': r'\W', 'result': True })
    tests.append({ 'string': r'z{15,}', 'result': True })
    tests.append({ 'string': r'a(?=bc)', 'result': True })
    tests.append({ 'string': r'(?i)CasE', 'result': True })
    tests.append({ 'string': r'(?<!x)yz', 'result': True })
    tests.append({ 'string': r'(?<=a)bc', 'result': True })
    tests.append({ 'string': r'\Z', 'result': True })
    tests.append({ 'string': r'\1', 'result': True })
    tests.append({ 'string': r'\D', 'result': True })
    tests.append({ 'string': r'\(?P=name)', 'result': True })
    tests.append({ 'string': r'\v', 'result': True })
    tests.append({ 'string': r'\B', 'result': True })

    # Escaping special characters is a good signal
    tests.append({ 'string': r'\(ab', 'result': True })
    tests.append({ 'string': r'ab\)', 'result': True })
    tests.append({ 'string': r'\[a', 'result': True })
    tests.append({ 'string': r'a\]b', 'result': True })
    tests.append({ 'string': r'\\', 'result': True })

    for test in tests:
      #libLF.log('isRegexPattern: test {}'.format(test))
      self.assertEqual(libLF.isRegexPattern(test['string']), test['result'])

  def test_scorePatternWritingDifficulty(self):
    patterns = [
    r'a',
    r'aa',
    r'a+b',
    r'(a+)+$',
    r'a{500}'
    ]

    for p in patterns:
      self.assertEqual(libLF.scorePatternWritingDifficulty(p), len(p))

  def test_scorePatternReadingDifficulty(self):
    patterns = [
    r'a',
    r'aa',
    r'a+b',
    r'(a+)+$',
    r'a{500}'
    ]

    for p in patterns:
      self.assertEqual(libLF.scorePatternReadingDifficulty(p), len(p))

#####
# LFFlag
#####

class LFFlagTest(unittest.TestCase):
  def test_PerlFlags(self):
    """Test a few of the flags."""
    self.assertIsInstance(
      libLF.LFFlags.langFlagToLFFlag('perl', 'm'),
      libLF.LFFlags.MultiLineAnchors
    )
    self.assertIsInstance(
      libLF.LFFlags.langFlagToLFFlag('perl', 's'),
      libLF.LFFlags.DotAll
    )
    self.assertIsInstance(
      libLF.LFFlags.langFlagToLFFlag('perl', 'i'),
      libLF.LFFlags.CaseInsensitive
    )
    self.assertIsInstance(
      libLF.LFFlags.langFlagToLFFlag('perl', 'g'),
      libLF.LFFlags.GlobalSearch
    )

  def test_PythonFlags(self):
    """Test a few of the flags."""
    self.assertIsInstance(
      libLF.LFFlags.langFlagToLFFlag('python', 'M'),
      libLF.LFFlags.MultiLineAnchors
    )
    self.assertIsInstance(
      libLF.LFFlags.langFlagToLFFlag('python', 'MULTILINE'),
      libLF.LFFlags.MultiLineAnchors
    )
    self.assertIsInstance(
      libLF.LFFlags.langFlagToLFFlag('python', 'U'),
      libLF.LFFlags.CharsetUnicode
    )
    self.assertIsInstance(
      libLF.LFFlags.langFlagToLFFlag('python', 'UNICODE'),
      libLF.LFFlags.CharsetUnicode
    )

  def test_JavaScriptFlags(self):
    """Test all the flags"""
    self.assertIsInstance(
      libLF.LFFlags.langFlagToLFFlag('javascript', 'g'),
      libLF.LFFlags.GlobalSearch
    )
    self.assertIsInstance(
      libLF.LFFlags.langFlagToLFFlag('javascript', 'i'),
      libLF.LFFlags.CaseInsensitive
    )
    self.assertIsInstance(
      libLF.LFFlags.langFlagToLFFlag('javascript', 'm'),
      libLF.LFFlags.MultiLineAnchors
    )
    self.assertIsInstance(
      libLF.LFFlags.langFlagToLFFlag('javascript', 'y'),
      libLF.LFFlags.StickySearch
    )
    self.assertIsInstance(
      libLF.LFFlags.langFlagToLFFlag('javascript', 'u'),
      libLF.LFFlags.CharsetUnicode
    )

  def test_PHPFlags(self):
    """Test a few of the flags."""
    self.assertIsInstance(
      libLF.LFFlags.langFlagToLFFlag('php', 'm'),
      libLF.LFFlags.MultiLineAnchors
    )
    self.assertIsInstance(
      libLF.LFFlags.langFlagToLFFlag('php', 'x'),
      libLF.LFFlags.Comments
    )
    self.assertIsInstance(
      libLF.LFFlags.langFlagToLFFlag('php', 'A'),
      libLF.LFFlags.StartingAnchor
    )
    self.assertIsInstance(
      libLF.LFFlags.langFlagToLFFlag('php', 'D'),
      libLF.LFFlags.DollarIsTrueEnd
    )

#####
# GitHubProject
#####

class GitHubProjectTest(unittest.TestCase):
  owner = 'foo'
  name = 'bar'
  registry = 'crates.io'
  modules = ['a', 'b']
  nStars = 1
  tarballPath = '/tmp/foo.tgz'

  def test_initFromRaw(self):
    ghp = libLF.GitHubProject()
    ghp.initFromRaw(self.owner, self.name, self.registry, self.modules, self.nStars, self.tarballPath)
    self.assertEqual(self.owner, ghp.owner)
    self.assertEqual(self.name, ghp.name)
    self.assertEqual(self.registry, ghp.registry)
    self.assertEqual(self.modules, ghp.modules)
    self.assertEqual(self.nStars, ghp.nStars)
    self.assertEqual(self.tarballPath, ghp.tarballPath)

  def test_initFromNDJSON(self):
    ghp = libLF.GitHubProject()
    ghp.initFromRaw(self.owner, self.name, self.registry, self.modules, self.nStars, self.tarballPath)
    ndjson = ghp.toNDJSON()
    ghp2 = libLF.GitHubProject().initFromJSON(ndjson)
    ndjson2 = ghp2.toNDJSON()
    self.assertEqual(ndjson, ndjson2)

  def test_toNDJSON(self):
    ghp = libLF.GitHubProject()
    ghp.initFromRaw(self.owner, self.name, self.registry, self.modules, self.nStars, self.tarballPath)
    ndjson = ghp.toNDJSON()
    self.assertTrue(re.search(r'owner', ndjson))
    self.assertTrue(re.search(self.registry, ndjson))

  def test_getNModules(self):
    ghp = libLF.GitHubProject()
    ghp.initFromRaw(self.owner, self.name, self.registry, self.modules, self.nStars, self.tarballPath)
    self.assertEqual(len(ghp.modules), len(self.modules))

#####
# Parallel
#####

class Task(libLF.parallel.ParallelTask):
  def __init__(self, x):
    self.x = x

  def run(self):
    return self.x

class ExceptTask(libLF.parallel.ParallelTask):
  def __init__(self, x):
    self.x = x

  def run(self):
    raise(SyntaxError(self.x))

class ParallelTest(unittest.TestCase):
  # Expected results
  exp = [i for i in range(1, 30)]
  expExcept = [SyntaxError(i) for i in exp]

  expBig = [i for i in range(1, 25000)]
  
  # Tasks
  tasks = [Task(i) for i in exp]
  exceptTasks = [ExceptTask(i) for i in exp]

  tasksBig = [Task(i) for i in expBig]

  def test_parallelMap_basic(self):    
    res = libLF.parallel.map(self.tasks, libLF.parallel.CPUCount.CPU_BOUND, libLF.parallel.RateLimitEnums.NO_RATE_LIMIT, libLF.parallel.RateLimitEnums.NO_RATE_LIMIT, False)
    self.assertEqual(self.exp, res)

  def test_parallelMap_basicExcept(self):
    res = libLF.parallel.map(self.exceptTasks, libLF.parallel.CPUCount.CPU_BOUND, libLF.parallel.RateLimitEnums.NO_RATE_LIMIT, libLF.parallel.RateLimitEnums.NO_RATE_LIMIT, False)
    self.assertEqual(list(map(str, self.expExcept)), list(map(str, res)))
  
  def test_parallelMap_jitter(self):
    res1 = libLF.parallel.map(self.tasks, libLF.parallel.CPUCount.CPU_BOUND, libLF.parallel.RateLimitEnums.NO_RATE_LIMIT, libLF.parallel.RateLimitEnums.NO_RATE_LIMIT, False)
    res2 = libLF.parallel.map(self.tasks, libLF.parallel.CPUCount.IO_BOUND, libLF.parallel.RateLimitEnums.NO_RATE_LIMIT, libLF.parallel.RateLimitEnums.NO_RATE_LIMIT, True)
    self.assertEqual(self.exp, res1)
    self.assertEqual(res1, res2)

  def test_parallelMap_rateLimitSeconds(self):
    # All can run in one window, or will take two windows.
    for nPerSec in [len(self.tasks), 1 + int(len(self.tasks)/2)]:
      now = time.time()
      res = libLF.parallel.map(self.tasks, libLF.parallel.CPUCount.NETWORK_BOUND, nPerSec, libLF.parallel.RateLimitEnums.PER_SECOND, False)
      elapsedSec = time.time() - now

      # Worked correctly?
      self.assertEqual(self.exp, res)

      # Took the right amount of time?
      minSecElapsed = int(len(self.tasks)/nPerSec) - 1
      self.assertGreaterEqual(elapsedSec, minSecElapsed)

  def test_parallelMap_rateLimitMinutes(self):
    nPerMinute = len(self.tasks)

    now = time.time()
    res = libLF.parallel.map(self.tasks, libLF.parallel.CPUCount.NETWORK_BOUND, nPerMinute, libLF.parallel.RateLimitEnums.PER_MINUTE, False)
    elapsedSec = time.time() - now

    # Worked correctly?
    self.assertEqual(self.exp, res)

    # Took the right amount of time?
    minMinElapsed = int(len(self.tasks)/nPerMinute) - 1
    self.assertGreaterEqual(elapsedSec/60, minMinElapsed)

  def test_parallelMap_rateLimitHours(self):
    nPerHour = len(self.tasks)

    now = time.time()
    res = libLF.parallel.map(self.tasks, libLF.parallel.CPUCount.NETWORK_BOUND, nPerHour, libLF.parallel.RateLimitEnums.PER_HOUR, False)
    elapsedSec = time.time() - now

    # Worked correctly?
    self.assertEqual(self.exp, res)

    # Took the right amount of time?
    minHourElapsed = int(len(self.tasks)/nPerHour) - 1
    self.assertGreaterEqual(elapsedSec/3600, minHourElapsed)

  def test_parallelMap_rateLimitHours_big(self):
    nPerSec = int(len(self.tasksBig) / 5)

    now = time.time()
    res = libLF.parallel.map(self.tasksBig, libLF.parallel.CPUCount.NETWORK_BOUND, nPerSec, libLF.parallel.RateLimitEnums.PER_SECOND, False)
    elapsedSec = time.time() - now

    # Worked correctly?
    self.assertEqual(self.expBig, res)

    # Took the right amount of time?
    minSecElapsed = int(len(self.tasks)/nPerSec) - 1
    self.assertGreaterEqual(elapsedSec, minSecElapsed)

###########################################################

if __name__ == '__main__':
  unittest.main()
