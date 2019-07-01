# Summary

Tools to:
1. Get the regexes from Internet sources.
2. Count these regexes.
3. Identify overlap between the regexes from Internet sources and regexes used in practice.

Note: In the paper we report a breakdown by language of origin and by module.
This requires mapping each regex back to its original module.
While we have this data, for security reasons we are not disclosing the mapping from regex back to its original module.

However, the provided scripts are sufficient to demonstrate our findings writ broad: developers appear to re-use regexes from Internet sources.

# Sources

| source | directory | description |
|--------|-----------|-------------|
| RegExLib | `regexlib/` | Get the regexes from www.regexlib.com, which is a website dedicated to regexes for various DSLs |
| StackOverflow | `stackoverflow/` | Get the regexes from regex posts on www.stackoverflow.com |

# Tools

1. Count the total and unique regexes for "fun facts" reporting.

```
./count-regexes.py --regex-file stackoverflow/data/internetSources-stackoverflow.json
./count-regexes.py --regex-file regexlib/data/internetSources-regExLib.json
```

2. Check if real regexes match those from an internet source.

```
# Simple check for intersections between regexlib and the production regexes
./check-real-regexes-from-internet.py --internet-patterns regexlib/data/internetSources-regExLib.json --real-patterns ../production-regexes/uniq-regexes-8.json 2>/tmp/check-match-regexlib.log

# Simple check for intersections between stackoverflow and the production regexes
./check-real-regexes-from-internet.py --internet-patterns stackoverflow/data/internetSources-stackoverflow.json --real-patterns ../production-regexes/uniq-regexes-8.json 2>/tmp/check-match-stackoverflow.log

# Check for intersections with varying writing difficulty thresholds
for thresh in 0 5 10 20 30 40; do ./check-real-regexes-from-internet.py --internet-patterns regexlib/data/internetSources-regExLib.json --real-patterns ../production-regexes/uniq-regexes-8.json --writing-difficulty-threshold $thresh 2>/tmp/check-match-regexlib-thresh$thresh.log; done
```

This gives a sense of what the data underlying Figure 4 (RQ5) looks like.

# File format

An Internet source should yield a file of NDJSON-formatted libLF.InternetRegexSource objects.
