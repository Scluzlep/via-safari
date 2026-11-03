#!/usr/bin/env python3
"""Cheap, read-only version check. No Android toolchain for unchanged versions."""
import json
import os
import pathlib
import re
import subprocess
import time
import urllib.error
import urllib.request

SOURCE = "https://res.viayoo.com/v1/latest_cn.json"

def keep_schedule_alive_if_needed(build):
    """Avoid GitHub's 60-day inactivity auto-disable without an extra job."""
    if build or os.environ.get("GITHUB_EVENT_NAME") != "schedule":
        return
    last = int(subprocess.check_output(
        ["git", "log", "-1", "--format=%ct"], text=True).strip())
    if time.time() - last < 45 * 86400:
        return
    heartbeat = pathlib.Path(".github/last-active.txt")
    heartbeat.parent.mkdir(exist_ok=True)
    heartbeat.write_text(f"{int(time.time())}\\n", encoding="utf-8")
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], check=True)
    subprocess.run(["git", "add", str(heartbeat)], check=True)
    subprocess.run(["git", "commit", "-m", "chore: keep scheduled update check active"], check=True)
    subprocess.run(["git", "push", "origin", "HEAD:main"], check=True)
    print("Committed low-frequency heartbeat to prevent schedule auto-disable")


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
    keep_schedule_alive_if_needed(build)
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as f:
            f.write(f"version={version}\ntag={tag}\nshould_build={'true' if build else 'false'}\n")

if __name__ == "__main__":
    main()
