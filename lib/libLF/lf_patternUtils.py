import re

#####
# Misc regex functions
#####

def perlStyleToPattern(pattern):
  """Convert 's/abc/i'-style regexes to 'abc' patterns.

     Used during extraction of regexes from InternetSource.
  """
  if pattern.count('/') is 2:
    l = pattern.index('/')
    r = pattern.rindex('/')
    if 0 <= l and l < r:
      pattern = pattern[l+1 : r]
  return pattern

def isRegexPattern(string):
  """Returns True if string looks like a regex pattern, else False.

     Tries to exclude things that look like code snippets.

     Searches for any of the common regex feature syntaxes.
     Basically, we are looking for regexes that contain anything more
     advanced than characters.

     Example: We reject /a/ but accept /a+/.

     Uses notation from Chapman&Stolee ISSTA'16 (Table 4),
     which targets Python regexes.
     The syntax is pretty universal so I think this is OK for starters.

     Used during extraction of regexes from InternetSource.
  """

  # Filter: Code snippets.
  # Each of these is a source of false omissions.
  # Regexes that are actually matching source code will be rejected.
  if "(regex)" in string or "<regex>" in string or "[regex]" in string:
    return False
  if (   re.search(r're\.\w+\(', string)
      or re.search(r'RegExp\(', string)
      or re.search(r'preg_\w+\(', string)
      or re.search(r'console\.log', string)
      or re.search(r'\w\s+=\s+\w', string)
  ):
    return False

  # Regex syntax.
  if (False
  # Chapman & Stolee
  or re.search(r'\+', string) # ADD
  or re.search(r'\([\s\S]+\)', string) # CG
  or re.search(r'\*', string) # KLE
  or re.search(r'\[[\s\S]+\]', string) # CCC
  or re.search(r'\.', string) # ANY
  or re.search(r'\[.*\-.*\]', string) # RNG
  or re.search(r'\^', string) # STR
  or re.search(r'\$', string) # END
  or re.search(r'\[\^', string) # NCCC
  or re.search(r'\\s', string) # WSP
  or re.search(r'\|', string) # OR
  or re.search(r'\\d', string) # DEC
  or re.search(r'\\w', string) # WORD
  or re.search(r'\?', string) # QST
  or re.search(r'\+\?', string) # LZY - ADD
  or re.search(r'\*\?', string) # LZY - KLE
  or re.search(r'\(\?:', string) # NCG
  or re.search(r'\(\?P<', string) # PNG
  or re.search(r'{\d+}', string) # SNG
  or re.search(r'\\S', string) # NWSP
  or re.search(r'{\d+,\d+}', string) # DBB
  or re.search(r'\(\?!', string) # NLKA
  or re.search(r'\\b', string) # WNW
  or re.search(r'\\W', string) # NWRD
  or re.search(r'\{\d+,\}', string) # LWB
  or re.search(r'\(\?=', string) # LKA
  or re.search(r'\(\?\w+\)', string) # OPT
  or re.search(r'\(\?<!', string) # NLKB
  or re.search(r'\(\?<=', string) # LKB
  or re.search(r'\\Z', string) # ENDZ
  or re.search(r'\\\d+', string) # BKR
  or re.search(r'\\D', string) # NDEC
  or re.search(r'\(\?P=', string) # BKRN
  or re.search(r'\\v', string) # VWSP
  or re.search(r'\\B', string) # NWNW
  # Escaping special characters is also a good indicator.
  or re.search(r'\\', string)
  or re.search(r'\\(\[|\])', string)
  or re.search(r'\\(\(|\))', string)
  ):
    return True
  return False

def scorePatternWritingDifficulty(pattern):
  """Measure the human difficulty of WRITING a regex pattern.

  If score(r) < score(t), r is easier to write than t. 
  When writing regexes, our intuition is that the longer
  the regex, the harder to write.

  Thus we simply use the length of the pattern as a measure of difficulty.
  """
  return len(pattern)

def scorePatternReadingDifficulty(pattern):
  """Measure the human difficulty of READING a regex pattern.

  If score(r) < score(t), r is easier to read than t. 
  When reading regexes, our intuition is that the more convoluted
  the regex, the harder to read.

  Thus we want to use some measure of the complexity of the corresponding NFA-ish.
  Some caution here:
    While 'a{100}' has a "complex" NFA by raw size,
    I think this regex is about as easy to read as 'aaaaaa'.
      'a{100}': 100 states and 100 transitions
      'aaaaaa': 6 states and 6 transitions

    On this note, I experimented with the FAdo package but
    str2regexp did not work even in python2 for r'abc+' ??
  """
  # TODO This is too simplistic.
  return len(pattern)

def unescapeDoubleQuotes(strPattern):
  """Convert any \" to ".
  
  This is the primary difference between Rust string literals and raw string literals.
  If anyone is using the "end of line escape followed by a newline", however,
  we won't notice that.
  We have a similar problem with the Perl /x extended mode."""
  return strPattern.replace('\\"', '"')