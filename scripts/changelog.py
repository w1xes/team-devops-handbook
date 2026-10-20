#!/usr/bin/env python3
"""Generate Markdown from Conventional Commits in the current branch."""

import argparse
from collections import defaultdict
from pathlib import Path
import re
import subprocess

from check_commit import HEADER


def render(records):
    groups = defaultdict(list)
    for sha, subject, body in records:
        match = HEADER.fullmatch(subject)
        if not match:
            continue
        kind = match.group(1)
        breaking = bool(match.group(3)) or bool(
            re.search(r"(?m)^BREAKING[ -]CHANGE: ", body)
        )
        label = "**BREAKING** " if breaking else ""
        groups[kind].append(f"- {label}{subject.split(': ', 1)[1]} (`{sha}`)")
    lines = ["# Changelog", "", "Generated from Git history; newest first within each type.", ""]
    for kind in sorted(groups):
        lines.extend([f"## {kind}", "", *groups[kind], ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", help="Exclude this revision and its ancestors.")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.since:
        # Resolve before forming a range; option-like input is never passed to log.
        sha = subprocess.check_output(
            ["git", "rev-parse", "--verify", "--end-of-options", f"{args.since}^{{commit}}"],
            text=True,
        ).strip()
        revision = f"{sha}..HEAD"
    else:
        revision = "HEAD"
    raw = subprocess.check_output(
        ["git", "log", "--format=%h%x00%s%x00%b%x00", revision, "--"], text=True
    )
    fields = raw.split("\0")
    records = [
        (fields[i].strip(), fields[i + 1], fields[i + 2])
        for i in range(0, len(fields) - 2, 3)
    ]
    content = render(records)
    if args.output:
        args.output.write_text(content, encoding="utf-8")
    else:
        print(content, end="")


if __name__ == "__main__":
    main()
