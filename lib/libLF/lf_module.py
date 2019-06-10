"""Lingua Franca: Module info
TODO I need tests!
"""

import libLF.lf_ndjson as lf_ndjson
import libLF
import requests
import json
import re

registryToPrimaryLanguages = {
    'crates.io': ['rust'],
    'cpan': ['perl'],
    'npm': ['javascript', 'typescript'],
    'pypi': ['python'],
    'maven': ['java'],
    'rubygems': ['ruby'],
    'packagist': ['php'],
    'nuget': ['C#'],
    'godoc': ['go']
}

class ModuleInfo:
    """Represents a software module in a registry.
    
    type: 'ModuleInfo' or sub-class type
    registry: What registry this module came from, e.g. 'crates.io', 'cpan'
    name: The name of the module in the registry, e.g. 'eslint'.
    version: The version of the module under consideration.
            e.g. '0.0.1'
            We are interested in the most recent version of each module
            at the time of study.
            If the registry does not provide version numbers,
            this will be ModuleInfo.NoVersion
    popularity: Some numeric measure of popularity. Larger is better.
            If the registry does not provide version numbers,
            this will be ModuleInfo.NoPopularity
    registryUri: URI to get the most recent version of this module from the registry
                e.g. 'http://registry.npmjs.org/0/-/0-0.0.0.tgz'
                If no registryUri, this will be ModuleInfo.NoRegistryUri
    vcsUri: URI to the source code of this module (in a Version Control System)
            e.g. 'git+https://github.com/25th-floor/javascript.git'
            If no source URI exists, this will be ModuleInfo.NoVCSUri
    tarballPath: Path to a registry artifact of this module as a tarball.
    
    Must have at least one of { registryUri, vcsUri } defined.

    Use the factory method when handling arbitrary ModuleInfo's from files.
    """

    NoPopularity = -1
    NoVersion = 'NoVersion'
    NoRegistryUri = 'NoRegistryUri'
    NoVCSUri = 'NoVCSUri'
    NoGitHubStars = -1
    NoTarballPath = 'NoTarballPath'

    def factory(jsonStr):
      """Create *and initialize* a ModuleInfo from this ndjson string."""
      # Parse and get the 'type' field.
      obj = lf_ndjson.fromNDJSON(jsonStr)
      if not 'type' in obj:
        raise ValueError('Error no type in jsonStr: {}'.format(jsonStr))

      # Re-parse based on the appropriate type.
      moduleInfo = None
      if obj['type'] == 'CpanInfo':
        moduleInfo = CpanInfo()
      elif obj['type'] == 'CratesInfo':
        moduleInfo = CratesInfo()
      elif obj['type'] == 'NpmInfo':
        moduleInfo = NpmInfo()
      elif obj['type'] == 'PypiInfo':
        moduleInfo = PypiInfo()
      elif obj['type'] == 'PackagistInfo':
        moduleInfo = PackagistInfo()
      elif obj['type'] == 'GodocInfo':
        moduleInfo = GodocInfo()
      elif obj['type'] == 'NugetInfo':
        moduleInfo = NugetInfo()
      elif obj['type'] == 'RubygemsInfo':
        moduleInfo = RubygemsInfo()
      else:
        raise ValueError('Error, unexpected type {}'.format(obj['type']))

      moduleInfo.initFromJSON(jsonStr)
      return moduleInfo

    def __init__(self):
        """Declare an object and then initialize using JSON or "Raw" input."""
        self.initialized = False
        self.type = 'ModuleInfo'
  
    def initFromRaw(self, registry, name, version=None, popularity=None, registryUri=None, vcsUri=None, gitHubStars=None, gitHubStarsFetchTime=None, tarballPath=None):
        """Initialize from individual fields

        registry: a string
        name: a string
        version: None or the version as a string
        popularity: None or a number
        registryUri: None or ...
        vcsUri: None or ...
        gitHubStars: None or TODO
        gitHubStarsFetchTime: None or TODO
        tarballPath: None or a string

        At least one of registryUri and vcsUri must be non-None.
        """
        self.initialized = True

        assert(registry in registryToPrimaryLanguages)
        self.registry = registry

        self.name = name
        
        if version is not None:
            self.version = version
        else:
            self.version = ModuleInfo.NoVersion

        if popularity is not None:
            self.popularity = popularity
        else:
            self.popularity = ModuleInfo.NoPopularity

        if registryUri is not None:
            self.registryUri = registryUri
        else:
            self.registryUri = ModuleInfo.NoRegistryUri

        if vcsUri is not None:
            self.vcsUri = vcsUri
        else:
            self.vcsUri = ModuleInfo.NoVCSUri

        if gitHubStars is not None:
            self.gitHubStars = gitHubStars
        else:
            self.gitHubStars = ModuleInfo.NoGitHubStars

        if gitHubStarsFetchTime is not None:
            self.gitHubStarsFetchTime = gitHubStarsFetchTime
        else:
            self.gitHubStarsFetchTime = ModuleInfo.NoGitHubStars

        if tarballPath is not None:
            self.tarballPath = tarballPath
        else:
            self.tarballPath = ModuleInfo.NoTarballPath
        
        # Must have some URI.
        if self.registryUri is ModuleInfo.NoRegistryUri and self.vcsUri is ModuleInfo.NoVCSUri:
            raise ValueError('Must provide at least one uri')
        return self

    def initFromJSON(self, jsonStr):
        self.initialized = True

        obj = lf_ndjson.fromNDJSON(jsonStr)
        self.registry = obj['registry']
        self.name = obj['name']
        self.version = obj['version']
        self.popularity = obj['popularity']
        self.registryUri = obj['registryUri']
        self.vcsUri = obj['vcsUri']

        if 'gitHubStars' in obj:
            self.gitHubStars = obj['gitHubStars']
        else:
            self.gitHubStars = ModuleInfo.NoGitHubStars

        if 'gitHubStarsFetchTime' in obj:
            self.gitHubStarsFetchTime = obj['gitHubStarsFetchTime']
        else:
            self.gitHubStarsFetchTime = ModuleInfo.NoGitHubStars

        if 'tarballPath' in obj:
            self.tarballPath = obj['tarballPath']
        else:
            self.tarballPath = ModuleInfo.NoTarballPath

        return self

    def enhanceFromRegistry(self):
      """Enhance this object's members by contacting the registry

      This is necessary in registries that don't provide enough info in the index.
      @return self
      """
      return self

    def toNDJSON(self):
        assert(self.initialized)
        # Consistent and in ndjson format
        return lf_ndjson.toNDJSON(self._toDict())

    def _toDict(self):
        obj = { "registry": self.registry,
                "name": self.name,
                "version": self.version,
                "popularity": self.popularity,
                "registryUri": self.registryUri,
                "vcsUri": self.vcsUri,
                "gitHubStars": self.gitHubStars,
                "gitHubStarsFetchTime": self.gitHubStarsFetchTime,
                "tarballPath": self.tarballPath
        }
        return obj
    
    def getArtifactURL(self):
       """Return a URL from which to fetch the registry's packaged version of this module."""
       return self.registryUri

