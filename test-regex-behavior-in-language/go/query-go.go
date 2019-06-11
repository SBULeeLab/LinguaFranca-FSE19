// Author: Jamie Davis <davisjam@vt.edu>
// Description: Test a <regex, input> pair in Go

package main

///////////
// IMPORTS
///////////

import (
  "fmt"
  "os"
  "io/ioutil"
  "encoding/json"
  "regexp"
)

type Query struct {
  Pattern string     `json:"pattern"`
  Inputs []string    `json:"inputs"`
}

type MatchContents struct {
  MatchedString string    `json:"matchedString"`
  CaptureGroups []string  `json:"captureGroups"`
}

type MatchResult struct {
  Input string            `json:"input"`
  Matched bool            `json:"matched"`
  MC MatchContents        `json:"matchContents"`
}

type QueryResult struct {
  // Duplicate the Query
  Pattern string         `json:"pattern"`
  Inputs []string        `json:"inputs"`
  // Additional fields
  ValidGoPattern bool    `json:"validPattern"`
  MRs []MatchResult    `json:"results"`
}

///////////
// FUNCTIONS
///////////

func myLog(str string) {
  fmt.Fprintln(os.Stderr, str)
}

func check(e error) {
  if e != nil {
    panic(e)
  }
}

///////////
// main
///////////

func main() {
  if len(os.Args) <= 1 {
    fmt.Printf("Usage: query-go query.json\n")
    os.Exit(1)
  }

  // Load file contents
  queryFile := os.Args[1]
  myLog("queryFile " + queryFile)
  fd, err := os.Open(queryFile)
  check(err)
  byteValue, _ := ioutil.ReadAll(fd)

  // Load into a Query
  var query Query
  json.Unmarshal(byteValue, &query)
  myLog("Query: pattern /" + query.Pattern + "/")

  // Evaluate the Query as a QueryResult
  var queryResult QueryResult
  queryResult.Pattern = query.Pattern
  queryResult.Inputs = query.Inputs
  queryResult.MRs = make([]MatchResult, 0)

  re, err := regexp.Compile(query.Pattern)
  if err == nil {
    queryResult.ValidGoPattern = true

    for _, input := range query.Inputs {
      var matchResult MatchResult
      matchResult.Input = input

      matches := re.FindSubmatch([]byte(input)) // Partial match
      if matches != nil {
        //fmt.Println(matches)
        matchResult.Matched = true
        matchResult.MC.MatchedString = string(matches[0])

        // Build up the capture groups, from []byte to string
        matchResult.MC.CaptureGroups = make([]string, 0)
        for _, byteString := range matches[1:] {
          matchResult.MC.CaptureGroups = append(matchResult.MC.CaptureGroups, string(byteString))
        }
      } else {
        matchResult.Matched = false
        matchResult.MC.MatchedString = ""
        matchResult.MC.CaptureGroups = make([]string, 0)
      }

      queryResult.MRs = append(queryResult.MRs, matchResult)
    }
  } else {
    queryResult.ValidGoPattern = false
  }

  // Emit
  str, _ := json.Marshal(queryResult)
  fmt.Println(string(str))
}
