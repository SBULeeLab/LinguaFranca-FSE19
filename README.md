# Lingua Franca

Welcome to the ESEC/FSE'19 artifact for the ESEC/FSE paper *"Why Aren’t Regular Expressions a Lingua Franca? An Empirical Study on the Re-use and Portability of Regular Expressions"*, by J.C. Davis, L.G. Michael IV, C.A Coghlan, F. Servant, and D. Lee, all of Virginia Tech.

This paper describes our study into regex portability practices and problems. In this empirical work, we:
- surveyed 158 professional software developers about their regex beliefs and re-use practices
- extracted regular expression-like entities from Stack Overflow and RegExLib to understand re-use practices
- extracted regular expressions from about 200,000 software projects written in 8 programming languages
- analyzed these production regular expressions for portability problems: syntactic, semantic, and performance

## Artifact

Our artifact includes the following:

| Item | Description | Corresponding content in the paper | Scientific interest | Relation to prior work |
|------|-------------|---------------------|------------------------------------|------------------------|
| Internet Sources collectors | Tools to extract regexes from Internet Sources | Section 6.2.1 | | |
| Internet Sources corpus | Entities that look like regexes across Stack Overflow and RegExLib | Section 6.2 | First snapshot of regexes in Internet forums | No prior work has examined the regexes from these Internet sources. Our analysis was in the spirit of work on more general code re-use from Stack Overflow to GitHub. |
| Regex extractors | Tools to statically extract regexes from software written in 8 programming languages | Section 5 | | Adds 6 programming languages to [the tools from our FSE'18 paper](https://github.com/VTLeeLab/EcosystemREDOS-FSE18) |
| Regex corpus | A polyglot regex corpus of 537,806 unique regexes extracted from 193,524 projects written in 8 programming languages | *Collection*: Section 5, esp. Table 1. *Experiments*: Section 7 | This is the largest and most diverse regex corpus ever collected. It should be useful for future regex analysis purposes, e.g. in testing a visualization or input generation tool. | Our FSE'18 paper included a corpus of about 400,000 regexes extracted from about 670,000 npm and pypi modules (See Table 1 in [that paper](https://dl.acm.org/citation.cfm?id=3236027), and [that artifact](https://github.com/VTLeeLab/EcosystemREDOS-FSE18)). This new corpus covers 6 more programming languages. |
| Regex analyses: Semantic | Drivers for 5 input generators | Section 7.1 | Collects, improves, and unifies existing input generators | |
| Regex analyses: Performance | Drivers for 3 super-linear regex detectors | Section 7.2 | Extends existing super-linear regex detectors to partial-match semantics | Builds on the tooling from our FSE'18 paper |


In addition to this directory's `README.md`, each sub-tree comes with one or more READMEs describing the software and tests.

## Installation

### By hand

To install, execute the script `./configure` on an Ubuntu 16.04 machine with root privileges.
This will obtain and install the various dependencies (OS packages, REDOS detectors, npm modules, and pypi modules).
It will also initialize submodules.

The final line of this script is `echo "Configuration complete. I hope everything works!"`.
If you see this printed to the console, great!
Otherwise...alas.

### Container

To facilitate replication, we have published a [containerized version](https://hub.docker.com/r/jamiedavis/daviscoghlanservantlee-fse18-regexartifact/) of this project on hub.docker.com.
The container is based on an Ubuntu 16.04 image so it is fairly large.
  
For example, you might run:

```
docker pull jamiedavis/daviscoghlanservantlee-fse18-regexartifact
docker run -ti jamiedavis/daviscoghlanservantlee-fse18-regexartifact
> vim .env
# Set ECOSYSTEM_REGEXP_PROJECT_ROOT=/davis-fse18-artifact/EcosystemREDOS-FSE18
> . .env
> ./full-analysis/analyze-regexp.pl ./full-analysis/test/vuln-email.json
```

## Use

### Environment variables

Export the following environment variables to ensure the tools know how to find each other.
- `ECOSYSTEM_REGEXP_PROJECT_ROOT`
- `VULN_REGEX_DETECTOR_ROOT` (submodule, set it to `ECOSYSTEM_REGEXP_PROJECT_ROOT/vuln-regex-detector`)

See `.env` for examples.

### Analysis phases

Each phase of the analysis is performed by a separate set of tools.
See the description of the directory structure below for a mapping from research questions to directories.

### Running all of the phases at once

The `full-analysis/analyze-regexp.pl` program runs all of the analysis phases on a list of regexes and prints a summary for each regex.
Use this to confirm that the code is installed and working. Whether you think it does something interesting or useful is up to you.

## Directory structure

| File or Directory/    | Description |
|:---------------------:|:------------|
| README.md             | You're in it                                              |
| PAPER.pdf             | Non-anonymized manuscript we submitted for review. Not camera-ready.                                              |
| LICENSE               | Terms of software release                                 |
| STATUS                | Claims of artifact quality                                |
| INSTALL               | "Install instructions"                                    |
| internet-regexes/                | Corpus for Internet Sources, plus extraction tools                                    |
| production-regexes/              | Corpus for Production Regexes, plus extraction tools |
| lib/                             | Python libraries -- utility routines, serializers and parsers for types expressed in JSON
| test-regex-behavior-in-language/ | Drivers for testing regex behavior in each language
| semantic/                        | Tools for semantic experiments
| performance/                     | Tools for performance experiments
| containerized/                   | Dockerfile for building container | - |
| full-analysis/                   | Run each analysis step on a regex.                        | - |

Each directory contains its own README for additional details.

## Style and file formats

### Style

Most of the scripts in this repository are written in Perl.
They tend to write status updates to STDERR and to emit useful output to STDOUT, though the more complex ones use a resultFile instead.

If you have dependencies on other scripts in the repo, require the invoker to define `ECOSYSTEM_REGEXP_PROJECT_ROOT`.
This environment variable should name the location of your clone of this repository.

### File formats

This project uses JSON to describe research data.
Files named `*.json` are generally JavaScript files that contain one JSON object per line.
This makes it easy to do a line-by-line analysis on the objects in the file, even if the file is large.

## Contact

Contact J.C. Davis at davisjam@vt.edu with any questions.

