import re
import json

def usesPOSIX(reg):
  return '\\p{' in reg or re.search(r"\[:\w+:\]", reg)

def usesTradl(reg):
  st = [ '\\d', '\\D', '\\w', '\\W', '\\s', '\\S' ]
  for s in st:
    if s in reg:
      return True
  return False

#def usesCustom(reg):
#  return '[' in reg and ']' in reg

def usesBuiltInCC(reg):
  return usesPOSIX(reg) or usesTradl(reg)

def containsLongWhitespaceSpan(reg):
  return "        " in reg

##############

objs = []
with open("uniq-regexes-8.json", "r") as inStream:
  for row in inStream:
    objs.append(json.loads(row))

langsWithPOSIX = ['java', 'perl', 'php', 'ruby', 'go']
langsWithWhitespace = ['perl', 'python', 'go']
lang2eco = {
  "java": "maven",
  "perl": "cpan",
  "php": "packagist",
  "ruby": "rubygems",
  "go": "godoc",
  "python": "pypi",
}

def inLang(lang, obj):
  return lang2eco[lang] in obj['useCount_registry_to_nModules'] and obj['useCount_registry_to_nModules'][lang2eco[lang]] > 0

def analyzePOSIXUsingRegexes(lang, allObjs):
  objs = [
    o
    for o in allObjs
    if inLang(lang, o)
  ]

  #print(f"Found {len(objs)} {lang} regexes")

  regs = [ str(o['pattern']) for o in objs ]
  ccs = [ reg for reg in regs if usesBuiltInCC(reg) ]
  usedPOSIX = [ reg for reg in ccs if usesPOSIX(reg) ]
  #print(f"usedPOSIX: {usedPOSIX[0:5]}")

  usedBuiltin = [ reg for reg in ccs if usesTradl(reg) ]
  #print(f"usedBuiltin: {usedBuiltin[0:5]}")

  usedBoth = [ reg for reg in ccs if usesPOSIX(reg) and usesTradl(reg) ]
  #print(f"usedBoth: {usedBoth[0:5]}")

  print(f"{lang} report: {len(ccs)} regexes used CCC. {len(usedPOSIX)} used POSIX, while {len(usedBuiltin)} used built-in CCs. {len(usedBoth)} mixed styles")
  return "%.2d" % (100*len(usedPOSIX)/len(ccs))

def countLongWhitespaceIncidence(lang, allObjs):
  objs = [
    o
    for o in allObjs
    if inLang(lang, o)
  ]

  bigWhitespace = [
    o
    for o in objs
    if containsLongWhitespaceSpan(o['pattern'])
  ]
  perc = 100 * len(bigWhitespace) / len(objs)
  print(f"{lang} report: {len(bigWhitespace)} / {len(objs)} regexes had a big span: " + "%.2d%%"%(perc))

########

lang2percUsedPOSIX = {}
for lang in langsWithPOSIX:
  lang2percUsedPOSIX[lang] = analyzePOSIXUsingRegexes(lang, objs)

for lang, perc in lang2percUsedPOSIX.items():
  print(f"{lang}: {perc}% of CC-using regexes used POSIX")

for lang in langsWithWhitespace:
  countLongWhitespaceIncidence(lang, objs)