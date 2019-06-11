# Summary

This directory is concerned with generating a diverse set of input strings for regexes.

These strings should be used with vuln-regex-detector's per-language regex evaluation scripts
to determine whether any regex + string combinations behave differently in different languages.

## How does it work?

Regexes are complicated and randomly testing strings would not be very useful.
We rely instead on the following input generators:
1. [Eric Larson's EGRET](http://fac-staff.seattleu.edu/elarson/web/regex.htm)
2. [Veanes et al.'s Rex](https://www.microsoft.com/en-us/research/publication/rex-symbolic-regular-expression-explorer/)
3. [Shen et al.'s ReScue](http://cs.nju.edu.cn/changxu/1_publications/ASE18.pdf)
    - ReScue discovers strings that improve node coverage for super-linear regex detection.
		  Along the way, it tests and mutates a bunch of strings.
			We use those strings as inputs.
4. [Arcaini et al.'s MutRex](https://cs.unibg.it/gargantini/research/papers/mutrexSIstvr2017.pdf)
5. [Moeller's Brics](http://www.brics.dk/automaton/)
    - The jar file is built from my [fork](https://github.com/davisjam/dk.brics.automaton/tree/RandomStringGenerator)
		  which introduces *random* instead of *exhaustive* string generation

## What are the components?

### test-regex-semantic-compatibility.py

This is the high-level tool you should use.
Give it a regex, it produces a match result.

### gen-input-for-regex.py

This is a helper.
Given a regex, it emits a set of inputs proposed by various input generators.

### generators

Folder holding drivers for and the src of input generators 
Each of the drivers is a independent python CLI that is set up to be envoked
either stand alone or through gen-input-for-regex.py

# Set-Up

The `compile-input-generators.pl` script should take care of this for you.

## EGRET

Before running the EGRET extractor you will need to build the EGRET tool.
See the README.md for egret.

## Rex

Before running the Rex extractor you will need to install wine so that `wine` executes properly.
More info on installing wine can be found [here](https://wiki.winehq.org/Wine_Installation_and_Configuration).
The distribution for Ubuntu should work fine.

## ReScue

Run `mvn package`.

## MutRex

Nothing. The jar file is included in the repo.

## Brics

Nothing. The jar file is included in the repo.
