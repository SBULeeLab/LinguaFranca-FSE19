#!/usr/bin/env perl
# Compile the static extractors
#   Java: Needs mvn
#   JS: Needs npm
#   Perl: Needs cpan
#   PHP: Needs composer
#   Ruby: Needs the Ripper module installed
#   Rust: Needs access to a nightly build that supports -Z. See the usage message for rust/extract-rust-regexes.py

use strict;
use warnings;

print "Configuring/Compiling the static extractors\n";

print "Configuring java\n";
system("cd java/regex-extractor/; mvn package; cd -");

print "Configuring go\n";
system("cd go; make; cd -");

print "Configuring js\n";
system("cd js; npm install; cd -");

print "Configuring perl\n";
system("cd perl; ./install.sh; cd -");

print "Configuring php\n";
system("cd php; composer install; cd -");

print "Configuring python\n";
system("cd python; pip install --user -r requirements.txt; cd -");

print "Configuring typescript\n";
system("cd ts; npm install; npm run build; cd -");

print "Hope everything went well...\n";
