#!/usr/bin/env perl

use strict;
use warnings;

use File::Basename;
use File::Spec;
use Cwd qw(abs_path);

# The dirname() thing will only work if this script is invoked directly, not via symlink
my $toolDirname = dirname(abs_path($0));
my $jar = File::Spec->catfile($toolDirname, "target", "query-java-1.0-shaded.jar");

# java -jar JARFILE ...
exec("java", "-jar", $jar, @ARGV);
