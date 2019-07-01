#!/usr/bin/env perl

use strict;
use warnings;

if (not @ARGV) {
  die "Usage: $0 num-regexes-to-analyze\nExample: $0 50\n";
}

# Make tmp dirs
my $RUN_DIR = "/tmp/LF-$$";
&cmd("mkdir $RUN_DIR");

my $VIS_DIR = "$RUN_DIR/vis";
&cmd("mkdir $VIS_DIR");

my $LOG_DIR = "$RUN_DIR/logs";
&cmd("mkdir $LOG_DIR");

my $RESULT_DIR = "$RUN_DIR/results";
&cmd("mkdir $RESULT_DIR");

# Here we go
my $numRegexesToTail = int($ARGV[0]);
my $baseRegexFile = "$ENV{ECOSYSTEM_REGEXP_PROJECT_ROOT}/data/production-regexes/uniq-regexes-8.json";

my $tmpFilePrefix = "$RESULT_DIR/regexes";
my $smallRegexFile = "$tmpFilePrefix-base.json";
my $syntaxFile = "$tmpFilePrefix-syntax.json";
my $semanticFile = "$tmpFilePrefix-semantic.json";
my $performanceFile = "$tmpFilePrefix-performance.json";

&createSmallRegexFile($baseRegexFile, $smallRegexFile, $numRegexesToTail);
&runSyntaxAnalysis($smallRegexFile, $syntaxFile);
&runSemanticAnalysis($syntaxFile, $semanticFile);
&runPerformanceAnalysis($syntaxFile, $performanceFile);
&printSummary();

#########
# Analysis stages
#########

sub createSmallRegexFile {
  my ($baseRegexFile, $smallRegexFile, $nRegexes) = @_;

  &logPhase("Creating small regex file from $baseRegexFile ($numRegexesToTail regexes)");

  &cmd("tail -$numRegexesToTail $baseRegexFile > $smallRegexFile");
}

sub runSyntaxAnalysis {
  my ($regexFile, $outFile) = @_;

  &logPhase("Running syntax analysis");

  &cmd("$ENV{ECOSYSTEM_REGEXP_PROJECT_ROOT}/bin/test-for-syntax-portability.py --regex-file $regexFile --out-file $outFile 2>$LOG_DIR/syntax-$$.log");
}

sub runSemanticAnalysis {
  my ($regexFile, $outFile) = @_;

  &logPhase("Running semantic analysis");

  &cmd("$ENV{ECOSYSTEM_REGEXP_PROJECT_ROOT}/bin/test-for-semantic-portability.py --regex-file $regexFile --out-file $outFile --rngSeed 1 > $LOG_DIR/test-semantic-$$-log.txt 2>&1");
  &cmd("$ENV{ECOSYSTEM_REGEXP_PROJECT_ROOT}/bin/analyze-semantic-portability.py --regex-file $outFile --vis-dir $VIS_DIR >$LOG_DIR/analyze-semantic-$$-report.txt 2>$LOG_DIR/analyze-semantic-$$-log.txt");
}

sub runPerformanceAnalysis {
  my ($regexFile, $outFile) = @_;

  &logPhase("Running performance analysis");

  &cmd("$ENV{ECOSYSTEM_REGEXP_PROJECT_ROOT}/bin/test-for-SL-behavior.py --regex-file $regexFile --out-file $outFile > $LOG_DIR/test-performance-$$-log.txt 2>&1");
  &cmd("$ENV{ECOSYSTEM_REGEXP_PROJECT_ROOT}/bin/analyze-SL-behavior.py --slra-file $outFile --vis-dir $VIS_DIR >$LOG_DIR/analyze-performance-$$-report.txt 2>$LOG_DIR/analyze-performance-$$-log.txt");
}

sub printSummary {
  print "Analysis complete. Performed syntax, semantic, and performance analyses.

  $RESULT_DIR: data files
  $LOG_DIR: reports and logs
  $VIS_DIR: visualizations

  Clean up with:
    rm -rf $RUN_DIR
";
}

#########
# Utils
#########

sub cmd {
  my ($cmd) = @_;
  &log($cmd);
  my $out = `$cmd`;
  my $rc = $? >> 8;
  if ($rc) {
    die "Error, cmd <$cmd> got rc $rc out\n$out\n";
  }

  return $out;
}

sub log {
  my ($msg) = @_;
  my $now = localtime;
  print STDERR "$now: $msg\n";
}

sub logPhase {
  my ($msg) = @_;
  my $dashes = "-" x 50;
  my $xmsg = "\n\n$dashes\n\t$msg\n$dashes\n";
  &log($xmsg);
}
