# Summary

Tools to find regular expressions in different languages.
Subdirectories hold specific extractor scripts.

Each language-specific extractor should emit NDJSON results of libLF.SimpleFileWithRegexes.

# Files

1. regex-extractor.py

Extract regexes from a GitHubProject object that has an associated tarball.
Extracts only regexes from source files in the target language of the corresponding Registry.
This is the CLI leveraged by ghp-extract-regexes.py

2. analyze-regex-duplication.py

Identify the unique regexes extracted by `regex-extractor.py`.
Measure their degree of duplication both intra-registry and inter-registry.
Also identify regexes that occur in both GitHub and in one of our InternetSources.

Output:

    - A list of (unique) libLF.Regex objects
    - Visualizations of regex duplication

Example:

```language=bash
$ECOSYSTEM_REGEXP_PROJECT_ROOT/ecosystems/per-module/extract-regexps/static/analyze-regex-duplication.py \
  --github-project-list data/regextract/*-regexes.json \
  --internet-source-lists data/regextract/internetSources-regExLib.json \
  --cur-prefix /home/davisjam/data/github-clone --new-prefix $ECOSYSTEM_REGEXP_PROJECT_ROOT/data/regextract \
  --unique-regex-file /tmp/uniq-regexes.json \
  --vis-dir /tmp/vis
```
