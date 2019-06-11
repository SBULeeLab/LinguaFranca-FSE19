#!/usr/bin/env perl
# Extract regexes from the perl file named in the first argument.
# Regexp-like things appear in three ways: https://perldoc.perl.org/perlop.html#Binding-Operators
#     - Match: m/REGEX/ aka /REGEX/
#     - Substitute: s/REGEX/replacement/
#     - Transliteration: tr/abc/xyz/ aka y/abc/xyz/
#
# Extract regex pattern and flags from Match and Substitute regexes.
# We omit Transliteration.
#   Transliteration is treated as a regexp token by PPI: PPI::Token::Regexp::Transliterate
#     (y// or tr//: see https://perldoc.perl.org/perlop.html#Quote-Like-Operators)
#   However, this is not a regex in the sense that we mean it, so we omit such tokens.

use strict;
use warnings;

use PPI::Document;
use PPI::Dumper;
use PPI::Find;

use JSON;

# Some regexes. So we can point at ourselves for testing.
my $str = 'abc';
my $regex = 'abc';
if ($str =~ $regex) {}
if ($str =~ m/abc/gi) {}
if ($str =~ /abc/) {}
if ($str =~ s/a/b/g) {}
if ($str =~ s/a+(bc|df)\\\[\]/b/g) {}
while ($str =~ m/qqqq/g) {}
$str =~ tr/a/z/;
$str =~ y/a/z/;
$str =~ m!a!;
$str =~ m'a';
$str =~ m"a";
$str =~ s"a"b";
$str =~ s"a"b";
$str =~ s.a.b.;
$str =~ m<a>;
$str =~ m(a);
$str =~ m[a];
$str =~ m{a};

# Load a document
if (not @ARGV) {
  die "Usage: $0 perl-source-file\n";
}
my $sourceFile = $ARGV[0];

eval {
  # Create a document
  my $doc = PPI::Document->new($sourceFile);

  #&dumpAll($doc);
  my @regexesWithFlags = extractRegexesWithFlags($doc);
  my $simpleFileWithRegexesObj = {
    "fileName" => $sourceFile,
    "language" => "Perl",
    "couldParse" => 1,
    "regexes"  => \@regexesWithFlags
  };
  print encode_json($simpleFileWithRegexesObj) . "\n";
  exit 0;
};
if ($@) {
  my $simpleFileWithRegexesObj = {
    "fileName" => $sourceFile,
    "language" => "Perl",
    "couldParse" => 0,
  };
  print encode_json($simpleFileWithRegexesObj) . "\n";
  exit 0;
}

##################################

sub extractRegexesWithFlags {
  my ($doc) = @_;

  # Find regexes
  my $Find = PPI::Find->new( \&wanted );
  
  my @found = $Find->in( $doc );
  my @regexes;
  for my $elt (@found) {
    print STDERR "Elt: " . $elt->class() . " --> " . $elt->content() . "\n";
    push @regexes, &regexTokenToPatternAndFlags($elt);
  }

  return @regexes;

  ### Helpers

  sub getBeginDelim {
    my (@chars) = @_;

    for (my $i = 0; $i < scalar(@chars); $i++) {
      # Characters other than these can serve as delimiters, I think.
      # I cannot find a clear statement about it in the perl docs.
      if ($chars[$i] !~ m/^[a-zA-Z0-9_]$/) {
        return $chars[$i];
      }
    }

    die "Error, could not find beginDelim in chars <@chars>\n";
  }

  # @param $elt: PPI::Element of type PPI::Token::Regexp::{Match|Substitute}
  # @returns $regexObj
  #   keys: pattern "abc" flags "gi"
  #   unref on parsing error
  sub regexTokenToPatternAndFlags {
    my ($elt) = @_;

    my $content = $elt->content();
    my @chars = split("", $content);

    # Indices of delimiters.
    # Using these we can compute pattern and flags.
    # Obtaining the delimiters is different for ::Match and ::Substitute.
    my ($beginIx, $midIx, $endIx);

    if ($elt->class() eq "PPI::Token::Regexp::Match") {
      # Examples:
      #   m/a/g
      #   /a/
      #   'a'
      #   (a)
      #   {a}
      #   [a]
      #   <a>

      my %delimPairs = (
        "(" => ")",
        "[" => "]",
        "{" => "}",
        "<" => ">",
      );
      my ($beginDelim, $endDelim);

      $beginDelim = &getBeginDelim(@chars);
      if ($delimPairs{$beginDelim}) {
        $endDelim = $delimPairs{$beginDelim};
      } else {
        $endDelim = $beginDelim;
      }

      # No danger of escapes here -- can't escape before the first or the last.
      # If the program parsed then this will work.
      $beginIx = index($content, $beginDelim);
      $endIx = rindex($content, $endDelim);
      if (not ($beginIx < $endIx)) {
        die "Error, could not find endIx in chars: <@chars>\n";
      }
      $midIx = $endIx;
    } elsif ($elt->class() eq "PPI::Token::Regexp::Substitute") {
      # Examples:
      # s/a/b/
      # s/a/b/g

      my ($beginDelim, $midDelim, $endDelim);

      # No pairing here. Must be the same delim in each place.
      $beginDelim = &getBeginDelim(@chars);
      $midDelim = $beginDelim;
      $endDelim = $beginDelim;

      # Indexing won't work here. Crawl for unescaped delimiters.
      my $escaped = 0;
      $beginIx = -1;
      $midIx = -1;
      $endIx = -1;
      for (my $i = 0; $i < scalar(@chars); $i++) {
        if ($escaped) {
          $escaped = 0;
          next;
        }

        if ($beginIx < 0 and $chars[$i] eq $beginDelim) {
          $beginIx = $i;
        } elsif ($midIx < 0 and $chars[$i] eq $midDelim) {
          $midIx = $i;
        } elsif ($endIx < 0 and $chars[$i] eq $endDelim) {
          $endIx = $i;
        }

        if ($chars[$i] eq "\\") {
          $escaped = 1;
        }
      }

      if ($beginIx < 0 or $midIx < 0 or $endIx < 0) {
        die "Error, could not find beginIx midIx or endIx in chars <@chars>\n";
      }

    } else {
      die "Unexpected class " . $elt->class() . "\n";
    }

    # Now we have beginIx, midIx, and endIx.
    # Using them, we can extract pattern and flags.

    #print "beginIx $beginIx midIx $midIx endIx $endIx\n";

    my $pattern = substr($content, $beginIx + 1, ($midIx - $beginIx) - 1);
    my $flags = substr($content, $endIx + 1);

    return {
      "pattern" => $pattern,
      "flags"   => $flags,
    };
  }
  
  sub wanted {
    my ($elt, $root) = @_;
    return (
         ($elt->class() eq "PPI::Token::Regexp::Match")
      or ($elt->class() eq "PPI::Token::Regexp::Substitute")
    );
  }
}

# Trying to see what a document looks like
sub dumpAll {
  my ($doc) = @_;

  # Create the dumper
  my $Dumper = PPI::Dumper->new( $doc );
    
  # Dump the document
  $Dumper->print;
}