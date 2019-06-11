#!/usr/bin/env perl
# Compile the regex testers

use strict;
use warnings;

print "Configuring/Compiling the regex testers\n";

print "Configuring java\n";
system("cd java/; mvn package; cd -");

print "Configuring go\n";
system("cd go; make; cd -");

print "Configuring js\n";
#system("cd js; npm install; cd -");

print "Configuring perl\n";
#system("cd perl; ./install.sh; cd -");

print "Configuring php\n";
#system("cd php; composer install; cd -");

print "Configuring python\n";
#system("cd python; pip install --user -r requirements.txt; cd -");

print "Configuring rust\n";
system("cd rust; make; cd -");

print "Hope everything went well...\n";
