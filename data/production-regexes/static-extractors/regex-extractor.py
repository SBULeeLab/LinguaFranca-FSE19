#!/usr/bin/env python3
# Extract regexes from a tarball of a GitHubProject.
# Only extracts regexes from source code in the "target language"
# as identified by the registry from which the GHP was referenced.

# TODO Consistency on language capitalization: Ruby vs rust vs Perl vs javascript vs etc.

# Import libLF
import os
import sys
import re
sys.path.append('{}/lib'.format(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT']))
import libLF
import argparse
import tarfile
import re
import subprocess
import shutil

#######
# Globals
#######

CLEAN_TMP_DIR = True # TODO

registryToExtensionLists = {
    'crates.io': [r'\.rs', r'\.rlib'],
    'cpan': [r'\.pl', r'\.pm'],
    'npm': [r'\.js', r'\.ts'],
    'pypi': [r'\.py'],
    'maven': [r'\.java'],
    'rubygems': [r'\.rb'],
    'packagist': [r'\.php'],
    'nuget': [r'\.cs'],
    'godoc': [r'\.go']
}

extensionToLang = {
    r'\.rs': 'rust',
    r'\.rlib': 'rust',
    r'\.pl': 'Perl',
    r'\.pm': 'Perl',
    r'\.js': 'javascript',
    r'\.ts': 'typescript',
    r'\.py': 'python',
    r'\.java': 'Java',
    r'\.rb': 'Ruby',
    r'\.php': 'PHP',
    r'\.cs': 'c#',
    r'\.go': 'go'
}

registryToFileOutputRE = {
    'cpan': ['Perl'],
    'npm': [r'Node\.js', 'javascript'], # `file` does not support typescript
    'pypi': ['python'],
    'rubygems': ['Ruby'],
    'packagist': ['PHP'],
    # `file` does not correctly identify Java, Golang, etc. files.
    # `cloc` does but is much slower.
    # I think it unlikely that people would name source code
    # in a *compiled* language with a non-traditional suffix.
    # The use of `file` is really more for executables, which might have no suffix,
    # but these are only source code when they are in an interpreted language.
    'nuget': [], # `file` does not support C#
    'godoc': [], # `file` does not support Go
    'crates.io': [], # `file` does not support rust
    'maven': []
}

fileOutputREToLang = {
    'Perl': 'Perl',
    r'Node\.js' : 'javascript',
    'javascript': 'javascript', 
    'python': 'python',
    'Ruby': 'Ruby',
    'PHP': 'PHP'
    # No compiled languages here
}

registryToLangs = {
    'crates.io': ['rust'],  
    'cpan': ['Perl'],
    'npm': ['javascript', 'typescript'], 
    'pypi': ['python'],
    'maven': ['Java'],
    'rubygems': ['Ruby'],
    'packagist': ['PHP'],
    'nuget': ['c#'], 
    'godoc': ['go'] 
}

extractorDir = os.path.join(os.environ['ECOSYSTEM_REGEXP_PROJECT_ROOT'], 'bin')
langToExtractorPath = {
    'rust': os.path.join(extractorDir,'extract-rust-regexes.py'),
    'Perl': os.path.join(extractorDir, 'extract-perl-regexps.pl'),
    'javascript': os.path.join(extractorDir, 'extract-js-regexps.js'),
    'typescript': os.path.join(extractorDir, 'extract-ts-regexes.py'), 
    'python': os.path.join(extractorDir, 'extract-python-regexes-wrapper.pl'),
    'java': os.path.join(extractorDir, 'extract-java-regexps.jar'),
    'Ruby': os.path.join(extractorDir, 'extract-ruby-regexps.rb'),
    'PHP': os.path.join(extractorDir, 'extract-php-regexps.php'),
    'go': os.path.join(extractorDir, 'extract-go-regexps'),
    'c#': '', 
}

def cleanUp(tmpDir):
    if CLEAN_TMP_DIR:
        libLF.log('cleanUp: Wiping {}'.format(tmpDir))
        try:
            if os.path.isdir(tmpDir): # Make sure we don't touch tarballs
                shutil.rmtree(tmpDir)
        except:
            pass

def runExtractor(sourceFile, extractor, registry):
    libLF.log('Extracting regexes from {} using {}'.format(sourceFile['name'], extractor))

    # Any special invocation recipe?
    if extractor.endswith(".jar"):
        invocationPrefix = "java -jar"
    else:
        invocationPrefix = ""

    try:
        # Extract
        cmd = "{} '{}' '{}' 2>/dev/null".format(invocationPrefix, extractor, sourceFile['name'])
        out = libLF.chkcmd(cmd)
        try:
            sfwr = libLF.SimpleFileWithRegexes()
            sfwr.initFromNDJSON(out)
            if not sfwr.couldParse:
              libLF.log('Could not parse: {}'.format(sourceFile['name']))

            # TODO ruList = libLF.sfwrToRegexUsageList(sfwr)
            ruList = []
            for regex in sfwr.regexes:
                ru = libLF.RegexUsage()
                basePath = os.path.basename(sourceFile['name'])
                ru.initFromRaw(regex['pattern'], regex['flags'], None, None, sourceFile['name'], basePath)
                ruList.append(ru)
            libLF.log('Got {} regexes from {}'.format(len(ruList), sourceFile['name']))
            return ruList
        except KeyboardInterrupt:
            raise
        except Exception as err:
            libLF.log('Error converting output from SFWR to RU: {}\n  {}'.format(out, err))
    except KeyboardInterrupt:
        raise 
    except BaseException as err:
        libLF.log('Error extracting regexes from {} using {}: {}'.format(sourceFile['name'], extractor, err))

def extractRegexes(registry, lang, sourceFile):
    """Extract regexes from this sourceFile."""
    output = runExtractor(sourceFile, langToExtractorPath[lang], registry)
    return output

def checkRegistryDeps(registry):
    dependenciesToCheck = []
    for l in registryToLangs[registry]:
        dependenciesToCheck.append(langToExtractorPath[l.lower()])
    libLF.checkShellDependencies(dependenciesToCheck, mustBeExecutable=False)

def unpackTarball(tarball):
   tmpDir = os.path.join(os.sep, 'tmp', 'regex-extractor', str(os.getpid()))
   libLF.log('Unpacking {} to {}'.format(tarball, tmpDir))
   if not os.path.exists(tmpDir):
       os.makedirs(tmpDir)
   
   with tarfile.open(tarball, "r:gz") as tar:
       tar.extractall(path=tmpDir) 
       return tmpDir

def main(projectCodePath, registry, outFile):
  checkRegistryDeps(registry)

  if os.path.isdir(projectCodePath):
    wasTarball = False
    srcDir = projectCodePath
  else:
    wasTarball = True
    try:
      # We should clean up srcDir later
      srcDir = unpackTarball(projectCodePath)
    except BaseException as err:
      libLF.log("Error while unpacking {}: {}".format(projectCodePath, err))
      raise err

  lang2sourceFiles = libLF.getUnvendoredSourceFiles(srcDir, registry)

  # TODO Project metrics: nFiles, cloc, ...

  nFilesAnalyzed = 0
  nRegexesFound = 0
  with open(outFile, 'w') as outStream:
    for lang, sourceFiles in lang2sourceFiles.items():
      for sourceFile in sourceFiles:
        output = extractRegexes(registry, lang, sourceFile)
        nFilesAnalyzed += 1
        if output is not None:
          for ru in output:
            nRegexesFound += 1
            ru.regexes = registry
            outStream.write(ru.toNDJSON() + '\n')
  libLF.log('Extracted a total of {} regexes from {} files'.format(nRegexesFound, nFilesAnalyzed))

  if wasTarball:
    cleanUp(srcDir)

###############################################

# Parse args
parser = argparse.ArgumentParser(description='Statically extract regexes from a module\'s GitHub project. Only regexes in the primary language of the module will be extracted. cf. ghp-extract-regexes.py')
parser.add_argument('--registry', '-r',  help='What registry did the module associated with this libLF.GitHub project come from?', required=True)
parser.add_argument('--src-path', '-t', help='GitHub project (tarball or root dir)', required=True, dest='srcPath')
parser.add_argument('--out-file', '-o', help='Where to write RegexUsage objects as NDJSON?', required=True, dest='outFile')

args = parser.parse_args()

# Here we go!
main(args.srcPath, args.registry, args.outFile)
