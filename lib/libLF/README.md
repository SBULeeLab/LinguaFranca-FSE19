# Summary

Library for the Lingua Franca project.

# Features

This is a relatively empirical project and we collect tons of data.
To analyze this data, it is convenient to have classes representing the objects under study.
That way we can write scripts independent of the underlying data representation.

It is also convenient to have a consistent, and human-readable, on-disk data format.
To this end:
- The on-disk representation is human-readable --- newline-delimited JSON ([ndjson](http://ndjson.org/)).
- The classes in this library generally have `initFromNDJSON` and `toNDJSON` methods.

# Structure

1. Each component is placed in its own `lf_*.py` file.
2. These components are collected in `__init__.py` so they can be imported as a single package.

# Use

1. Add this directory to your `sys.path`.
2. Import like this: `import libLF`.

Example:

```
import os
import sys
sys.path.append(os.path.join(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT'], 'lib'))
import libLF
```

# Tests

Each class should have a corresponding test class in `test-libLF.py`.

Run the tests like this:

```bash
./test-libLF.py
```
