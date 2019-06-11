#!/usr/bin/env bash

echo "Configuring repo. I hope you use Ubuntu..."

set -x
set -e

# Need this for the vuln-regex-detector installation
echo "Installing nvm"
curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.33.8/install.sh | bash
# Source so nvm is in path now
touch ~/.bashrc && . ~/.bashrc

echo "Installing and using node v8.9.3. The code works at this level, so insulate against future breaking changes."
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
nvm install v8.9.3
nvm alias default v8.9.3

## Dependencies

echo "Configuring submodule: vuln-regex-detector"
pushd analysis/performance/vuln-regex-detector
./configure
popd

echo "Configuring per-language regex extractors"
pushd data/production-regexes/static-extractors/
./compile-extractors.pl
popd

echo "Configuring per-language regex drivers"
pushd analysis/test-regex-behavior-in-language/
./compile-testers.pl
popd

echo "Compiling input generators"
pushd analysis/semantic/input-generation/generators/
./compile-input-generators.pl
popd 

echo "Configuration complete. I hope everything works!"
