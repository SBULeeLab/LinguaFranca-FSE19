"""Lingua Franca: GitHub project
"""

import libLF.lf_ndjson as lf_ndjson
import libLF
import json
import re

class SimpleGitHubProjectNameAndStars:
  """GitHub project name with # stars
  
  name: projectOwner/repoName 
  nStars: integer
  """
  Type = 'SimpleGitHubProjectNameAndStars'
  def __init__(self):
    self.type = SimpleGitHubProjectNameAndStars.Type
    self.initialized = False

  def initFromRaw(self, name, nStars):
    """Initialize from individual fields"""
    self.initialized = True

    self.name = name
    self.nStars = nStars
    return self

  def initFromJSON(self, jsonStr):
    """Initialize from NDJSON string"""
    self.initialized = True

    obj = lf_ndjson.fromNDJSON(jsonStr)
    assert(obj['type'] == SimpleGitHubProjectNameAndStars.Type)
    self.type = obj['type']
    self.name = obj['name']
    self.nStars = obj['nStars']
    
    return self
  
  def toNDJSON(self):
    assert(self.initialized)
    # Consistent and in ndjson format
    return lf_ndjson.toNDJSON(self._toDict())
  
  def getOwner(self):
    return self.name.split('/')[0]

  def getName(self):
    return self.name.split('/')[1]

  def _toDict(self):
    obj = { "type": self.type,
            "name": self.name,
            "nStars": self.nStars
    }
    return obj
  
  def toGitHubProject(self):
    return libLF.GitHubProject() \
           .initFromRaw(self.getOwner(),
                        self.getName(),
                        "maven",
                        ["UNKNOWN"],
                        nStars=self.nStars)


class GitHubProject:
    """Represents a GitHub project.
    
    owner: The project owner: github.com/OWNER/name, e.g. 'facebook'
    name: The project name: github.com/owner/NAME, e.g. 'react'
    registry: What registry did we get this project from, e.g. 'crates.io'
    modules: The registry modules that pointed to this project, e.g. ['rustModule1', 'rustModule2']
    nStars: The number of GitHub accounts that starred this project, e.g. 1
      Default is GitHubProject.UnknownStars
    tarballPath: The path to a tarball of a clone of this project on sushi, e.g. '/home/davisjam/lf/clones/crates.io/1/facebook-react.tgz'
      Default is GitHubProject.NoTarballPath
    regexPath: The path to a ndjson file of RegexUsage objects found in this project on sushi, e.g. '/home/davisjam/lf/clones/crates.io/1/facebook-react.json'
      Default is GitHubProject.NoRegexPath
    """

    UnknownStars = -1
    NoTarballPath = 'NoTarballPath'
    NoRegexPath = 'NoRegexPath'
    Type = 'GitHubProject'

    def __init__(self):
        """Declare an object and then initialize using JSON or "Raw" input."""
        self.initialized = False
        self.type = GitHubProject.Type
  
    def initFromRaw(self, owner, name, registry, modules, nStars=UnknownStars, tarballPath=NoTarballPath, regexPath=NoRegexPath):
        """Initialize from individual fields"""
        self.initialized = True

        self.owner = owner
        self.name = name
        self.registry = registry
        self.modules = modules

        if nStars is not None:
          self.nStars = nStars
        else:
          self.nStars = GitHubProject.UnknownStars

        if tarballPath is not None:
          self.tarballPath = tarballPath
        else:
          self.tarballPath = GitHubProject.NoTarballPath

        if regexPath is not None:
          self.regexPath = regexPath
        else:
          self.regexPath = GitHubProject.NoRegexPath
        
        return self

    def initFromJSON(self, jsonStr):
        """Initialize from ndjson string"""
        self.initialized = True

        obj = lf_ndjson.fromNDJSON(jsonStr)
        assert(obj['type'] == GitHubProject.Type)
        self.type = obj['type']
        self.owner = obj['owner']
        self.name = obj['name']
        self.registry = obj['registry']
        self.modules = obj['modules']
        self.nStars = obj['nStars']
        self.tarballPath = obj['tarballPath']
        if 'regexPath' in obj:
            self.regexPath = obj['regexPath']
        else:
            self.regexPath = GitHubProject.NoRegexPath
        
        return self

    def toNDJSON(self):
        assert(self.initialized)
        # Consistent and in ndjson format
        return lf_ndjson.toNDJSON(self._toDict())

    def _toDict(self):
        obj = { "type": self.type,
                "registry": self.registry,
                "owner": self.owner,
                "name": self.name,
                "modules": self.modules,
                "nStars": self.nStars,
                "tarballPath": self.tarballPath,
                "regexPath": self.regexPath
        }
        return obj

    def getNModules(self):
      """Return the number of modules that point to this project."""
      return len(self.modules)
