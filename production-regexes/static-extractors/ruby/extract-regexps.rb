#!/usr/bin/env ruby

require 'ripper'
require 'pp' # Pretty print. 'pp x' will pretty-print most things to STDOUT.
require 'json'

# Globals
$DYNAMIC_PATTERN = 'DYNAMIC'
$UNKNOWN_PATTERN = 'UNKNOWN'
$DYNAMIC_FLAGS = 'DYNAMIC'
$UNKNOWN_FLAGS = 'UNKNOWN'
$regexes = []

$TYPE_LITERAL = 'LITERAL'
$TYPE_OBJECT = 'OBJECT'

# Classes

class MyRegexBuilder
  # Return true if it looks like a regex, else false
  # Useful as an interestingF method.
  def self.isInteresting(sexp)
    begin
      return self._isRegexLiteral(sexp) || self._isRegexCreation(sexp)
    rescue
      return false
    end
  end

  # Returns a MyRegex based on this sexp
  # (or nil)
  # Useful as part of a visitF method.
  def self.factory(sexp)
    begin
      if self._isRegexLiteral(sexp)
        return self._fromRegexLiteral(sexp) 
      elsif self._isRegexCreation(sexp)
        return self._fromRegexCreation(sexp) 
      end
    rescue
      return nil
    end
  end

  # Helper. Assumes sexp is a regex literal and verifies this fact.
  # May throw.
  # Ruby regexes can be created using /re/opt and %{re}opt.
  def self._isRegexLiteral(sexp)
    return sexp[0] == :regexp_literal
  end

  # Helper. Assumes sexp is a regex creation and verifies this fact.
  # May throw.
  # Ruby regexes can be created using Regexp.new(str[, opt[, lang]])
  # and Regexp.compile(str[, opt[, lang]]).
  def self._isRegexCreation(sexp)
    return sexp[0] == :method_add_arg &&
           sexp[1][0] == :call &&
           sexp[1][1][0] == :var_ref &&
           sexp[1][1][1][0] == :@const &&
           sexp[1][1][1][1] == "Regexp" &&
           sexp[1][2] == :"." &&
           sexp[1][3][0] == :@ident &&
           (sexp[1][3][1] == "new" || sexp[1][3][1] == "compile")
  end

  # Helper. sexp is a regex literal.
  # May throw if there are variations we don't know about.
  # Returns nil on failure
  def self._fromRegexLiteral(sexp)
    my_log("MyRegexBuilder: Building from RegexLiteral")

    child = sexp[1]
    if child[0][0] == :@tstring_content
      if sexp[2][0] == :@regexp_end
        # A static "inline regexp" like /abc/i
        pat = child[0][1]
        # flags: '/ix' or '}ix' --> 'ix'
        #   /ix is for /abc/ix
        #   }ix is for %r{abc}ix
        flags = sexp[2][1].chars[1..-1].join('')
        if flags == nil
          flags = ''
        end
        my_log('pat: ' + pat)
        my_log('flags: ' + flags)
        return MyRegex.new(pat, flags, $TYPE_LITERAL)
      else
        # Not sure what's here
        my_log("UNKNOWN pattern")
        return MyRegex.new($UNKNOWN_PATTERN, $UNKNOWN_FLAGS, $TYPE_LITERAL)
      end
    else
      # pattern is not a :@tstring_content
      my_log("DYNAMIC pattern")
      return MyRegex.new($DYNAMIC_PATTERN, $UNKNOWN_FLAGS, $TYPE_LITERAL)
    end

    # Not sure how this happened
    my_log("UNKNOWN anything")
    return MyRegex.new($UNKNOWN_PATTERN, $UNKNOWN_FLAGS, $TYPE_LITERAL)
  end

  def self._fromRegexCreation_getPat(sexp)
    if sexp[0] == :string_literal &&
       sexp[1][0] == :string_content &&
       sexp[1][1][0] == :@tstring_content
       return sexp[1][1][1]
    else
      return $DYNAMIC_PATTERN
    end
  end

  def self._fromRegexCreation_getOpts(sexp)
    if sexp[0] == :var_ref
      return $DYNAMIC_FLAGS
    elsif sexp[0] == :const_path_ref &&
          sexp[1][0] == :var_ref &&
          (sexp[1][1][0] == :@const && sexp[1][1][1] == "Regexp") &&
          sexp[2][0] == :@const
      return sexp[2][1]
    else
      # TODO. Recurse for Binary flag names 'X | Y | Z'.
      my_log("_fromRegexCreation_getOpts: Unsupported: RegexCreation with binary flags")
      return $UNKNOWN_FLAGS
    end

    my_log("_fromRegexCreation_getOpts: unknown")
    return $UNKNOWN_FLAGS
  end

  # Helper. sexp is a regex creation.
  # May throw if there are variations we don't know about.
  # Returns nil on failure
  def self._fromRegexCreation(sexp)
    my_log("MyRegexBuilder: Building from RegexCreation")

    # Get pattern
    if sexp[0] == :method_add_arg &&
       sexp[1][0] == :call &&
       sexp[1][1][0] == :var_ref &&
       sexp[1][1][1][0] == :@const &&
       sexp[1][1][1][1] == "Regexp" &&
       sexp[1][2] == :"." &&
       sexp[1][3][0] == :@ident &&
       (sexp[1][3][1] == "new" || sexp[1][3][1] == "compile")
      # Regex.new() and Regex.compile() take the same args: (str[, opts[, lang]])
      arg_paren = sexp[2]
      args_add_block = arg_paren[1]

      arg_pat = nil
      arg_opts = nil
      pat = nil
      flags = ""
      if args_add_block[1].length >= 1
        arg_pat = args_add_block[1][0]
        pat = self._fromRegexCreation_getPat(arg_pat)
      end
      if args_add_block[1].length >= 2
        arg_opts = args_add_block[1][1]
        flags = self._fromRegexCreation_getOpts(arg_opts)
      end

      return MyRegex.new(pat, flags, $TYPE_OBJECT)
    end

    return nil
  end
