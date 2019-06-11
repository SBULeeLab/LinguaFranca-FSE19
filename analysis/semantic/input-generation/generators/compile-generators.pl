#!/usr/bin/env perl
# Compile the input generators

use strict;
use warnings;

print "Configuring/Compiling the input generators\n";

print "Configuring ReScue\n";
system("cd ReScue/; mvn package; cd -");

print "Configuring Egret\n";
system("cd egret/src; make; cd -");

print "Hope everything went well...\n";
