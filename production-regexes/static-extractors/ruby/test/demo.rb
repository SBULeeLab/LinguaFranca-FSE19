#!/usr/bin/env ruby

# Declare regexes
/abc/
%r{def|geh}
Regexp.new("abc", Regexp::IGNORECASE)

# Assign regexes
r1 = /abc/
r2 = %r{def|geh}
r3 = Regexp.new("abc", Regexp::IGNORECASE)
r4 = Regexp.new("abc" + "def", Regexp::IGNORECASE)
pat = "abc"
r5 = Regexp.new(pat, Regexp::IGNORECASE | Regexp::MULTILINE)
Regexp.new("abc # Comment", Regexp::EXTENDED | true ? Regexp::IGNORECASE : Regexp::MULTILINE)

# Use regexes
/hay/ =~ 'haystack'
r{hay} =~ 'haystack'

/\s\u{6771 4eac 90fd}/.match("Go to 東京都")

# With flags
f1 = /pat/i
f2 = /pat/imxo
f3 = /pat/xmoi

# Inside a function
def my_log(msg)
  r = /abc/xm
end
