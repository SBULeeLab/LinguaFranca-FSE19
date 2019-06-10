# Summary

Tools to:
1. Get the regexes from Internet sources.
2. Count these regexes.
3. Identify overlap between the regexes from Internet sources and regexes used in practice.

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
# Check npm against the RegExLib and StackOverflow sources
./check-real-regexes-from-internet.py --internet-patterns regexlib/data/internetSources-regExLib.json --real-patterns ../data/npm/npm-pattern2modules.json --out-file /tmp/out.json 2>/tmp/npm-REL.err
grep -c 'matches internet source' /tmp/npm-REL.err
grep -c 'does not match internet source' /tmp/npm-REL.err
tail -2 /tmp/npm-REL.err | head -1

./check-real-regexes-from-internet.py --internet-patterns stackoverflow/data/internetSources-stackoverflow.json --real-patterns ../data/npm/npm-pattern2modules.json --out-file /tmp/out.json 2>/tmp/npm-SO.err
grep -c 'matches internet source' /tmp/npm-SO.err
grep -c 'does not match internet source' /tmp/npm-SO.err
tail -2 /tmp/npm-SO.err | head -1

# Check pypi against the RegExLib and StackOverflow sources
./check-real-regexes-from-internet.py --internet-patterns regexlib/data/internetSources-regExLib.json --real-patterns ../data/pypi/pypi-pattern2modules.json --out-file /tmp/out.json 2>/tmp/pypi-REL.err
grep -c 'matches internet source' /tmp/pypi-REL.err
grep -c 'does not match internet source' /tmp/pypi-REL.err
tail -2 /tmp/pypi-REL.err | head -1

./check-real-regexes-from-internet.py --internet-patterns stackoverflow/data/internetSources-stackoverflow.json --real-patterns ../data/pypi/pypi-pattern2modules.json --out-file /tmp/out.json 2>/tmp/pypi-SO.err
grep -c 'matches internet source' /tmp/pypi-SO.err
grep -c 'does not match internet source' /tmp/pypi-SO.err
tail -2 /tmp/pypi-SO.err | head -1

# Test pypi against regexlib with varying writing difficulty thresholds
for thresh in 0 5 10 20 30 40; do ./check-real-regexes-from-internet.py --internet-patterns regexlib/data/internetSources-regExLib.json --real-patterns ../data/pypi/pypi-pattern2modules.json --out-file /tmp/out.json --writing-difficulty-threshold $thresh 2>/tmp/pypi-REL-thresh$thresh.err; done
```

# File format

An Internet source should yield a file of ndjson-formatted libLF.InternetRegexSource objects.
