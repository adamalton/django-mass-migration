#!/usr/bin/env python

""" Make and push a tag which will trigger the release process (which is a GitHub Action).
    Usage:
        ./release.py kind
    where `kind` is major/minor/bugfix.
"""

import subprocess
import sys

KINDS = ("major", "minor", "bugfix")


def get_kind():
    kind = sys.argv[-1]
    while kind.lower() not in KINDS:
        kind = input(f"What kind of release? [{'/'.join(KINDS)}] ")
    return kind


def get_latest_tag():
    tags = subprocess.check_output(["git", "tag", "--list", "v*"]).split()
    return tags[-1].decode("utf8")


def increment_tag(tag, kind):
    """ Increment the relevant part of the tag for the given kind of release. """
    major, minor, bugfix = tag.replace("v", "").split(".")
    if kind == "major":
        major = int(major) + 1
    elif kind == "minor":
        minor = int(minor) + 1
    elif kind == "bugfix":
        bugfix = int(bugfix) + 1
    return f"v{major}.{minor}.{bugfix}"


def push_tag(tag_name):
    subprocess.check_output(["git", "tag", tag_name])
    subprocess.check_output(["git", "push", "origin", tag_name])


def main():
    tag_name = increment_tag(get_latest_tag(), get_kind())
    print(f"Pushing new tag: {tag_name}")
    push_tag(tag_name)
    print("Done")


if __name__ == "__main__":
    main()