class CpanInfo(ModuleInfo):
    """CPAN module information"""
    def __init__(self):
        super().__init__()
        self.type = "CpanInfo"

    def initFromRaw(self, name, registryUri, category, author, size, publishDate):
        super().initFromRaw('cpan', name, version=None, popularity=-1, registryUri=registryUri, vcsUri=None)
        self.category = category
        self.author = author
        self.size = size
        self.publishDate = publishDate
        return self
    
    def initFromJSON(self, jsonStr):
        super().initFromJSON(jsonStr)
        obj = lf_ndjson.fromNDJSON(jsonStr)
        assert(obj['type'] == self.type)
        self.category = obj['category']
        self.author = obj['author']
        self.size = obj['size']
        self.publishDate = obj['publishDate']
        return self

    def enhanceFromRegistry(self):
      """Enhance this object's members by contacting the registry"""
      assert(False)

    def _toDict(self):
        obj = super()._toDict()
        obj['type'] = self.type
        obj['category'] = self.category
        obj['author'] = self.author
        obj['size'] = self.size
        obj['publishDate'] = self.publishDate

        return obj

class CratesInfo(ModuleInfo):
    """crates.io module information"""
    def __init__(self):
        super().__init__()
        self.type = "CratesInfo"

    def initFromRaw(self, name, mostRecentVersion, totalDownloads, recentDownloads,
     vcsUri, documentationUri, keywords, categories, createDate, mostRecentPublishDate):
        super().initFromRaw('crates.io', name, version=mostRecentVersion, popularity=totalDownloads, registryUri=None, vcsUri=vcsUri)
        self.recentDownloads = recentDownloads
        self.documentationUri = documentationUri
        self.keywords = keywords
        self.categories = categories
        self.createDate = createDate
        self.mostRecentPublishDate = mostRecentPublishDate
        return self

    def initFromJSON(self, jsonStr):
        super().initFromJSON(jsonStr)
        obj = lf_ndjson.fromNDJSON(jsonStr)
        assert(obj['type'] == self.type)
        self.recentDownloads = obj['recentDownloads']
        self.documentationUri = obj['documentationUri']
        self.keywords = obj['keywords']
        self.categories = obj['categories']
        self.createDate = obj['createDate']
        self.mostRecentPublishDate = obj['mostRecentPublishDate']
        return self

    def _toDict(self):
        obj = super()._toDict()
        obj['type'] = self.type
        obj['recentDownloads'] = self.recentDownloads
        obj['documentationUri'] = self.documentationUri
        obj['keywords'] = self.keywords
        obj['categories'] = self.categories
        obj['createDate'] = self.createDate
        obj['mostRecentPublishDate'] = self.mostRecentPublishDate
        return obj

