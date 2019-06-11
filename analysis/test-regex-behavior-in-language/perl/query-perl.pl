#!/usr/bin/env perl
# Author: Jamie Davis <davisjam@vt.edu>
# Description: Test regex in Perl

use strict;
use warnings;

use JSON::PP; # I/O
use Carp;

# Arg parsing.
my $queryFile = $ARGV[0];
if (not defined($queryFile)) {
  print "Error, usage: $0 query-file.json\n";
  exit 1;
}

# Load query from file.
my $query = decode_json(&readFile("file"=>$queryFile));

# Check query is valid.
my $validQuery = 1;
my @requiredQueryKeys = ('pattern', 'inputs');
for my $k (@requiredQueryKeys) {
  if (not defined($query->{$k})) {
    $validQuery = 0;
  }
};
if (not $validQuery) {
  &log("Error, invalid query. Need keys <@requiredQueryKeys>. Got " . encode_json($query));
  exit 1;
}

&log("Query is valid");

# Try to match string against pattern.


my @resultObjs;

my $result = $query;
for my $input (@{$query->{inputs}}) {
  my ($validPattern, $matched, $matchedString, $captureGroups) = &getResult($query->{pattern}, $input);
  if ($validPattern) {
    $result->{validPattern} = 1;
    my $resultObj = {
      "input" => $input,
      "matched" => $matched,
      "matchContents" => {
        "matchedString" => $matchedString,
        "captureGroups" => $captureGroups,
      },
    };
    push @resultObjs, $resultObj;
  } else {
    $result->{validPattern} = 0;
    last;
  }
}
$result->{results} = \@resultObjs;

print encode_json($result) . "\n";
exit 0;

##################

sub log {
  my ($msg) = @_;
  my $now = localtime;
  print STDERR "$now: $msg\n";
}

# input: %args: keys: file
# output: $contents
sub readFile {
  my %args = @_;

	open(my $FH, '<', $args{file}) or confess "Error, could not read $args{file}: $!";
	my $contents = do { local $/; <$FH> }; # localizing $? wipes the line separator char, so <> gets it all at once.
	close $FH;

  return $contents;
}

# returns: ($validPattern, $matched, $matchedString, $captureGroups)
sub getResult {
  my ($pattern, $input) = @_;

  my $len = length($input);
  &log("matching: pattern /$pattern/ inputStr: len $len");

  my $validPattern = 1;
  my $matched = 0;
  my $matchedString = "";
  my $captureGroups = [];

  # Eval in case the regex is invalid
  eval {
    # Perform the match
    # TODO Match by variable interpolation works with most escaped directives but has problems with \Q and \E.
    if ($input =~ m/$pattern/) {
      $matched = 1;
      $matchedString = $&; # I love perl

      # If there were capture groups, collect their contents.
      # Apply a second match in list context to obtain capture groups.
      # Magic $#+: See notes for @- (http://perldoc.perl.org/perlvar.html#@LAST_MATCH_START)
      if (0 < $#+) {
        my @matches = ($input =~ m/$pattern/);
        @matches = map { if (defined $_) { $_ } else { ""; } } @matches; # Convert undef's to "" for consistency
        &log("Matches: <@matches>");
        $captureGroups = \@matches;
      }
    }
  };

  # this just catches all warnings -- can we specify by anything other than string text?
  if ($@) {
    $validPattern = 0;
  } else {
    # No exceptions -- valid pattern
    $validPattern = 1;
  }

  return ($validPattern, $matched, $matchedString, $captureGroups);
}

