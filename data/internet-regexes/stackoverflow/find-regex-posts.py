#!/usr/bin/env python3
# Description:
#   Extracts all posts associated with those questions that are tagged 'regex'.
#   Writes them in JSON format to --out-file, one per line.
# Credits:
#   https://www.ibm.com/developerworks/xml/library/x-hiperfparse/
#   For advice on parsing large XML files without ENOMEM.

# Import our lib
import os
import sys
sys.path.append('{}/lib'.format(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT']))
import libLF

# Private lib
from intermediateRegexPost import IntermediateRegexPost

from functools import partial
from lxml import etree
import json
import argparse
import re

def handleEventForGetqid2aid(qid2aid, tagsRegex, elem):
  if elem.tag == 'row':
    isQuestion = (elem.get('PostTypeId') == '1')
    if isQuestion:
      isRegex = (re.search(tagsRegex, elem.get('Tags')))
      if isRegex:
        # Get the answer Id.
        try:
          answerId = elem.get('AcceptedAnswerId')
        except E:
          answerId = -1
        if not answerId:
          answerId = -1

        qid2aid[elem.get('Id')] = answerId
        return True
  return False

# Returns: questionId2AnswerId: qid2aid[id] = answerId
# An answerId of -1 means it has no accepted answer.
#
# We return a minimally-sized dict: 2 id's (strings) per entry.
# Estimated cost: 200K * 32 bytes = 6.4MB
def getRegexQuestionId2Answer(inFile):
  tagsRegex = re.compile('<regex>')
  qid2aid = {}

  # Build the qid2aid table.
  context = etree.iterparse(inFile, events=('end',))
  fast_iter(context, partial(handleEventForGetqid2aid, qid2aid, tagsRegex))
  return qid2aid

# Handler for fast_iter.
# If the elem is a row tag for a regex Q or A: write to outStream and return True
# Else return False.
def handleEventForPrintRegexPosts(outStream, qid2aid, elem):
  if elem.tag == 'row':
    isRegexQuestion = (elem.get('Id') in qid2aid)
    isRegexAnswer = (elem.get('PostTypeId') == '2' and elem.get('ParentId') in qid2aid)

    if isRegexQuestion or isRegexAnswer:
      post = IntermediateRegexPost()
      isQuestion = False
      isAcceptedAnswer = False
      parentId = None

      if isRegexQuestion:
        isQuestion = True
      elif isRegexAnswer:
        isQuestion = False
        isAcceptedAnswer = (qid2aid[elem.get('ParentId')] == elem.get('Id'))
        parentId = elem.get('ParentId')

      post.initFromRaw(_id=elem.get('Id'), _parentId=parentId, _body=elem.get('Body'), _isQuestion=isQuestion, _isAcceptedAnswer=isAcceptedAnswer)
      outStream.write(post.toNDJSON() + '\n')
      return True
    else:
      return False
  return False

# Print the RegexPost's we encounter to outStream in JSON format, one per line.
#
# We stream these out rather than returning a structure
# because the inStream is expected to be O(GB) and we have limited memory.
def printRegexPosts(inStream, qid2aid, outStream):
  i = 0
  context = etree.iterparse(inStream, events=('end',))
  return fast_iter(context, partial(handleEventForPrintRegexPosts, outStream, qid2aid))

def fast_iter(context, func):
  i = 0
  nFunc = 0
  for event, elem in context:
    if i and i % 10000 == 0:
      libLF.log('fast_iter: i {}'.format(i))

    if func(elem):
      nFunc = nFunc + 1
      if nFunc and nFunc % 10000 == 0:
        libLF.log('fast_iter: special {}'.format(nFunc))
    
    i += 1

    # Trim the XML tree. We won't need this entry again.
    elem.clear()
    while elem.getprevious() is not None:
      del elem.getparent()[0]
  del context
  return nFunc

def main(postFile, outFile):
  with open(outFile, 'w') as outStream:
    # Get questions tagged "regex" from postFile
    libLF.log('Parsing postFile {}'.format(postFile))
    qid2aid = getRegexQuestionId2Answer(postFile)
    libLF.log('Got {} regex questions'.format(len(qid2aid.keys())))

    # Stream all posts associated with those questions
    # (including each question post) to outFile
    libLF.log('Streaming posts to {}'.format(outFile))
    nPosts = printRegexPosts(postFile, qid2aid, outStream)
    libLF.log('Streamed {} posts'.format(nPosts))

###############################################

# Parse args
parser = argparse.ArgumentParser(description='Extract regex-related posts from StackOverflow Posts.xml dump')
parser.add_argument('--all-posts-file', '-f', help='Path to Posts.XML', required=True)
parser.add_argument('--out-file', '-o', help='Where to write JSON results?', required=True)

args = parser.parse_args()

# Here we go!
main(args.all_posts_file, args.out_file)
