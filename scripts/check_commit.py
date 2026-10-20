#!/usr/bin/env python3
"""Validate commit files, stdin, or every commit in a Git revision range."""

import argparse
import re
import subprocess
import sys
from pathlib import Path

TYPES = "feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert"
HEADER = re.compile(
    rf"^({TYPES})(\([a-z][a-z0-9/-]*\))?(!)?: \S.*$"
)


def validate(message):
    lines = message.splitlines()
    if not lines or not HEADER.fullmatch(lines[0]):
        return "Expected type[(scope)][!]: description (Conventional Commits)."
    if len(lines[0]) > 72:
        return "Commit header exceeds 72 characters."
    if any(line != line.rstrip() for line in lines):
        return "Commit message has trailing whitespace."
    if len(lines) > 1 and lines[1]:
        return "Separate the header and body with a blank line."
    return None


def git(*args):
    return subprocess.check_output(["git", *args], text=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("file", nargs="?")
    source.add_argument("--stdin", action="store_true")
    source.add_argument("--range", dest="revision_range")
    args = parser.parse_args()
    if args.revision_range:
        commits = git("rev-list", args.revision_range, "--").splitlines()
        if not commits:
            parser.error("The selected range contains no commits.")
        messages = [(sha[:7], git("show", "-s", "--format=%B", sha)) for sha in commits]
    elif args.stdin:
        messages = [("stdin", sys.stdin.read())]
    else:
        messages = [(args.file, Path(args.file).read_text(encoding="utf-8"))]
    failed = False
    for label, message in messages:
        error = validate(message)
        if error:
            print(f"{label}: {error}", file=sys.stderr)
            failed = True
    if not failed:
        print(f"Validated {len(messages)} commit message(s).")
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
