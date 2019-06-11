# Summary

Drivers to test a regex's behavior in each of the languages in our study.

Each driver follows the same CLI: `TESTER query.json`.

`query.json`: keys pattern and inputs
- `pattern`: string: The regex pattern you want to test
- `inputs`: string[]: The inputs you want to test against

The regex match follows partial-match semantics in each language.

For each input, a result is emitted of the form: "Same as the input, with an extra field called 'results'".
The `results` field is an array of `result` objects, one for each input. Each `result` object follows the schema:
- `input`: string: the input string
- `matched`: bool: true if the regex matched the string, else false
- `matchContents`: object with keys `matchedString` (substring of input that matched), `captureGroups`: array of strings of capture groups

## Compiling the regex CLIs

You can run the `compile-testers.pl` script to build all of the regex CLIs.
When it finishes, they should all work (or you are missing dependencies).
