#!/usr/bin/env ruby

foo = 'abc'
flags = Regexp::IGNORECASE | Regexp::MULTILINE

# /RegexLiteral/
/abc/ # Static regex
/def/m # Static regex with flags
%r{abc}x
/#{Regexp.quote(foo)}/ # Dynamic regex
/#{Regexp.quote(foo)}/i # Dynamic regex with flags

# RegexpCreation 
## new
Regexp.new("abc")
Regexp.new("abc", 0)
Regexp.new("abc", Regexp::IGNORECASE) # Static with static flags
Regexp.new("abc", Regexp::IGNORECASE | Regexp::MULTILINE) # Static with static flags
_ = Regexp.new(foo, Regexp::IGNORECASE | Regexp::MULTILINE) # Dynamic with flags
_ = Regexp.new(foo, flags) # Dynamic with dynamic flags
_ = Regexp.new("abc", 0, "n")
_ = Regexp.new(/FromRegex/)

## compile
_ = Regexp.compile("abc")
Regexp.compile("abc", 0)
Regexp.compile("abc", 0, "n")
