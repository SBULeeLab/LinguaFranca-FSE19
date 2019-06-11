// Author: Jamie Davis <davisjam@vt.edu>
// Description: Test regex in Rust
//   NB This should always take linear-time, unless there are subtleties in the Rust docs.

// command-line args
use std::env;

// File I/O
use std::fs::File;
use std::io::prelude::*;

// JSON
extern crate serde;
use serde::{Deserialize, Serialize};

#[macro_use]
extern crate serde_json;
use serde_json::{Value, Error, Result};

#[macro_use]
extern crate serde_derive;

// Regex
extern crate regex;
use regex::Regex;

#[derive(Serialize, Deserialize)]
struct Query {
	pattern: String,
	inputs: Vec<String>,
}

#[derive(Serialize, Deserialize)]
struct MatchContents {
  matchedString: String,
  captureGroups: Vec<String>,
}

#[derive(Serialize, Deserialize)]
struct MatchResult {
  input: String,
  matched: bool,
  matchContents: MatchContents,
}

#[derive(Serialize, Deserialize)]
struct QueryResult {
  pattern: String,
  inputs: Vec<String>,
  validPattern: bool,
  results: Vec<MatchResult>,
}

fn main() {
	// Get file from command-line args
	let args: Vec<String> = env::args().collect();
	let filename = &args[1];
	eprintln!("File: {}", filename);

	// Read file contents into string
	let mut f = File::open(filename).expect("file not found");

	let mut contents = String::new();
	f.read_to_string(&mut contents)
			.expect("something went wrong reading the file");

	eprintln!("File contents:\n{}", contents);

	// Parse as JSON
	let query: Query = serde_json::from_str(&contents).unwrap();
  eprintln!("The pattern is: {}", query.pattern);

  // Prep a QueryResult
	let mut queryResult: QueryResult = QueryResult{
		pattern: query.pattern.clone(),
		inputs: query.inputs.clone(),
    validPattern: false,
		results: vec![],
	};

  match Regex::new(&query.pattern) {
		Ok(re) => {
			queryResult.validPattern = true;

			for i in 0..query.inputs.len() {
				let input = query.inputs.get(i).unwrap();
				eprintln!("Input: {}", input);

				let mut matched = false;
				let mut matchedString = "".to_string();
				let mut captureGroups: Vec<String> = Vec::new();

				// Partial-match semantics
				match re.captures(&input) {
					Some(caps) => {
						matched = true;

						matchedString = caps.get(0).unwrap().as_str().to_string();
						captureGroups = Vec::new();
						for i in 1..caps.len() {
							match caps.get(i) {
								Some(m) => {
									captureGroups.push(m.as_str().to_string());
								},
								None => {
									captureGroups.push("".to_string()); // Interpret unused capture group as ""
								}
							}
						}
					},
					None => {
						matched = false;
					}
				}

				let mr: MatchResult = MatchResult{
					input: input.to_string(),
					matched: matched,
					matchContents: MatchContents{
						matchedString: matchedString,
						captureGroups: captureGroups,
					},
				};

				queryResult.results.push(mr);
			}
		},
		Err(error) => {
			// Could not build.
			queryResult.validPattern = false;
		}
	};

	println!("{}", serde_json::to_string(&queryResult).unwrap());
}
