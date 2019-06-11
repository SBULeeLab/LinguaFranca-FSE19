package edu.virginiatech.leelabs.linguafranca;

import com.github.javaparser.JavaParser;
import com.github.javaparser.ParseException;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.expr.MethodCallExpr;
import com.github.javaparser.ast.visitor.VoidVisitorAdapter;
import com.github.javaparser.ast.expr.Expression;
import com.github.javaparser.ast.expr.NameExpr;
import com.github.javaparser.ast.expr.StringLiteralExpr;
import com.github.javaparser.ast.NodeList;

import com.github.javaparser.symbolsolver.model.resolution.TypeSolver;
import com.github.javaparser.symbolsolver.*;
import com.github.javaparser.symbolsolver.resolution.typesolvers.*;
import com.github.javaparser.resolution.declarations.ResolvedValueDeclaration;
import com.github.javaparser.resolution.declarations.ResolvedMethodDeclaration;
import com.github.javaparser.resolution.types.ResolvedType;
import com.github.javaparser.resolution.UnsolvedSymbolException;

import com.google.common.base.Strings;

import java.io.File;
import java.io.IOException;

import java.util.regex.Pattern;
import java.util.regex.Matcher;

import java.util.Optional;
import java.util.List;
import java.util.ArrayList;

import com.google.gson.Gson; 

public class RegexExtractor {

  private static String getTypeName(Expression expr) {
    return expr.getClass().getName();
  }

  /**
   * @returns: String or null
   */
  private static String getFirstArgIfLiteralString(NodeList<Expression> methodCallArgs) {
    Expression arg = methodCallArgs.get(0);
    if (arg.isStringLiteralExpr()) {
      StringLiteralExpr patternStr = arg.asStringLiteralExpr();
      return patternStr.getValue();
    } else {
      System.err.println("arg0 className: <" + arg.getClass().getName() + ">");
      return null;
    }
  }

  private static boolean isScopedMethodCall(MethodCallExpr expr) {
    Optional<Expression> scopeName = expr.getScope();
    return scopeName.isPresent();
  }

  private static boolean isStringType(NameExpr nameExpr) {
    try {
      System.err.println(" ne: Resolving");
      ResolvedValueDeclaration rvd = nameExpr.resolve();
      System.err.println(" ne: Getting type");
      ResolvedType type = rvd.getType();
      if (type.describe().equals("java.lang.String")) {
        return true;
      }
    } catch (Exception e) {
      System.err.println(" >>> Exception: Could not resolve NameExpr");
      return false;
    }
    return false;
  }

  private static boolean isStringType(MethodCallExpr mcExpr) {
    try {
      System.err.println(" mce: Resolving");
      ResolvedMethodDeclaration rmd = mcExpr.resolve();
      System.err.println(" mce: Getting type");
      ResolvedType type = rmd.getReturnType();
      if (type.describe().equals("java.lang.String")) {
        return true;
      }
    } catch (Exception e) {
      System.err.println(" >>> Exception: Could not resolve MethodCallExpr");
      return false;
    }
    return false;
  }

  private static boolean isMethodCallInStringScope(MethodCallExpr expr) {
    if (isScopedMethodCall(expr)) {
      System.err.println("  scope: " + expr.getScope());
      System.err.println("  scope Expression type: " + expr.getScope().get().getClass().getName());
      Expression scope = expr.getScope().get();
      if (scope.isStringLiteralExpr()) {
        // If the scope is a string literal, then we are in String scope by definition
        System.err.println("Scope is StringLiteralExpr");
        return true;
      } else if (scope.isNameExpr()) {
        System.err.println("Scope is NameExpr");
        NameExpr ne_scope = scope.asNameExpr();
        return isStringType(ne_scope);
      } else if (scope.isMethodCallExpr()) {
        MethodCallExpr mce_scope = scope.asMethodCallExpr();
        return isStringType(mce_scope);
      } else {
        System.err.println("Unknown scope type");
        return false;
      }
    }
    //System.err.println("  scope ResolvedType: " + expr.getScope().calculateResolvedType().describe());
    System.err.println("  name: " + expr.getName());
    return false;
  }

  private static boolean isMethodCallInPatternScope(MethodCallExpr expr) {
    // Pattern.compile and Pattern.matches are static, so the scope is easy to identify.
    // This assumes, of course, that the user never names a variable 'Pattern' or defines
    // their own class with this name. Probably a safe assumption?
    if (isScopedMethodCall(expr)) {
      String scopeName = expr.getScope().get().toString();
      System.err.println(" scopeName: " + scopeName);
      return scopeName.equals("Pattern") || scopeName.equals("java.util.regex.Pattern");
    } 
    return false;
  }

  private static boolean isCallTo(MethodCallExpr expr, String method) {
    return expr.getName().asString().equals(method);
  }

  private static boolean isCallToMatches(MethodCallExpr expr) {
    return expr.getName().asString().equals("matches");
  }

