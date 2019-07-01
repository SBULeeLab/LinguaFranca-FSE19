# Summary

Here there be analyses for experiments!

| Directory                        | Description                                                             |
|----------------------------------|-------------------------------------------------------------------------|
| test-regex-behavior-in-language/ | Drivers for testing regex behavior in each language                     |
| syntax/                          | Tools for syntax experiments                                            |
| semantic/                        | Tools for semantic experiments -- input generation and analysis scripts |
| performance/                     | Tools for performance experiments                                       |

## Structure of the analyses

The analyses in this paper are embarrassingly parallel.
Each analysis can be performed on a single regex (or a group of regexes) independent of analyses on the others.

As a result, we performed our experiments on a compute cluster.
We therefore divided each analysis into two parts:
1. `test-for-X.py`: Test for the property in question and produce a data file (distribute the work across the cluster)
2. `analyze-X.py`: Analyze a combined set of results (after merging the compute job)

## One stop shop

The `run-analyses.pl` script runs these analyses in the proper order.
See the main [README.md](../README.md) for a detailed explanation.
