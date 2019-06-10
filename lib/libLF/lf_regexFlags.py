class LFFlag():
  """Represents a regex flag."""
  def __init__(self, name, desc):
    self.name = name
    self.desc = desc

class MultiLineAnchors(LFFlag):
  def __init__(self):
    super().__init__('MultiLineAnchors', 'Apply anchors at line delimiters instead of string begin and end')

class StartingAnchor(LFFlag):
  def __init__(self):
    super().__init__('StartingAnchor', 'Match must begin at beginning, like ^')

class DollarIsTrueEnd(LFFlag):
  def __init__(self):
    super().__init__('DollarIsTrueEnd', 'Make $ actually match at the end instead of a final newline')

class DotAll(LFFlag):
  def __init__(self):
    super().__init__('DotAll', 'Make . match any character, including newlines')

class CaseInsensitive(LFFlag):
  def __init__(self):
    super().__init__('CaseInsensitive', 'Make letters match all cases')

class Comments(LFFlag):
  def __init__(self):
    super().__init__('Comments', 'Enable pretty regexes: ignore non-escaped whitespace and treat # as a comment.')

class Eval(LFFlag):
  def __init__(self):
    super().__init__('Eval', 'Eval-like behavior during search-replace')

class CharsetRestrictedUnicode(LFFlag):
  def __init__(self):
    super().__init__('CharsetRestrictedUnicode', 'Use the Unicode charset. Also restrict the behavior of \\d, \\s, \\w, and Posix char classes to consider only within the ASCII range. \\D, \\S, and \\W match non-ASCII characters')

class CharsetUnicode(LFFlag):
  def __init__(self):
    super().__init__('CharsetUnicode', 'Use the Unicode charset')

class CharsetUTF8(LFFlag):
  def __init__(self):
    super().__init__('CharsetUTF8', 'Use the UTF8 charset')

class CharsetLocale(LFFlag):
  def __init__(self):
    super().__init__('CharsetLocale', 'Use the charset of the current Locale')

class Debug(LFFlag):
  def __init__(self):
    super().__init__('Debug', 'Print debug info')

class GlobalSearch(LFFlag):
  def __init__(self):
    super().__init__('GlobalSearch', 'Global search: resume where previous search left off')

class StickySearch(LFFlag):
  def __init__(self):
    super().__init__('StickySearch', 'Sticky search: resume, left-anchored, previous search left off')

class ASCIIMatchForBuiltInCharClasses(LFFlag):
  def __init__(self):
    # TODO
    super().__init__('ASCIIMatchForBuiltInCharClasses', 'TODO XXX')

class Optimize(LFFlag):
  def __init__(self):
    super().__init__('Optimize', 'Optimize the internal regex representation')

class Ungreedy(LFFlag):
  def __init__(self):
    super().__init__('Ungreedy', 'Reverse quantifier greediness')

class DebugInfo(LFFlag):
  def __init__(self):
    super().__init__('DebugInfo', 'Generate debugging info')

