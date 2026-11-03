#!/usr/bin/env python3
"""Verify an Apktool-decoded official APK matches Via's version feed.

Apktool moves android:versionCode into apktool.yml, so it may be absent
from the decoded AndroidManifest.xml.
"""
import argparse
import pathlib
import re
import xml.etree.ElementTree as ET


def read_apktool_version(metadata: str) -> int:
    lines = [
        line.split(":", 1)[1].strip()
        for line in metadata.splitlines()
        if line.lstrip().startswith("versionCode:")
    ]
    if len(lines) != 1:
        raise ValueError(f"Expected exactly one versionCode in apktool.yml, found {len(lines)}")
    value = lines[0].strip("'\"")
    if not re.fullmatch(r"[1-9][0-9]{0,9}", value):
        raise ValueError(f"Invalid versionCode in apktool.yml: {lines[0]!r}")
    return int(value)


def verify(decoded: pathlib.Path, expected: int) -> None:
    root = ET.parse(decoded / "AndroidManifest.xml").getroot()
    if root.get("package") != "mark.via":
        raise ValueError(f"Unexpected package: {root.get('package')!r}")
    actual = read_apktool_version((decoded / "apktool.yml").read_text(encoding="utf-8"))
    if actual != expected:
        raise ValueError(f"Official JSON versionCode={expected}, APK versionCode={actual}")
    print(f"Official APK verified: mark.via versionCode={actual}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--decoded", type=pathlib.Path, required=True)
    parser.add_argument("--version", type=int, required=True)
    args = parser.parse_args()
    verify(args.decoded, args.version)
