#!/usr/bin/env python3
# Description:
#   Extracts regexes from posts that answer questions tagged with 'regex'.
#   Writes them in InternetRegexSource format to --out-file.

# Import our lib
import os
import sys
sys.path.append('{}/lib'.format(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT']))
import libLF

# Private lib
from intermediateRegexPost import IntermediateRegexPost

import json
import argparse
import re
import html

# input: body
# output: [p1, ...]: the (unique) patterns identified in the body. Maybe empty.
def extractPatternsFromPostBody(body):
  #libLF.log('Extracting patterns from: {}'.format(body))

  # Posts typically contain regexes within code.
  # Code can be inline (`regex`) or in a block (```regex```).
  # cf. https://meta.stackoverflow.com/a/251362
  #
  # We are OK extracting non-regex content.
  # Our research question is whether InternetRegexSources appear in RegexUsages,
  # and extracting not-true-regexes from SO will (probably) not cause false matches to occur.
  #
  # Though they could! For example, I could put `re.DOTALL` in a post, which would
  # cause matches if someone has a regex searching for Python regex flags.
  # Supporting evidence like a URL in the source code would surely help.
  #
  # Do not compute any metrics like "Number of ignored regexes on SO",
  # because here we will extract things that are not regexes.
  # Such a metric would be inaccurate anyway since we're just looking at a sample of source code.

  ##
  # Type 1: inline
  ##
  #
  # Example:
  #   ...I'm using was <code>&lt;(.|\\n)+?&gt;</code>...
  #
  # Non-example:
  #    <p><a href=\"http://php.net/strip_tags\" rel=\"nofollow\"><code>strip_tags()</code></a> does this

  ##
  # Type 2: Code blocks that contain only regexes, possibly with perl- or sed-style formatting (/.../, s/.../g)
  ##
  #
  # Example:
  #   <pre><code>/&lt;\/?([^p](\s.+?)?|..+?)&gt;/
  #   </code></pre>
  #
  # Example:
  #   <pre><code>s/&lt;(?!\/?a(?=&gt;|\s.*&gt;))\/?.*?&gt;//g;
  #   </code></pre>
  #
  # Example:
  #  <p>How about</p>
  #
  #  <pre><code>&lt;[^a](.|\n)+?&gt;
  #  </code></pre>
  #
  #  <p>?</p>
  #

  ##
  # Type 3: Code blocks that contain a full code snippet
  ##
  #
  # Example:
  #   <p>One way: A bunch of positive lookahead assertations:</p>
  #
  #   <pre><code>#!/usr/bin/perl
  #   use warnings;
  #   use strict;
  #   use feature qw/say/;
  #   my @tests = ("The Guild demands that the spice must flow from Arrakis",
  #                "House Atreides will be transported to Arrakis by the Guild.");
  #   for my $test (@tests) {
  #     if ($test =~ m/^(?=.*spice)
  #                     (?=.*Guild)
  #                     (?=.*Arrakis)/x) {
  #       say "$test: matches";
  #     } else {
  #       say "$test: fails";
  #     }
  #   }
  #   </code></pre>

  possiblePatterns = []

  # Match all types -- all types include <code>...<code>
  # NB This is not altogether sound, but should be OK since
  # SO doesn't seem to nest code blocks.
  allCodeBlocks = re.findall(r'<code>\s*(.*?)\s*</code>', body, re.DOTALL)
  #allCodeBlocks = re.findall(r'(?<!<pre>)<code>(.*?)</code>', body, re.DOTALL)
  #libLF.log('{} code blocks'.format(len(allCodeBlocks)))
  for code in allCodeBlocks:
    # Filter out lines beginning with a comment
    lines = [line for line in code.split('\n') if len(line) and line[0] is not '#' and line[0] is not '%']
    # Discard code blocks that span more than one line.
    # This discards e.g. code snippets demonstrating logic around regexes.
    # It also discards very long regexes split across multiple lines.
    if 1 < len(lines):
      continue

    #libLF.log('code: {}'.format(code))

    # Un-escape special HTML characters like < and >.
    code = html.unescape(code)

    # If they included a leading and trailing slash, remove them.
    code = libLF.perlStyleToPattern(code)

    # Filter out things that aren't pattern-like
    if libLF.isRegexPattern(code):
      possiblePatterns.append(code)
      #libLF.log('code is a pattern: {}'.format(code))

  return list(set(possiblePatterns))

def main(regexPostsFile, outFile):
  libLF.log('Streaming patterns from regexPostsFile {} to outFile {}'.format(regexPostsFile, outFile))
  with open(regexPostsFile, 'r') as inStream, open(outFile, 'w') as outStream:
    nPosts = 0
    nPatterns = 0
    for line in inStream:
      nPosts = nPosts + 1

      # Get the patterns from either Q or A posts.
      # Either could be a source of a regex in "regex flow".
      post = IntermediateRegexPost()
      post.initFromNDJSON(line)
      patterns = extractPatternsFromPostBody(post.body)
      libLF.log('Post {} had {} patterns'.format(post.id, len(patterns)))
      nPatterns = nPatterns + len(patterns)

      # If there were any patterns, emit.
      if len(patterns):
        # Build a StackOverflowRegexSource
        source = libLF.StackOverflowRegexSource()
        source.initFromRaw(uri=post.getURI(), uriAliases=post.getURIAliases(), patterns=patterns)

        # Emit
        outStream.write(source.toNDJSON() + '\n')

    libLF.log('Streamed {} posts (found {} pattern-like things)'.format(nPosts, nPatterns))

###############################################

# Parse args
parser = argparse.ArgumentParser(description='Extract regexes from regex-themed Posts in stackoverflow-regexPosts.json')
parser.add_argument('--regex-posts', '-f', help='Path to stackoverflow-regexPosts.json', required=True)
parser.add_argument('--out-file', '-o', help='Where to write JSON results?', required=True)

args = parser.parse_args()

# Here we go!
main(args.regex_posts, args.out_file)