# 2-level dict: [lang][flagInLang] -> equivalent libLF class
_langFlagToLFFlag = {
  'perl': {
    # https://perldoc.perl.org/perlre.html#Modifiers
    ## General modifiers
    # m: treat the string being matched as against multiple lines -- affects ^ and $
    'm': MultiLineAnchors,
    # s: treat the string being matched as a single line -- affects .
    's': DotAll,
    # i: case-insensitive pattern matching
    'i': CaseInsensitive,
    # x, xx: permit whitespace and comments
    #  - ignore whitespace that is neither backslashed nor within a [character class]
    #  - treat # as a metacharacter for comments
    #  - xx also ignores non-backslashed spaces and tabs within [character classes]
    'x': Comments,
    # p: preserve string matched
    # a, u, l, d: affect the character set rules used for the regex
    #   - a: set the character set to Unicode, adding several restrictions for ASCII-safe matching
    #      Allows code for mostly ASCII data to ignore Unicode."
    'a': CharsetRestrictedUnicode,
    #   (u, l, and d are generally for internal use.)
    #   - u: set the character set to Unicode
    #       Equivalent to 'use feature 'unicode_strings'
    #       https://perldoc.perl.org/perlunicode.html:
    #         "Note that unicode_strings is automatically chosen if you use 5.012 or higher."
    'u': CharsetUnicode,
    #   - l: set the character set to that of the Locale in effect at execution-time
    'l': CharsetLocale,
    #        --> It is recommended to obtain locale and unicode behavior using
    #            'use local / use feature "unicode_strings"' instead.
    #            Should we try to identify pragmas?
    #            PPI can see them:
    #                 ...
    #               PPI::Statement::Include
    #                 PPI::Token::Word    'use'
    #                 PPI::Token::Whitespace    ' '  
    #                 PPI::Token::Word    'locale'
    #                 PPI::Token::Structure   ';'  
    #                 ...
    #               PPI::Statement::Include
    #                 PPI::Token::Word    'use'
    #                 PPI::Token::Whitespace    ' '  
    #                 PPI::Token::Word    'feature'
    #                 PPI::Token::Whitespace    ' '  
    #                 PPI::Token::Quote::Single   ''unicode_strings''
    #                 PPI::Token::Structure   ';'

    #   - d: obsolete
    # n: prevent grouping metachars from capturing. Stop the population of $1, $2, etc.
    ## Other modifiers
    ### For m//
    # c: keep current position during repeated matching
    # g: globally match the pattern repeatedly in the string
    'g': GlobalSearch,
    ### For s///
    # e: evaluate RHS as an expression
    # ee: evaluate RHS as a string then eval the result
    'e': Eval,
    # o: pretend to optimize your code, but actually introduce bugs
    # r:  non-destructive substitution
  },

  'python': {
    # https://docs.python.org/2/library/re.html
    # DEBUG: Display debug information about compiled expression
    # I, IGNORECASE: Case-insensitive matching. Not affected by current locale
    #   ASCII-only unless you add UNICODE
    'I': CaseInsensitive,
    'IGNORECASE': CaseInsensitive,
    # DEBUG: Display debug information about compiled expression
    'DEBUG': DebugInfo,
    # L, LOCALE: Make \w, \W, \b, \B, \s, and \S depend on the current locale
    'L': CharsetLocale, # Analogous to Perl. Possibly perfectly equivalent?
    'LOCALE': CharsetLocale,
    # M, MULTILINE: Cause ^ and $ to match on newlines as well
    'M': MultiLineAnchors,
    'MULTILINE': MultiLineAnchors,
    # S, DOTALL: Cause . match any character including newline
    'S': DotAll,
    'DOTALL': DotAll,
    # U, UNICODE: Make \w, \W, \b, \B, \d, \D, \s, and \S use Unicode.
    #   Also enables non-ASCII matching for IGNORECASE.
    'U': CharsetUnicode, # Analogous to Perl. Possibly perfectly equivalent?
    'UNICODE': CharsetUnicode,
    # X, VERBOSE: Ignores whitespace within the pattern; # indicates a comment
    'X': Comments,
    'VERBOSE': Comments,

    # https://docs.python.org/3/library/re.html
    ## New in v3
    # A, ASCII: Make \w, \W, \b, \B, \d, \D, \s, and \S perform ASCII-only matching
    #   instead of full Unicode matching. Only affects Unicode patterns. cf. (?a)
    #   This intersects a bit with Perl's /a flag.
    'A': ASCIIMatchForBuiltInCharClasses,
    'ASCII': ASCIIMatchForBuiltInCharClasses
    ## Similar-enough in v3
    # DEBUG: Same as v2
    # I, IGNORECASE: Changed in v3
    #  Now Unicode are also case-insensitive by default and ASCII *disables* this behavior.
    # L, LOCALE: Mostly the same as v2 but a few differences
    # M, MULTILINE: Same as v2
    # S, DOTALL: Same as v2
    # X, VERBOSE: Same as v2
  },

  'javascript': {
    # https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_Expressions#Advanced_searching_with_flags_2
    'g': GlobalSearch, # https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/RegExp/global
    'i': CaseInsensitive, # https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/RegExp/ignoreCase
    'm': MultiLineAnchors, # https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/RegExp/multiline
    'u': CharsetUnicode, # https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/RegExp/unicode
     # y: sticky -- like an anchored search I think? https://stackoverflow.com/questions/30291436/what-is-the-purpose-of-the-y-sticky-pattern-modifier-in-javascript-regexps
    'y': StickySearch, # https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/RegExp/sticky
  },

  'php': {
    # http://php.net/manual/en/reference.pcre.pattern.modifiers.php
    'i': CaseInsensitive,
    'm': MultiLineAnchors,
    's': DotAll,
    'x': Comments,
    # e: eval-like behavior similar to Perl's /e, /ee : now deprecated
    'e': Eval,
    # A: Introduces a starting anchor. Equivalent to /^.../
    'A': StartingAnchor,
    # D: Cause $ to match only the end of the string
    #    Without D, $ will match *before* a newline if it is the final character
    'D': DollarIsTrueEnd,
    # S: "Study": Optimize the regex representation internally for faster matching
    'S': Optimize,
    # U: "Ungreedy": Invert greediness: + is non-greedy, +? is greedy
    'U': Ungreedy,
    # X: "EXTRA": Enable minor deviations from Perl.
    # J: "Internal": Allow duplicate names for sub-patterns.
    # u: "UTF8": Treat pattern and inputs as UTF-8.
    'u': CharsetUTF8,
  }
}

def langFlagToLFFlag(lang, flag):
  """Return the LF Flag for $flag in $lang."""
  lfFlagClass = _langFlagToLFFlag[lang][flag]
  return lfFlagClass()
