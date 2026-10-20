#!/bin/sh
set -eu
cd "$(git rev-parse --show-toplevel)"
current=$(git config --local --get core.hooksPath || true)
if [ -n "$current" ] && [ "$current" != .githooks ]; then
    echo "Existing core.hooksPath=$current; preserve or migrate it first." >&2
    exit 1
fi
git config --local core.hooksPath .githooks
echo 'Installed pre-commit and commit-msg from .githooks.'
