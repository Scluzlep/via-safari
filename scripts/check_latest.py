#!/usr/bin/env python3
"""Cheap, read-only version check. No Android toolchain for unchanged versions."""
import json
import os
import pathlib
import re
import subprocess
import urllib.request

SOURCE = "https://res.viayoo.com/v1/latest_cn.json"

def main():
    req = urllib.request.Request(SOURCE, headers={"User-Agent": "Via-Safari-Updater/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.load(response)
    if not isinstance(data, dict):
        raise ValueError("Unexpected upstream JSON structure")
    version = str(data.get("version", ""))
    if not re.fullmatch(r"[1-9][0-9]{0,9}", version):
        raise ValueError(f"Unexpected upstream version: {version!r}")
    version_int = int(version)
    if version_int > 2147483647:
        raise ValueError("Upstream versionCode exceeds Android signed 32-bit limit")
    tag = f"via-{version}"
    pathlib.Path("work").mkdir(exist_ok=True)
    pathlib.Path("work/upstream.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    proc = subprocess.run(
        ["gh", "release", "view", tag, "-R", os.environ["GITHUB_REPOSITORY"]],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    build = proc.returncode != 0
    print(f"Official version={version}; release={tag}; need_build={build}")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as f:
            f.write(f"version={version}\ntag={tag}\nshould_build={'true' if build else 'false'}\n")

if __name__ == "__main__":
    main()
