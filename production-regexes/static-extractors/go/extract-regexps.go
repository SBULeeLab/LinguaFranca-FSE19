// Description: Extract regexps from a Go program
// Prints a JSON object with keys: fileName regexes[]
//   fileName is the path provided
//   regexes is an array of objects, each with keys: pattern flags
//   pattern and flags are each either a string or 'DYNAMIC-{PATTERN|FLAGS}'

package main

///////////
// IMPORTS
///////////

import (
  "fmt"
  "os"
  "encoding/json"
  "go/ast"
  "go/parser"
  "go/token"
)

type RegexUsage struct {
  Pattern string    `json:"pattern"`
  Flags string      `json:"flags"`
}

type AllRegexes struct {
  Language string      `json:"language"`
  Filename string      `json:"fileName"`
  CouldParse bool      `json:"couldParse"`
  Regexes []RegexUsage `json:"regexes"`
}

///////////
// GLOBALS
///////////

// This is set if we see an Import statement that imports "regexp".
// If so, subsequent references to regexp are really regexps.
// Otherwise they are to something else.
var FOUND_REGEXP_IMPORT bool = false

// Update while walking the AST
var allRegexes AllRegexes

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
func importsRegexp(node *ast.ImportSpec) bool {
  if node.Path.Kind == token.STRING && node.Path.Value == "\"regexp\"" {
    myLog("Found regexp import")
    return true
  }
  return false
}

func exprIsIdentNamedRegexp(expr ast.Expr) bool {
  switch identExpr := expr.(type) {
	case *ast.Ident:
	  myLog("expr: identExpr named regexp")
	  return identExpr.Name == "regexp"
  }
  myLog("expr: not an identExpr named regexp")
  return false
}

func nameIndicatesRegex(name string) bool {
  return name == "Match" ||
         name == "MatchReader" ||
         name == "MatchString" ||
         name == "Compile" ||
         name == "CompilePOSIX" ||
         name == "MustCompile" ||
         name == "MustCompilePOSIX"
}

func getFirstArgIfString(args []ast.Expr) (pattern string, ok bool) {
  ok = false
  if len(args) >= 1 {
    switch basicLit := args[0].(type) {
	case *ast.BasicLit:
		if basicLit.Kind == token.STRING {
			ok = true
			str := basicLit.Value
			myLog("Found string: <" + str + ">")
			// Peel off the wrapping quote chars
            pattern = str[1:len(str)-1]
		}
	}
  }
  return pattern, ok
}

func tryToGetRegexUsageFromCallExpr(node *ast.CallExpr) (regexUsage RegexUsage, ok bool) {
  ok = false
  regexUsage.Pattern = ""
  regexUsage.Flags = ""
  if FOUND_REGEXP_IMPORT {
    switch se := node.Fun.(type) {
      case *ast.SelectorExpr:
        if exprIsIdentNamedRegexp(se.X) && nameIndicatesRegex(se.Sel.Name) {
		  myLog("Looks regex-y!")
		  ok = true
          // The regex is always the first arg
		  pattern, wasLiteralString := getFirstArgIfString(node.Args)
		  if wasLiteralString {
            myLog("Literal")
			regexUsage.Pattern = pattern
			regexUsage.Flags = "UNKNOWN"
		  } else {
            myLog("Dynamic")
			regexUsage.Pattern = "DYNAMIC"
			regexUsage.Flags = "UNKNOWN"
		  }
		}
    }
  }

  return regexUsage, ok // I want to return nil but don't know how, oh well
}

///////////
// main
///////////

func main() {
  if len(os.Args) <= 1 {
	fmt.Printf("Usage: extract-regexps source.go\n")
	os.Exit(1)
  }

  // Load file contents
  sourceFileToParse := os.Args[1]
  myLog("Extracting regexps from " + sourceFileToParse)

  // Initialize allRegexes
  allRegexes.Language = "go"
  allRegexes.Filename = sourceFileToParse
  // Empty array, not nil, for consistency with other extractors
  allRegexes.Regexes = make([]RegexUsage, 0)

  // Create the AST by parsing src.
  fset := token.NewFileSet() // positions are relative to fset
  f, err := parser.ParseFile(fset, sourceFileToParse, nil, 0)
  if err == nil {
	allRegexes.CouldParse = true
    // This is really handy for figuring out types and members!
    //myLog("Pretty-printing the AST")
    //ast.Print(fset, f)

    myLog("Inspecting the AST")
    // Inspect the AST and print all identifiers and literals.
    ast.Inspect(f, func(n ast.Node) bool {
      switch x := n.(type) { // Type switch! https://tour.golang.org/methods/16
	    case *ast.ImportSpec:
		  if importsRegexp(x) {
            FOUND_REGEXP_IMPORT = true
		  }
	    case *ast.CallExpr:
		  regexUsage, ok := tryToGetRegexUsageFromCallExpr(x)
		  if ok {
		    myLog("Got a regex")
            allRegexes.Regexes = append(allRegexes.Regexes, regexUsage)
		  }
	}

      // Keep inspecting -- proceeds until the entire tree is traversed
      return true
    })
  } else {
	allRegexes.CouldParse = false
  }

  // Emit
  str, _ := json.Marshal(allRegexes)
  fmt.Println(string(str))
}