end

class MyRegex
  def initialize(pattern, flags, type)
    @pattern = pattern
    @flags = flags
    @type = type
  end

  def emitJSON()
    _hash = {:pattern => @pattern, :flags => @flags, :type => @type}
    puts JSON.generate(_hash)
  end

	def pattern()
		@pattern
	end
	
	def flags()
		@flags
	end

end

class SimpleFileWithRegexes
  def initialize(fileName, language, couldParse, regexes)
	  # regexes: an array of objects with keys 'pattern', 'flags'
    @fileName = fileName
    @language = language
    @couldParse = couldParse
    @regexes = regexes
  end

  def emitJSON()
    _hash = {
      :fileName => @fileName,
			:language => @language,
			:couldParse => @couldParse,
			:regexes => @regexes
    }
    puts JSON.generate(_hash)
  end
end


# Functions

def my_log(msg)
  STDERR.puts msg
end

# Apply visitF to sexp on nodes for which interesting(node) is true
#  interestingF: Proc -- only visitF.call(node) if interestingF.call(node) is true
#  visitF: Proc for nodes of interest
# NB Proc's should not 'return'.
def walk_sexp_filtered(sexp, interestingF, visitF)
  applyIf = Proc.new do |node|
    if interestingF.call(node)
      visitF.call(node)
    end
  end

  walk_sexp(sexp, applyIf)
end

# walk_sexp(sexp, visitF)
#   visitF is a Proc
#   cf. https://mixandgo.com/learn/mastering-ruby-blocks-in-less-than-5-minutes
#   cf. https://medium.com/@sihui/what-the-heck-are-code-blocks-procs-lambdas-and-closures-in-ruby-2b0737f08e95
#
# Apply visitF to every node in sexp recursively
# First we apply visitF to sexp itself.
# Then we apply visitF to each of sexp's children.
def walk_sexp(sexp, visitF)
  # Invalid input
  if !sexp
    return sexp
  end

  # Apply to self
  visitF.call(sexp)

  if Array === sexp
    # Recurse:
    # Apply to contents
    # I think every sexp is an Enumerable or at least Enumerable-ish.
    # cf. ruby/test/ripper/test_sexp.rb

    sexp.each_entry do |e|
      walk_sexp(e, visitF)
    end
  else
    # Base case
    return sexp
  end
end

def main
  # Check usage
  if ARGV.length != 1
    puts("Usage: #{$0} file-to-analyze.rb")
    exit(1)
  end

  # Read in the file
	rubyFile = ARGV[0]
  file = File.open(rubyFile, "r")
  contents = file.read
  file.close()

  # Parse
  sexp = Ripper.sexp(contents)

  interestingF = Proc.new do |node|
    MyRegexBuilder.isInteresting(node)
  end

  extractRegexpF = Proc.new do |node|
    re = MyRegexBuilder.factory(node)
    if re
      $regexes.push(re)
    end
    re
  end

  # Walk the AST and extract MyRegex objects.
  # Append them to $regexes
  walk_sexp_filtered(sexp, interestingF, extractRegexpF)

  # Extract and dump toNDJSON in SimpleFileWithRegexes format.
	regexArray = Array.new()
  $regexes.each_entry do |re|
    regexArray.push({
			"pattern" => re.pattern,
			"flags"   => re.flags
		})
  end
  sfwr = SimpleFileWithRegexes.new(rubyFile, "Ruby", 1, regexArray)
	sfwr.emitJSON()
end

################

main()
