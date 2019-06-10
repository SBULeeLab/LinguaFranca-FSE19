#!/usr/bin/env php
<?php
// Extract regexes from PHP program.

// php-parser supports autoload, hooray
require __DIR__ . '/vendor/autoload.php';

// Import php-parser classes
use PhpParser\{ParserFactory, Error, NodeFinder};
use PhpParser\NodeDumper;

function my_log($msg) {
  fwrite(STDERR, $msg . "\n");
}

class Regex {
  public $function;
  public $raw;
  public $pattern;
  public $flags;

  public function __construct($function='', $raw='') {
    $this->function = $function;
    $this->raw = $raw;
    $this->_extractPatternAndFlags();
  }

  public function _extractPatternAndFlags() {
    if ($this->raw === 'UNSUPPORTED') {
      $this->pattern = 'UNSUPPORTED';
      $this->flags = 'UNSUPPORTED';
    } else if ($this->raw === 'DYNAMIC') {
      $this->pattern = 'DYNAMIC';
      $this->flags = 'DYNAMIC';
    } else {
      $beginDelim = $this->raw[0];

      # $endDelim is the same as $beginDelim, except for mirrors.
      $endDelim = $beginDelim;
      if ($beginDelim === '(') {
        $endDelim = ')';
      } else if ($beginDelim === '{') {
        $endDelim = '}';
      } else if ($beginDelim === '[') {
        $endDelim = ']';
      } else if ($beginDelim === '<') {
        $endDelim = '>';
      }

      # /pattern/flags
      # The outermost delimiter appearances cannot be escaped by definition.
      $beginDelimIx = strpos($this->raw, $beginDelim);
      $endDelimIx = strrpos($this->raw, $endDelim);
      $this->pattern = substr($this->raw, $beginDelimIx + 1, ($endDelimIx - $beginDelimIx) - 1);
      $this->flags = substr($this->raw, $endDelimIx + 1);
    }
  }

  public function toNDJSON() {
    $obj = array(
      "function" => $this->function,
      "raw"      => $this->raw,
      "pattern"  => $this->pattern,
      "flags"    => $this->flags,
    );
    return json_encode($obj);
  }
}

# @returns Regex[]
function findRegexes($ast) {
  # Find all function call nodes
  $nodeFinder = new NodeFinder;

  $functionCalls = $nodeFinder->findInstanceOf($ast, PhpParser\Node\Expr\FuncCall::class);
  my_log("Found " . sizeof($functionCalls) . " func calls");

  $regexes = array();
  foreach ($functionCalls as $call) {
    my_log("call: {$call->name}");
    $trimmedName = trim($call->name);
    if ($trimmedName === 'preg_filter'
     || $trimmedName === 'preg_grep'
     || $trimmedName === 'preg_match_all'
     || $trimmedName === 'preg_match'
     || $trimmedName === 'preg_replace_callback'
     || $trimmedName === 'preg_replace'
     || $trimmedName === 'preg_split'
     ) {
      my_log("  preg_X with pattern as first arg");
      $raw = '';
      if ($call->args[0]->value instanceof PhpParser\Node\Scalar\String_) {
        $raw = $call->args[0]->value->value;
      } else {
        $raw = "DYNAMIC";
      }
      array_push( $regexes, new Regex($trimmedName, $raw) );
    } elseif ($trimmedName === 'preg_replace_callback_array') {
      # TODO If they provide an anonymous array inline then we can get the regexes out.
      # It'll take some elbow grease though.
      array_push( $regexes, new Regex($trimmedName, 'UNSUPPORTED') );
    }
  }

  return $regexes;
}

function main() {
  global $argc, $argv;

  // Usage
  if ($argc != "2") {
    echo "Usage: " . $argv[0] . " file-to-analyze.php\n";
    exit(1);
  }

  # Read file
  $sourceFile = $argv[1];
  $FH = fopen($sourceFile, "r") or die("Unable to open file!");
  $phpCode = fread($FH, filesize($argv[1]));
  fclose($FH);

  # Parser -- Default to PHP7 but will fall back to PHP 5.
  $parser = (new ParserFactory)->create(ParserFactory::PREFER_PHP7);
  try {
    $ast = $parser->parse($phpCode);
  } catch (Error $error) {
    $sfwr = array(
      "fileName" => $sourceFile,
      "language" => "PHP",
      "couldParse" => 1,
    );
    fwrite(STDOUT, json_encode($sfwr) . "\n");
    exit(1);
  }

  # Parsing succeeded.

  $dumper = new NodeDumper;
  #my_log($dumper->dump($ast));

  # Look for regexes.
  $regexes = findRegexes($ast);

  # Emit as a SimpleFileWithRegexes in NDJSON.
  $sfwr = array(
    "fileName" => $sourceFile,
    "language" => "PHP",
    "couldParse" => 1,
    "regexes" => array()
  );
  foreach ($regexes as $regex) {
    my_log('Appending regex: ' . $regex->toNDJSON());
    $simpleRegexObj = array(
      "pattern" => $regex->{'pattern'},
      "flags"   => $regex->{'flags'}
    );
    array_push($sfwr['regexes'], $simpleRegexObj);
  }

  fwrite(STDOUT, json_encode($sfwr) . "\n");
}

///////////////////

main();

?>
