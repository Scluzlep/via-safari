#!/usr/bin/env python3
"""Cheap, read-only version check. No Android toolchain for unchanged versions."""
import json
import os
import pathlib
import re
import urllib.error
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
    repo = os.environ["GITHUB_REPOSITORY"]
    token = os.environ["GH_TOKEN"]
    release_req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/releases/tags/{tag}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "Via-Safari-Updater/1.0",
        },
    )
    try:
        with urllib.request.urlopen(release_req, timeout=20):
            build = False
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
        build = True
    print(f"Official version={version}; release={tag}; need_build={build}")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as f:
            f.write(f"version={version}\ntag={tag}\nshould_build={'true' if build else 'false'}\n")

if __name__ == "__main__":
    main()