  private static List<MyRegex> extractRegexes(File file) {
    System.err.println("File: " + file);
    List<MyRegex> regexList = new ArrayList<MyRegex>();
    System.err.println(Strings.repeat("=", (int) file.length()));

    TypeSolver reflectionTypeSolver = new ReflectionTypeSolver();
    //TypeSolver javaParserTypeSolver = new JavaParserTypeSolver(new File("/home/jamie/Desktop/EcosystemRegexps/ecosystems/per-module/extract-regexps/static/java/regex-extractor")); // TODO Accept root of file tree
    reflectionTypeSolver.setParent(reflectionTypeSolver);
    CombinedTypeSolver combinedSolver = new CombinedTypeSolver();
    combinedSolver.add(reflectionTypeSolver);
    //combinedSolver.add(javaParserTypeSolver);

    JavaSymbolSolver symbolSolver = new JavaSymbolSolver(combinedSolver);
    JavaParser.getStaticConfiguration().setSymbolResolver(symbolSolver);

    try {
      CompilationUnit compilationUnit = JavaParser.parse(file);
       new VoidVisitorAdapter<List<MyRegex>>() {
         @Override
         public void visit(MethodCallExpr expr, List<MyRegex> regexList) {
           super.visit(expr, regexList);

           System.err.println("MethodCallExpr: " + expr);
           boolean callDefinesARegex = false;
           String pattern = null;
           if (isMethodCallInStringScope(expr)) {
             System.err.println("  Method call in String scope");
             if (isCallTo(expr, "matches")
                 || isCallTo(expr, "split")
                 || isCallTo(expr, "replaceFirst")
                 || isCallTo(expr, "replaceAll"))
             {
               System.err.println("  String.{matches | split | replaceFirst | replaceAll}");
               callDefinesARegex = true;
               // Each of these has a regex as the first arg
               NodeList<Expression> args = expr.getArguments();
               if (args.size() >= 1) {
                 pattern = getFirstArgIfLiteralString(args);
               }
             }
           }
           else if (isMethodCallInPatternScope(expr)) {
             System.err.println("  Method call in Pattern scope");
             if (isCallTo(expr, "compile")) {
               System.err.println("  Pattern.compile");
               NodeList<Expression> args = expr.getArguments();
               if (args.size() == 1 || args.size() == 2) {
                 // Pattern.compile: Pattern.compile(String pattern[, int flags])
                 callDefinesARegex = true;
                 System.err.println(" Pattern.compile(pattern[, flags])");
                 pattern = getFirstArgIfLiteralString(args);
                 // TODO We could retrieve flags if we wanted, for args.size() > 1.
               }
             } else if (isCallToMatches(expr)) {
               System.err.println("  Pattern.matches");
               NodeList<Expression> args = expr.getArguments();
               if (args.size() == 2) {
                // Pattern.matches(String pattern, String input)
                callDefinesARegex = true;
                pattern = getFirstArgIfLiteralString(args);
               }
             }
           }
           // If call defines a regex but arg is not a literal string, it is DYNAMIC
           if (callDefinesARegex && pattern == null) {
             System.err.println("Call defines a regex, but the regex is not a string literal");
             pattern = "DYNAMIC";
           }

           // Values for pattern at this point:
           //   null            A method call that does not create a regex
           //   DYNAMIC         A method call that creates a regex, but with a non-StringLiteral expression
           //   anything else   A method call that creates a regex with a static string
           if (pattern != null) {
             pattern = unescapePattern(pattern);
             System.err.println(" << Regex declaration: regex /" + pattern + "/");
             regexList.add(new MyRegex(pattern, "UNKNOWN"));
           }
         }
       }.visit(compilationUnit, regexList);
      System.err.println(); // empty line
      return regexList;
    } catch (IOException e) {
      new RuntimeException(e);
    }
    return null;
  }

	/**
	 * Convert pattern to a "raw string".
	 * This matches how most other languages declare regexes.
	 */
  public static String unescapePattern(String pattern) {
		// Java really needs raw strings! This replaces '\\' with '\'
		String replacement = pattern.replaceAll(Matcher.quoteReplacement("\\\\"), Matcher.quoteReplacement("\\"));
		System.err.println("unescapePattern: /" + pattern + "/ --> /" + replacement + "/");
    return replacement;
  }

  public static void main(String[] args) {
    if (args.length == 1) {
      String fileName = args[0];
      File fileToAnalyze = new File(fileName);
      Output_SimpleFileWithRegexes out = null;
      try {
        List<MyRegex> regexes = extractRegexes(fileToAnalyze);
        out =
          new Output_SimpleFileWithRegexes(fileName, "java", true, regexes);
        System.err.println("Got " + regexes.size() + " regexes");
      } catch (Exception e) {
        System.err.println("main: Exception: " + e);
        e.printStackTrace(System.err);
        out =
          new Output_SimpleFileWithRegexes(fileName, "java", false, null);
      }
      Gson gson = new Gson();
      System.out.println(gson.toJson(out));
    } else {
      System.out.println("Usage: INVOCATION file-to-analyze.java");
      System.exit(-1);
    }
  }
}

// Name for what the visitor extracts
class MyRegex {
  String pattern;
  String flags;
  public MyRegex(String pattern, String flags) {
    this.pattern = pattern;
    this.flags = flags;
  }
}

// For output
class Output_SimpleFileWithRegexes {
  private String fileName;
  private String language;
  private boolean couldParse;
  private List<MyRegex> regexes;
  public Output_SimpleFileWithRegexes(String fileName, String lang, boolean couldParse, List<MyRegex> regexes) {
    this.fileName = fileName;
    this.language = lang;
    this.couldParse = couldParse;
    this.regexes = regexes;
  }
}
