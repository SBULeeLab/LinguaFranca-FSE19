# Summary

Get the regexes from www.stackoverflow.com in an easy-to-work-with format.

Caveats:
1. This will take a reasonably long time (O(hours)) and involves a very large file download.
2. You need ~80GB available in the partition in which you have cloned this repository.

## Steps

Paths are relative to this (`stackoverflow/`) directory.

0. Install dependencies

```
pip install --user -r requirements.txt
```

1. Download the `Posts` table from the stackoverflow archive.

```
mkdir data
mkdir raw-data
wget --no-clobber --output-document=raw-data/stackoverflow.com-Posts.7z https://archive.org/download/stackexchange/stackoverflow.com-Posts.7z
```

2. Unzip

```
cd raw-data/
7z e stackoverflow.com-Posts.7z 
cd -
```

This results in a Very Large file called `raw-data/Posts.xml`.
It's about 70GB.

3. Extract posts related to regexes

This includes:
- The Question
- The accepted Answer (if any)
- Any other Answers

Extraction is done using a Python script to munch through `raw-data/Posts.xml`.

```
./find-regex-posts.py --all-posts-file raw-data/Posts.xml --out-file data/stackoverflow-regexPosts.json
```

4. Extract regexes from answers

```
./extract-regexes-from-posts.py --regex-posts data/stackoverflow-regexPosts.json --out-file data/stackoverflow-regexes.json
```

# Testing

For testing, you can create a small file of posts called `raw-data/PostsTest.xml` like this:

```
head -50000 raw-data/Posts.xml > raw-data/PostsTest.xml
tail -50000 raw-data/Posts.xml >> raw-data/PostsTest.xml
```

The extraction scripts will work on this file as well.
Just provide different arguments.
