package edu.virginiatech.leelabs.linguafranca;

import java.util.regex.Pattern;
import java.util.regex.Matcher;

// For testing: pass as a command line argument to RegexExtractor
class Test {
  public static void main(String args[]) {
    // Regexes are used in Java in one of two ways:
    // 1. String functions
    String s = "abc";
    s.matches("string: static regex 1/5: matches");
    s.split("string: static regex 2/5: split one arg");
    s.split("string: static regex 3/5: split two args", 1);
    s.replaceFirst("string: static regex 4/5: replaceFirst", "foo");
    s.replaceAll("string: static regex 5/5: replaceAll", "bar");
    s.matches(s); // DYNAMIC
    s.toUpperCase(); // Should not be emitted
    getString().matches("string: indirection 1/2");
    "".matches("string: indirection 2/2");

    // 2. Pattern class
    Pattern p1 = Pattern.compile("pattern: static regex 1/3: regex-compile");
    Pattern p2 = Pattern.compile("pattern: static regex 2/3: regex-compile-flags", 0);
    boolean match = Pattern.matches("pattern: static regex 3/3: regex-matches", "def");
    String quoted = Pattern.quote("not a regex");
    Pattern p_dynamic = Pattern.compile(new String("abc")); // DYNAMIC
    int flags = p_dynamic.flags(); // Should not be emitted
    java.util.regex.Pattern p3 = java.util.regex.Pattern.compile("pattern regex: fully qualified name");

    Pattern p;
    p = Pattern.compile("\\d");
    makeRegex("123");
  }

  private static String getString() {
    return "";
  }

  private static void makeRegex(String str) {
    str.matches("regex created using String function argument");
  }
}
