"""Lingua Franca: NDJSON
"""

import json

#####
# ND-JSON
#####

def isNDJSON(ndjson):
  return type(ndjson) is str \
         and len(ndjson) >= 2 \
         and ndjson[0] is '{' \
         and ndjson[-1] is '}' \
         and ndjson.find('\n') is -1

def toNDJSON(obj):
  """Convert this object to an NDJSON-formatted string representation."""
  ndjson = json.dumps(obj, sort_keys=True)
  assert(isNDJSON(ndjson))
  return ndjson

def fromNDJSON(ndjson):
  """Return a simple Python object from an ndjson-encoded string."""
  ndjson = ndjson.strip()
  assert(isNDJSON(ndjson))
  return json.loads(ndjson)
