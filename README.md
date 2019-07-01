[![DOI](https://zenodo.org/badge/191027036.svg)](https://zenodo.org/badge/latestdoi/191027036)

# Lingua Franca

Welcome to the ESEC/FSE'19 artifact for the ESEC/FSE paper [*"Why Aren’t Regular Expressions a Lingua Franca? An Empirical Study on the Re-use and Portability of Regular Expressions"*](http://people.cs.vt.edu/~davisjam/downloads/publications/DavisMichaelCoghlanServantLee-LinguaFranca-ESECFSE19.pdf), by J.C. Davis, L.G. Michael IV, C.A Coghlan, F. Servant, and D. Lee, all of Virginia Tech.

This paper describes our study into regex portability practices and problems. In this empirical work, we:
- surveyed 158 professional software developers about their regex beliefs and re-use practices
- extracted regular expression-like entities from Stack Overflow and RegExLib to understand re-use practices
- extracted regular expressions from about 200,000 software projects written in 8 programming languages
- analyzed these production regular expressions for portability problems: syntactic, semantic, and performance

## Artifact

Our artifact includes the following:

| Item | Description | Corresponding content in the paper | Scientific interest | Relation to prior work |
|------|-------------|---------------------|------------------------------------|------------------------|
| Survey instrument | Survey of developers' regex practices | Section 4.1 | | Second survey of developer regex practices, cf. Chapman & Stolee ISSTA'16 |
| Internet Sources collectors | Tools to extract regexes from Internet Sources | Section 6.2.1 | | |
| Internet Sources corpus | Entities that look like regexes across Stack Overflow and RegExLib | Section 6.2 | First snapshot of regexes in Internet forums | No prior work has examined the regexes from these Internet sources. Our analysis was in the spirit of work on more general code re-use from Stack Overflow to GitHub. |
| Regex extractors | Tools to statically extract regexes from software written in 8 programming languages | Section 5 | | Adds 6 programming languages to [the tools from our FSE'18 paper](https://github.com/VTLeeLab/EcosystemREDOS-FSE18) |
| Regex corpus | A polyglot regex corpus of 537,806 unique regexes extracted from 193,524 projects written in 8 programming languages | *Collection*: Section 5, esp. Table 1. *Experiments*: Section 7 | This is the largest and most diverse regex corpus ever collected. It should be useful for future regex analysis purposes, e.g. in testing a visualization or input generation tool. | Our FSE'18 paper included a corpus of about 400,000 regexes extracted from about 670,000 npm and pypi modules (See Table 1 in [that paper](https://dl.acm.org/citation.cfm?id=3236027), and [that artifact](https://github.com/VTLeeLab/EcosystemREDOS-FSE18)). This new corpus covers 6 more programming languages. |
| Regex analyses: Semantic | Drivers for 5 input generators | Section 7.1 | Collects, improves, and unifies existing input generators | |
| Regex analyses: Performance | Drivers for 3 super-linear regex detectors | Section 7.2 | Extends existing super-linear regex detectors to partial-match semantics | Builds on the tooling from our FSE'18 paper |

In addition to this directory's `README.md`, each sub-tree comes with one or more READMEs describing its contents.

## Dependencies

Export the following environment variables to ensure the tools know how to find each other.
- `ECOSYSTEM_REGEXP_PROJECT_ROOT`
- `VULN_REGEX_DETECTOR_ROOT` (dependency, set it to `ECOSYSTEM_REGEXP_PROJECT_ROOT/analysis/performance/vuln-regex-detector`)

See `.env` for examples.

## Installation

### By hand

To install, execute the script `./configure.sh` on an Ubuntu 16.04 machine with root privileges.
This will obtain and install the various dependencies (e.g. OS packages, REDOS detectors) and compile all analysis tools.

The final line of this script is `echo "Configuration complete. I hope everything works!"`.
If you see this printed to the console, great!
Otherwise...alas.

### Container

!!!!!!!!!!!!!!
!Not yet done!
!!!!!!!!!!!!!!

(However, see containerized/Dockerfile -- this may work?)

To facilitate replication, we have published a [containerized version](https://hub.docker.com/r/jamiedavis/davismichaelcoghlanservantlee-fse19-regexartifact/) of this project on hub.docker.com.
The container is based on an Ubuntu 16.04 image so it is fairly large.
  
For example, you might run:

```
docker pull jamiedavis/davismichaelcoghlanservantlee-fse19-regexartifact
docker run -ti jamiedavis/davismichaelcoghlanservantlee-fse19-regexartifact
> vim .env
# Set ECOSYSTEM_REGEXP_PROJECT_ROOT=/davis-fse19-artifact/LinguaFranca-FSE19
> . .env
> # Proceed to use our tools, see some examples below
```

## Use

### One stop shop

We have prepared a simple script to drive the analysis on a single node on a subset of the regexes.
The actual analyses were performed on a compute cluster, as detailed in the paper.

To use this script, run the following command and wait about 10 minutes for all of the phases to complete.
(The performance analysis is the expensive part and takes more than half the time).

```
$ECOSYSTEM_REGEXP_PROJECT_ROOT/analysis/run-analyses.pl 50
```

This command will produce output like this:

```
...
Analysis complete. Performed syntax, semantic, and performance analyses.

  /tmp/LF-826/results: data files
  /tmp/LF-826/logs: reports and logs
  /tmp/LF-826/vis: visualizations

  Clean up with:
    rm -rf /tmp/LF-826
```

The directory name will vary in each run, but you can find:
- The various data files in the `results` subdir
- The program logs and tabular reports in the `logs` subdir
- Sample visualizations akin to those in the paper in the `vis` subdir

Of course, none of the results will match those in the paper when performed on a subset of the data,
but hopefully this is enough to give you a sense of how you *could* replicate the results in the paper.

See the following sections for sample commands for each step of the analysis.

### Analysis phases

Our analyses work on a set of regexes.
You can use the tail of the full corpus to see how things go.

```
tail -10 $ECOSYSTEM_REGEXP_PROJECT_ROOT/data/production-regexes/uniq-regexes-8.json > 10-regexes.json
```

#### Syntax

```
$ECOSYSTEM_REGEXP_PROJECT_ROOT/bin/test-for-syntax-portability.py --regex-file 10-regexes.json --out-file 10-syntax.json 2>10-syntax.log
```

This should run quickly.
If you examine the tail of `10-syntax.log`, you'll see output like this:

```
11/06/2019 02:05:13 woody/22034: Generating a quick summary of regex syntax support
11/06/2019 02:05:13 woody/22034: Number of supporting languages    Number of regexes
11/06/2019 02:05:13 woody/22034:                              7                    1
11/06/2019 02:05:13 woody/22034:                              8                    9
11/06/2019 02:05:13 woody/22034:


11/06/2019 02:05:13 woody/22034:        Language Number of supported regexes
11/06/2019 02:05:13 woody/22034:      javascript                   10
11/06/2019 02:05:13 woody/22034:            rust                    9
11/06/2019 02:05:13 woody/22034:             php                   10
11/06/2019 02:05:13 woody/22034:          python                   10
11/06/2019 02:05:13 woody/22034:            ruby                   10
11/06/2019 02:05:13 woody/22034:            perl                   10
11/06/2019 02:05:13 woody/22034:            java                   10
11/06/2019 02:05:13 woody/22034:              go                   10
11/06/2019 02:05:13 woody/22034:
```

Apparently one regex was unsupported in Rust, while the other 9 regexes were supported in all 8 languages.

If you examine `10-syntax.json`, you'll see enhanced libLF.Regex objects -- they now have the `supportedLangs` member populated.
The row with the pattern containing the string "avatar" lists 7 of the languages but not Rust, because Rust does not support the escaped forward slash notation as a valid construct.

#### Semantics

The semantics test should be run on the result of the syntax test, since it needs to know the `supportedLangs` of the libLF.Regex objects.

```
$ECOSYSTEM_REGEXP_PROJECT_ROOT/bin/test-for-semantic-portability.py --regex-file 10-syntax.json --out-file 10-semantic.json 2>10-semantic.log
```

This may take a few minutes.
Once it's done, you can look at the tail of `10-semantic.log`.
These 10 regexes are fairly dull from a semantic perspective:

```
  0 (0.00%) of the 10 completed regexes had at least one witness for different behavior
```

If you examine `10-semantic.json`, you'll see that the libLF.Regex objects have been enhanced in a different way:
- They have the `nUniqueInputsTested` member set to the number of inputs that were attempted for each regex
- They have the `semanticDifferenceWitnesses` member set, though since none were found all of those lists are empty

For demonstration purposes, we have prepared a regex file that has semantic difference witnesses.
(cf. the final row of Table 4).

```
$ECOSYSTEM_REGEXP_PROJECT_ROOT/bin/test-for-semantic-portability.py --regex-file demo/semantic-difference-witness-regex.json --out-file demo-semantic.json 2>demo-semantic.log
```

The log file now ends more enticingly:

```
  1 (100.00%) of the 1 completed regexes had at least one witness for different behavior
```

If you examine `demo-semantic.json`, you'll see the inputs that triggered semantic differences, with a breakdown of the distinct behaviors observed and the languages that evinced each behavior.

#### Performance

Run a performance analysis on the `10-regexes.json` file like this:

```
$ECOSYSTEM_REGEXP_PROJECT_ROOT/bin/test-for-SL-behavior.py --regex-file 10-regexes.json --out-file 10-performance.json --sl-timeout 10 --power-pumps 100000 2>10-performance.log
```

This takes a few minutes parallelized across my 8-core desktop.
If you're desperate, you can just run it on a 1-regex file instead of the 10-regex file we've been using.

Once complete, take a look at the end of `10-performance.log`. It says:

```
11/06/2019 01:56:43 woody/20094: Successfully performed SLRegexAnalysis on 10 regexes, 0 exceptions
11/06/2019 01:56:43 woody/20094: 1 of 10 successful analyses timed out in some language
11/06/2019 01:56:43 woody/20094: 1 of the regexes had different performance in different languages
11/06/2019 01:56:43 woody/20094: 0 of the regexes had different performance in the languages they actually appeared in
```

If you examine `10-performance.json`, you should see enhanced libLF.Regex objects. 
According to the log, one of these exhibited super-linear behavior
If you search the `10-performance.json` file for the string '100000": true', you will see that a regex pattern beginning `proxy.*fooo` timed out on an input of 100000 pumps in the following programming languages:
- javascript
- php
- python
- ruby
- java

## Directory structure

| File or Directory/    | Description |
|:---------------------:|:------------|
| README.md             | You're in it                                                    |
| PAPER.pdf             | Non-anonymized manuscript we submitted for review (not camera-ready) |
| LICENSE               | Terms of software release                                       |
| STATUS                | Claims of artifact quality                                      |
| INSTALL               | "Install instructions"                                          |
|-----------------------|-----------------------------------------------------------------|
| containerized/        | Dockerfile for building container                               |
| configure.sh          | One-stop-shop for configuration                                 |
|-----------------------|-----------------------------------------------------------------|
| survey/               | Survey instrument                                               |
| data/                 | Corpuses (internet and production) and tools to reproduce them  |
| analysis/             | Experimental analyses (syntax, semantic, performance)           |
| full-analysis/        | Run each analysis step on a regex                               |
| lib/                  | Python libraries -- utility routines, serializers and parsers for types expressed in JSON |
| bin/                  | Symlinks to the tools scattered throughout the tree, easing access from analysis scripts |
| regex-engine-bugs/    | README with links to the bugs we opened against regex engines or documentation |

Each directory contains its own README with additional details.

## Style and file formats

### Style

Most of the scripts in this repository are written in Python.
They tend to write status updates to STDERR, and write their output to an NDJSON-formatted --out-file of serialized libLF objects.

If you have dependencies on other scripts in the repo, require the invoker to define `ECOSYSTEM_REGEXP_PROJECT_ROOT`.
This environment variable should name the location of your clone of this repository.

### File formats

This project uses JSON to describe research data. Files named `*.json` are generally [NDJSON](http://ndjson.org/)-formatted files that contain one JSON object per line.

Why giant flat files?
- Makes it easy to do a line-by-line streaming analysis on the objects in the file, even if the file is large.
- Makes it easy to divide work amongst the nodes in a compute cluster.
- Makes it easy to share data with other researchers.

## Contact

Contact J.C. Davis at davisjam@vt.edu with any questions.
