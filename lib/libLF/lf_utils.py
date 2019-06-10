"""Lingua Franca: utils
"""

import time
import sys
import platform
import os
import hashlib
import subprocess
import shutil

#####
# Logging
#####

def log(msg):
  """Log this message."""
  sys.stderr.write('{} {}/{}: {}\n'.format(time.strftime('%d/%m/%Y %H:%M:%S'), platform.node(), os.getpid(), msg))

#####
# Hashing strings
#####

def hashString(string):
  """Obtain hex digest of this string.
  
  Returns:
    digest (str): hex chars double the length of string"""
  hashObject = hashlib.md5(string.encode())
  return hashObject.hexdigest()

#####
# Shelling out
#####

def runcmd(cmd):
  """Run this command

  Args:
    cmd (str): Command to run
  
  Returns:
    rc (int)
    stdout (str)
  """
  log('CMD: {}'.format(cmd))
  completedProcess = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, close_fds=True)
  return completedProcess.returncode, completedProcess.stdout.decode('utf-8')

def chkcmd(cmd):
  """Run this command and confirm rc is 0.

  This lets you try-catch one or more "shelled out" commands
  without muddying the waters with rc checking.

  Args:
    cmd (str): Command to run
  
  Returns:
    stdout (str)

  Raises:
    OSError: rc is not 0
  """
  rc, out = runcmd(cmd)
  if rc is not 0:
    raise OSError('Error, cmd <{}> returned {}: {}'.format(cmd, rc, out))
  return out

def checkShellDependencies(deps, mustBeExecutable=True):
  """Ensure each of deps exists (or, if mustBeExecutable, is in PATH)

  Args:
    deps str[]: list of shell dependencies

  Raises:
    AssertionError: some dep is not in PATH
  """
  log('Checking shell dependencies {}'.format(deps))
  depsNotExist = set()
  depsNotInPath = set()
  for dep in deps:
    if os.path.isfile(dep):
      if shutil.which(dep):
        pass
      else:
        depsNotInPath.add(dep)
    else:
      depsNotExist.add(dep)

  if mustBeExecutable:
    if len(depsNotInPath):
      raise AssertionError("Error, non-executable dependencies: {}".format(depsNotInPath))
  else:
    if len(depsNotExist):
      raise AssertionError("Error, non-existent dependencies: {}".format(depsNotExist))

def pathSplitAll(path):
    """'/tmp/foo/bar' -> [os.sep, 'tmp', 'foo', 'bar']"""
    reversePathArr = [] # '/tmp/foo' -> ['foo', 'tmp']

    remainingPath = path
    while remainingPath:
        if remainingPath == os.sep:
            reversePathArr.append(remainingPath)
            break
        (head, tail) = os.path.split(remainingPath)
        reversePathArr.append(tail)
        remainingPath = head
    reversePathArr.reverse()
    return reversePathArr

def writeToFile(f, cont):
  with open(f, 'w') as out:
    out.write(cont)

def writeToFileNDJSON(f, items):
  """"Write out items in NDJSON format. Each item must have a toNDJSON() method"""
  with open(f, 'w') as out:
    for item in items:
      out.write(item.toNDJSON() + "\n")