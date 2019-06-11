# Summary

| Item | Meaning |
|------|---------|
| static-extractors/ | Subdir for extractors, see README within |
| uniq-regexes-8.json | The 537,806 unique regexes in our corpus, spanning 8 programming languages |

`uniq-regexes-8.json` is an NDJSON-formatted minimal set of libLF.Regex objects. It contains a bunch of unpopulated fields. The only populated fields are:
1. `pattern`
2. `useCount_registry_to_nModules` -- indicates the language(s) in which this pattern was found

## Compiling the extractors

You can run the `compile-extractors.pl` script to build all of the extractors.
When it finishes, they should all work (or you are missing dependencies).

Dependencies: The following must be in your PATH
- npm
- cpan
- composer
- rustc (a version that supports -Z)