class NpmInfo(ModuleInfo):
    """npm module information"""
    def __init__(self):
        super().__init__()
        self.type = "NpmInfo"
        
    def initFromRaw(self, name, mostRecentVersion,
     registryUri, vcsUri, documentationUri, mostRecentPublishDate):
        super().initFromRaw('npm', name, version=mostRecentVersion, popularity=-1, registryUri=registryUri, vcsUri=vcsUri)
        self.documentationUri = documentationUri
        self.mostRecentPublishDate = mostRecentPublishDate
        return self

    def initFromJSON(self, jsonStr):
        super().initFromJSON(jsonStr)
        obj = lf_ndjson.fromNDJSON(jsonStr)
        assert(obj['type'] == self.type)
        self.documentationUri = obj['documentationUri']
        self.mostRecentPublishDate = obj['mostRecentPublishDate']
        return self

    def _toDict(self):
        obj = super()._toDict()
        obj['type'] = self.type
        obj['documentationUri'] = self.documentationUri
        obj['mostRecentPublishDate'] = self.mostRecentPublishDate
        return obj

class PypiInfo(ModuleInfo):
    """pypi module information"""
    def __init__(self):
        super().__init__()
        self.type = "PypiInfo"

    def initFromRaw(self, name, registryUri):
        """Minimal info from the 'simple table' pypi API.
        
        @param registryUri: This is fake -- in other registries this is URL for the registry artifact.
                            In this registry it is just the API endpoint for more info.
                            Like PackagistInfo.
        """                
        super().initFromRaw('pypi', name, version=None, popularity=None, registryUri=registryUri, vcsUri=None)
        return self

    def initFromJSON(self, jsonStr):
        super().initFromJSON(jsonStr)
        obj = lf_ndjson.fromNDJSON(jsonStr)
        assert(obj['type'] == self.type)
        return self

    def enhanceFromRegistry(self):
      """Enhance this object's members by contacting the registry"""
      # PyPI API is documented here: https://wiki.python.org/moin/PyPIJSON
      # And here: https://warehouse.readthedocs.io/api-reference/json/
      jsonEndpoint = 'https://pypi.org/pypi/{}/json'.format(self.name)
      try:
        response = requests.get(jsonEndpoint, verify=False, timeout=0.5)
        obj = json.loads(response.text)

        # There are several viable places for a github URI to live.
        allUris = []
        try:
          allUris.append(obj['info']['home_page'])
        except:
          pass

        try:
          allUris.append(obj['info']['project_urls']['Homepage'])
        except:
          pass

        try:
          allUris.append(obj['info']['project_url'])
        except:
          pass

        # Filter out 'UNKNOWN'
        allUris = [uri for uri in allUris if uri is not None and uri.upper() != 'UNKNOWN']

        # Pick out prioritized lists using regexes.
        githubUris = [uri for uri in allUris if re.search(r'github', uri)]
        popularVCSUris= [uri for uri in allUris if re.search(r'github|bitbucket|gitlab|sourceforge', uri)]
      
        # How'd we do?
        vcsUri = None
        if len(githubUris):
          vcsUri = githubUris[0]
        elif len(popularVCSUris):
          vcsUri = popularVCSUris[0]
        elif len(allUris):
          vcsUri = allUris[0]

        if vcsUri:
          libLF.log('Got a vcsUri: {}'.format(vcsUri))
          self.vcsUri = vcsUri
        else:
          libLF.log('No vcsUri')

      except KeyboardInterrupt:
        raise
      except:
        pass
      return self

    def _toDict(self):
        obj = super()._toDict()
        obj['type'] = self.type
        return obj

