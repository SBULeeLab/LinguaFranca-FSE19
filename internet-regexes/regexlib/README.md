# Summary

Get the regexes from www.regexlib.com in an easy-to-work-with format.

# Usage

Run `./get-regexlib-regexes.sh`
- Raw data is written to `raw-data/`.
- Formatted data is written to `data/`.

# Components

## `get-regexlib-regexes.sh`

Driver to get the regexes from www.regexlib.com.
Runs the rest of the commands in this section.

## fetch-regexlib-html.sh

Gets X pages from RegExLib.com and puts them in `raw-data/`

## parse-regexlib-html.py

Extracts regexes from the HTML files in `raw-data/`.
Writes RegExLibRegexSource objects as ndjson to `data/`, as defined by libLF.
