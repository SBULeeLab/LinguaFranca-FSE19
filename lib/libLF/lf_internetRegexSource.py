"""Lingua Franca: Internet-derived regexes
"""

import libLF.lf_ndjson as lf_ndjson
import libLF.lf_utils as lf_utils

#####
# InternetRegexSource
#####

class InternetRegexSource:
  """Represents a source of regexes on the internet.

  Members: uri, uriAliases, patterns[]
  You should sub-class from this for particular sources, e.g. RegExLib and StackOverflow.

  Sub-classes should define their type as a string, after calling the super's init.

  Use the factory method when handling arbitrary InternetRegexSource's from files.
  """

  def factory(jsonStr):
    """Create *and initialize* an InternetRegexSource from this ndjson string."""
    # Parse and get the 'type' field.
    obj = lf_ndjson.fromNDJSON(jsonStr)
    if not 'type' in obj:
      raise ValueError('Error no type in jsonStr: {}'.format(jsonStr))

    # Re-parse based on the appropriate type.
    internetSource = None
    if obj['type'] == "RegExLibRegexSource":
      internetSource = RegExLibRegexSource()
    elif obj['type'] == "StackOverflowRegexSource":
      internetSource = StackOverflowRegexSource()
    else:
      raise ValueError('Error, unexpected type {}'.format(obj['type']))
    internetSource.initFromNDJSON(jsonStr)
    return internetSource

  def __init__(self):
    """Declare an object and then initialize using JSON or "Raw" input."""
    self.initialized = False
    self.type = None
  
  def initFromRaw(self, uri, uriAliases, patterns):
    """uri: string. A unique identifier for this pattern in its source. Example: "https://stackoverflow.com/a/8270824".
       uriAliases: array of strings. Other unique identifiers for this source. Example: ["https://stackoverflow.com/questions/8270784/how-to-split-a-string-between-letters-and-digits-or-between-digits-and-letters/8270914#8270914", "https://stackoverflow.com/questions/8270784"].
       patterns: array of strings for the one or more patterns in this source. Example: ["[0-9]+|[a-z]+|[A-Z]+"].
    """
    self.initialized = True

    self.uri = uri
    self.uriAliases = uriAliases
    self.patterns = patterns

  def initFromNDJSON(self, jsonStr):
    self.initialized = True

    obj = lf_ndjson.fromNDJSON(jsonStr)
    self.uri = obj['uri']
    self.uriAliases = obj['uriAliases']
    self.patterns = obj['patterns']
    if 'type' in obj:
      self.type = obj['type']
  
  def toNDJSON(self):
    assert(self.initialized)
    # Consistent and in ndjson format
    return lf_ndjson.toNDJSON(self._toDict())

  def _toDict(self):
    obj = { "uri": self.uri,
            "uriAliases": self.uriAliases,
            "patterns": self.patterns
    }
    return obj

class RegExLibRegexSource(InternetRegexSource):
  """RegExLib regex source"""
  def __init__(self):
    super().__init__()
    self.type = "RegExLibRegexSource"

  def _toDict(self):
    obj = super()._toDict()
    obj['type'] = self.type
    return obj

class StackOverflowRegexSource(InternetRegexSource):
  """StackOverflow regex source"""
  def __init__(self):
    super().__init__()
    self.type = "StackOverflowRegexSource"

  def _toDict(self):
    obj = super()._toDict()
    obj['type'] = self.type
    return obj