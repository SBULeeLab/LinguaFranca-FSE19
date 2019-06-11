package VulnRegexDetector;

/* Taken from https://docs.oracle.com/javase/tutorial/essential/regex/test_harness.html */
import java.io.Console;
import java.util.List;
import java.util.ArrayList;
import java.util.regex.Pattern;
import java.util.regex.Matcher;

/* I/O. */
import com.google.gson.Gson;
import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import com.google.gson.JsonObject;
import com.google.gson.JsonArray;

import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.charset.Charset;
import java.io.IOException;

public class QueryJava {
  public static void main(String[] args)
    throws IOException
  {
    if (args.length == 1) {
   		// Trust input is valid.
		  String cont = readFile(args[0], Charset.defaultCharset());

			MyQuery query = new Gson().fromJson(cont, MyQuery.class);

      log(String.format("matching: pattern /%s/ against %d inputs", query.pattern, query.inputs.length));

      // Try to create regex
      Pattern p = null;
      boolean validPattern = false;
      try {
        p = Pattern.compile(query.pattern, 0);
        validPattern = true;
      } catch (Exception e) {
        log("Exception compiling pattern: " + e);
        validPattern = false;
      }

			List<MyMatchResult> matchResults = new ArrayList<MyMatchResult>();

			if (validPattern) {
				// Attempt matches
				for (int i = 0; i < query.inputs.length; i++) {
					int matched = 0;
					String matchedString = "";
					List<String> captureGroups = new ArrayList<String>();

					Matcher matcher = p.matcher(query.inputs[i]);
					matched = matcher.find() ? 1 : 0; // Partial match

					if (matched == 1) {
						matchedString = matcher.group();
						for (int j = 1; j <= matcher.groupCount(); j++) {
							String grp = matcher.group(j);
							// Strictly speaking, there is a distinction between "did not match" and "matched the empty string".
							if (grp == null) {
								captureGroups.add("");
							} else {
								captureGroups.add(grp);
							}
						}
					}
					MyMatchResult mmr = new MyMatchResult(query.inputs[i], matched, matchedString, captureGroups);
					matchResults.add(mmr);
				}
			}

			MyQueryResult mqr = new MyQueryResult(query.pattern, query.inputs, validPattern, matchResults);

      // Emit
      System.out.println(new Gson().toJson(mqr));
    } else {
      System.out.println("Usage: INVOCATION query.json");
      System.exit(-1);
    }
  }

 	/* https://stackoverflow.com/a/326440 */
	static String readFile(String path, Charset encoding)
		throws IOException 
	{
		byte[] encoded = Files.readAllBytes(Paths.get(path));
		return new String(encoded, encoding);
	}

	static void log(String msg) {
		System.err.println(msg);
	}
}

// Represents overall query response
class MyQuery {
	public String pattern;
	public String[] inputs;

	public MyQuery(String pattern, String[] inputs) {
		this.pattern = pattern;
		this.inputs = inputs;
	}
};

// Represents overall query response
class MyQueryResult {
	private String pattern;
	private String[] inputs;

	private boolean validPattern;
	private List<MyMatchResult> results;

	public MyQueryResult(String pattern, String[] inputs, boolean validPattern, List<MyMatchResult> results) {
		this.pattern = pattern;
		this.inputs = inputs;

		this.validPattern = validPattern;
		this.results = results;
	}
}

// Represents per-input match result
class MyMatchResult {
	private String input;
	private int matched; // 0 or 1
	private MyMatchContents matchContents;

	public MyMatchResult (String input, int matched, String matchedString, List<String> captureGroups) {
		this.input = input;
		this.matched = matched;
		this.matchContents = new MyMatchContents(matchedString, captureGroups);
	}
}

class MyMatchContents {
	private String matchedString;
	private List<String> captureGroups;

	public MyMatchContents (String matchedString, List<String> captureGroups) {
		this.matchedString = matchedString;
		this.captureGroups = captureGroups;
	}
}
