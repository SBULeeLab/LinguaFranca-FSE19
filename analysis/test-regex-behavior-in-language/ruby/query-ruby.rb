#!/usr/bin/env ruby
# Author: Jamie Davis <davisjam@vt.edu>
# Description: Test regex in Ruby

require 'json'

def my_log(msg)
  STDERR.puts msg + "\n"
end

def main()
  # Assume args are correct.
  file = ARGV[0]

  cont = File.read(file)
  query = JSON.parse(cont)

  # Query regexp.
  results = []
  begin
    query['inputs'].each { |input|
      my_log("matching: pattern /" + query['pattern'] + "/ input: length " + input.length.to_s)
      md = /#{query['pattern']}/.match(input) # Partial match
      query['validPattern'] = 1

      input = input
      matched = 0
      matchedString = ""
      captureGroups = []

      if md
        matched = 1
        matchedString = md[0]

        # Build captures, converting any unused groups to ""
        STDERR.puts "md: "
        STDERR.puts md.length
        STDERR.puts md
        STDERR.puts "captures: "
        STDERR.puts md.captures()
        STDERR.puts "names: "
        STDERR.puts md.names()
        captureGroups = []
        md.captures().each { |x|
          if x
            captureGroups.push(x)
          else
            captureGroups.push("")
          end
        }
      else
        matched = 0
      end

      results.push({
        "input" => input,
        "matched" => matched,
        "matchContents" => {
          "matchedString" => matchedString,
          "captureGroups" => captureGroups,
        },
      })
    }
  rescue => error
    STDERR.puts "Regex error: "
    STDERR.puts error
    query['validPattern'] = 0
  end
  query['results'] = results

  # Compose output.
  str = JSON.generate(query)
  STDOUT.puts str + "\n"

  # Whew.
  exit(0);
end

############

main()
