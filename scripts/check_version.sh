#!/usr/bin/env bash
set -e

# Requires the a version tag as first argument

# Check if the version tag matches a simple semantic version pattern
# Does not support more complex version e.g. pre-release, alpha etc.
if ! [[ "$1" =~ v[0-9]+\.[0-9]+\.[0-9]+ ]]; then
    echo "Given version tag '$1' does not match semantic version pattern. Abort!" >&2
    exit 1
fi

# Check if version tag matches current package verison using hatch
version="${1#v}"
hatch_version=$(hatch version)
if [[ "$version" != "$hatch_version" ]]; then 
    echo "Release version '$version' does not match package version '$hatch_version'. Abort!" >&2
    exit 1
fi

echo "$version"