class PackagistInfo(ModuleInfo):
    """Packagist module information"""
    def __init__(self):
        super().__init__()
        self.type = "PackagistInfo"

    def initFromRaw(self, name, registryUri):
        """Minimal info from the 'list packages' packagist API.
        
        @param registryUri: This is fake -- in most other registries this is URL for the registry artifact.
                            In this registry it is just the API endpoint for more info.
                            Like PypiInfo.
        """                
        super().initFromRaw('packagist', name, version=None, popularity=None, registryUri=registryUri, vcsUri=None)
        return self

    def initFromJSON(self, jsonStr):
        super().initFromJSON(jsonStr)
        obj = lf_ndjson.fromNDJSON(jsonStr)
        assert(obj['type'] == self.type)
        return self

    def enhanceFromRegistry(self):
      """Enhance this object's members by contacting the registry"""
      # Packagist API is documented here: https://packagist.org/apidoc#get-package-data
      jsonEndpoint = 'https://repo.packagist.org/p/{}.json'.format(self.name)
      try:
        response = requests.get(jsonEndpoint, verify=False, timeout=0.5)
        obj = json.loads(response.text)
        # Look in every version for a vcsUri
        for version in obj['packages'][self.name]:
          try:
            self.vcsUri = obj['packages'][self.name][version]['source']['url']
            if self.vcsUri:
              break
          except:
            pass # NBD Just try another version
      except KeyboardInterrupt:
        raise
      except:
        pass
      return self

    def _toDict(self):
        obj = super()._toDict()
        obj['type'] = self.type
        return obj

class GodocInfo(ModuleInfo):
    """Godoc module information"""
    def __init__(self):
        super().__init__()
        self.type = "GodocInfo"

    def initFromRaw(self, name, vcsUri):
        """Minimal info from the 'list packages' godoc API."""                
        super().initFromRaw('godoc', name, version=None, popularity=None, registryUri=None, vcsUri=vcsUri)
        return self

    def initFromJSON(self, jsonStr):
        super().initFromJSON(jsonStr)
        obj = lf_ndjson.fromNDJSON(jsonStr)
        assert(obj['type'] == self.type)
        return self

    def _toDict(self):
        obj = super()._toDict()
        obj['type'] = self.type
        return obj

class NugetInfo(ModuleInfo):
    """Nuget module information"""
    def __init__(self):
        super().__init__()
        self.type = "NugetInfo"

    def initFromRaw(self, name, version, registryUri):
        """Info from the Nuget catalog.
        
        @param registryUri: JSON endpoint with projectUrl or licenseUrl or etc. that might be helpful.
        """
        super().initFromRaw('nuget', name, version=version, registryUri=registryUri)
        return self

    def initFromJSON(self, jsonStr):
        super().initFromJSON(jsonStr)
        obj = lf_ndjson.fromNDJSON(jsonStr)
        assert(obj['type'] == self.type)
        return self

    def enhanceFromRegistry(self):
      """Enhance this object's members by contacting the registry"""
      # The JSON endpoint is the registryUri set during Nuget index scraping.
      # API: https://docs.microsoft.com/en-us/nuget/api/registration-base-url-resource#base-url
      jsonEndpoint = self.registryUri
      try:
        response = requests.get(jsonEndpoint, verify=False, timeout=0.5)
        obj = json.loads(response.text)
        # Prioritize by likelihood of being a relevant URL
        for uri in ['projectUrl', 'licenseUrl', 'iconUrl', 'releaseNotes']:
          if obj[uri]:
            self.vcsUri = obj[uri]
            break
      except KeyboardInterrupt:
        raise
      except:
        pass
      return self

    def _toDict(self):
        obj = super()._toDict()
        obj['type'] = self.type
        return obj

class RubygemsInfo(ModuleInfo):
    """Rubygems module information"""
    def __init__(self):
        super().__init__()
        self.type = "RubygemsInfo"

    def initFromRaw(self, name, registryUri):
        """Info from the Rubygems letter-by-letter index.
        
        @param registryUri: JSON endpoint with project_uri or homepage_uri or documentation_uri that might be helpful.
        """
        super().initFromRaw('rubygems', name, version=None, registryUri=registryUri)
        return self

    def initFromJSON(self, jsonStr):
        super().initFromJSON(jsonStr)
        obj = lf_ndjson.fromNDJSON(jsonStr)
        assert(obj['type'] == self.type)
        return self

    def enhanceFromRegistry(self):
      """Enhance this object's members by contacting the registry"""
      # Rubygems API is documented here: https://guides.rubygems.org/rubygems-org-api/#gem-methods
      jsonEndpoint = 'https://rubygems.org/api/v1/gems/{}.json'.format(self.name)
      try:
        response = requests.get(jsonEndpoint, verify=False, timeout=0.5)
        obj = json.loads(response.text)
        # Prioritize by likelihood of being a relevant URL
        for uri in ['source_code_uri', 'homepage_uri', 'bug_tracker_uri', 'documentation_uri']:
          if obj[uri]:
            self.vcsUri = obj[uri]
            break
      except KeyboardInterrupt:
        raise
      except:
        pass
      return self

    def _toDict(self):
        obj = super()._toDict()
        obj['type'] = self.type
        return obj
