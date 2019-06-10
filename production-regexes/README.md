# Summary

| Item | Meaning |
|------|---------|
| static-extractors/ | Subdir for extractors, see README within |
| uniq-regexes-8.json | The 537,806 unique regexes in our corpus, spanning 8 programming languages |

`uniq-regexes-8.json` is an NDJSON-formatted minimal set of libLF.Regex objects. It contains a bunch of unpopulated fields. The only populated fields are:
1. `pattern`
2. `useCount_registry_to_nModules` -- indicates the language(s) in which this pattern was found
