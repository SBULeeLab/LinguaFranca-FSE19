#!/usr/bin/env php
<?php
// Author: Jamie Davis <davisjam@vt.edu>
// Description: Evaluate a regex in PHP

function my_log($msg) {
  fwrite(STDERR, $msg . "\n");
}

// Return a string that can be used
// Returns NULL if nothing could be found
function patternAsPHPRegex($pat) {
  //http://php.net/manual/en/regexp.reference.delimiters.php
  $pairedDelimiters = [
    ['/', '/'],
    ['#', '#'],
    ['`', '`'],
    ['(', ')'],
    ['{', '}'],
    ['[', ']'],
    ['<', '>'],
  ];
  foreach($pairedDelimiters as $delim) {
    $first = $delim[0];
    $last = $delim[1];
    if (strpos($pat, $first) === FALSE && strpos($pat, $last) === FALSE) {
      return $first . $pat . $last;
    }
  }

  return NULL;
}

# returns: ($validPattern, $matched, $matchedString, $captureGroups)
function getResult($pattern, $input) {
  my_log('matching: Pattern ' . $pattern . ', input: len ' . strlen($input));

  $validPattern = 0;
  $matched = 0;
  $matchedString = "";
  $captureGroups = [];

  $matched_tmp = @preg_match($pattern, $input, $matches); // Partial match
  //var_dump($matches);
  // NB: (a?)abc|(d)  on "abc" --> (a?) is empty, but trailing unused groups like (d) are just dropped

  // capture exception, if any.
  // will return OK even if there's compilation problems.
  // PHP 7.4-dev emits a warning unless we @ to ignore it.
  $except = @array_flip(get_defined_constants(true)['pcre'])[preg_last_error()];

  // check for compilation
  $compilation_failed_message = 'preg_match(): Compilation failed:';
  $last_error = error_get_last();
  if(strpos($last_error['message'], $compilation_failed_message) === false) {
    $validPattern = 1;
  } else {
    my_log("Last error: " . $last_error['message']);
    $validPattern = 0;
  }

  // Compose output.
  $matched = $matched_tmp ? 1 : 0;
  if ($matched) {
    $matchedString = $matches[0];

    // Unset any capture groups keyed by name instead of number for consistency with other testers
    foreach ($matches as $key => $value) {
      if (!is_int($key)) {
        unset($matches[$key]);
      }
    }

    $captureGroups = array_slice($matches, 1);
  }

  return [$validPattern, $matched, $matchedString, $captureGroups];
}

function main() {
  // Assume args are correct, this is a horrible language.
  global $argc, $argv;
  $FH = fopen($argv[1], "r") or die("Unable to open file!");
  $cont = fread($FH, filesize($argv[1]));
  fclose($FH);

  $query = json_decode($cont);

  // Get a suitable regex string for PHP: /pattern/ etc.
  $phpPattern = patternAsPHPRegex($query->{'pattern'});

  if (is_null($phpPattern)) {
    $except = "INVALID_INPUT"; // Override compilation failed
    $query->{'validPattern'} = 0;
  } else {
    my_log('matching: pattern ' . $query->{'pattern'} . ' --> phpPattern ' . $phpPattern);

    $results = [];
    foreach($query->{'inputs'} as $input) {
      $res = getResult($phpPattern, $input);
      $validPattern = $res[0];
      $matched = $res[1];
      $matchedString = $res[2];
      $captureGroups = $res[3];

      if (!$validPattern) {
        $query->{'validPattern'} = 0;
        break;
      } else {
        $resultObj = array(
          "input" => $input,
          "matched" => $matched,
          "matchContents" => array(
            "matchedString" => $matchedString,
            "captureGroups" => $captureGroups,
          ),
        );
        array_push($results, $resultObj);
      }

    }
    $query->{'results'} = $results;
  }

  fwrite(STDOUT, json_encode($query) . "\n");

  // Whew.
  exit(0);
}

main();
?>
