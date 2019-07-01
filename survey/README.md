# Summary

This directory contains the survey instrument we used.

The instrument was delivered as a Qualtrics survey.
We exported it into PDF format for ease of reference.

Notes:
1. Space did not permit us to report on all survey results.
2. We did not include the raw survey results out of privacy concerns. Figures 1-3 aggregate responses for the survey questions we analyzed in this paper.

## Details about the filter used in our survey

Section 4 discusses a filter to combat spoofing. Limited space prevented us from elaborating there.

Any time you deploy a survey to untrusted parties (i.e. the Internet), you must take precautions against fraudulent responses. Indeed, on the third day of our deployment to HackerNews, we began receiving responses every few minutes for a span of several hours. These responses typically took only a few seconds to complete and used distinct gmail addresses that appeared to be automatically generated.

We applied an automated filter to find the survey responses that appeared to be completed in good faith. This filter was only applied to responses from the Internet, since we assumed that our professional connections would not give us fake responses in hopes of a minor financial reward ($5).

The filter works as follows: * We rejected responses that completed the survey in under 5 minutes. This time was chosen by looking at the response time for responses from our professional networks. * We rejected responses that did not put "meaningful" text in at least one of the free response areas. By "meaningful" we mean the text was not "N/A" and was not copy/pasted from other parts of the survey (the bot that filled out our survey did this). * We rejected responses that were not internally consistent. In particular, respondents could not list more years of experience using regexes in a programming language than they indicated using the language itself.
