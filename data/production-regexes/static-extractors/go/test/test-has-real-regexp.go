package test

import (
  "regexp"
)

func main() {
  var str string
  // In Golang, regexes are created in two ways.
  // 1. Creating a Regexp object
  re1 := regexp.Compile("Compile")
  re2 := regexp.CompilePOSIX("CompilePOSIX")
  re3 := regexp.MustCompile("MustCompile")
  re4 := regexp.MustCompilePOSIX("MustCompilePOSIX")
  re5 := regexp.MustCompilePOSIX(str) // DYNAMIC

  // 2. Using a "static" regexp method to perform a string test
  matched1, err1 := regexp.Match("Match", "[]byte")
  matched2, err2 := regexp.MatchReader("MatchReader", "RuneReader")
  matched3, err3 := regexp.MatchString("MatchString", "string")
  matched3, err3 := regexp.MatchString(str, "string") // DYNAMIC
}
