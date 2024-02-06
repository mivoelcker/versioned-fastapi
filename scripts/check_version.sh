#!/usr/bin/env bash
set -e

# Requires the a version tag as first argument

# Check if version tag matches current package version using hatch
version="${1#v}"
hatch_version=$(hatch version)
if [[ "$version" != "$hatch_version" ]]; then 
    echo "Release version '$version' does not match package version '$hatch_version'. Abort!" >&2
    exit 1
fi

echo "$version"