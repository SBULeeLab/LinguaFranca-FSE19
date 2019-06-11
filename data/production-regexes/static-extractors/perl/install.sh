#!/usr/bin/env bash

echo "Installing dependencies for Perl regex extraction using CPAN"
echo "  (I hope you configured CPAN on this node)"

set -e
set -x

cpan install JSON
cpan install PPI
