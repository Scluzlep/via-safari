#!/usr/bin/env python3
"""Cheap scheduled check: build only if upstream version > last successfully published."""
import json
import os
import pathlib
import re
import subprocess
import time
import urllib.error
import urllib.request

SOURCE = "https://res.viayoo.com/v1/latest_cn.json"
VERSION_FILE = pathlib.Path("version.env")


def read_published_version():
    if not VERSION_FILE.is_file():
        raise ValueError("version.env missing; refusing to assume an old version")
    matches = re.findall(
        r"(?m)^VIA_VERSION_CODE=([0-9]+)[ \t]*$",
        VERSION_FILE.read_text(encoding="utf-8"),
    )
    if len(matches) != 1:
        raise ValueError("version.env must contain exactly one VIA_VERSION_CODE")
    return int(matches[0])


def keep_schedule_alive_if_needed(pending):
    """Prevent GitHub's 60-day inactivity auto-disable, without another workflow."""
    if pending or os.environ.get("GITHUB_EVENT_NAME") != "schedule":
        return
    last = int(subprocess.check_output(
        ["git", "log", "-1", "--format=%ct"], text=True).strip())
    if time.time() - last < 45 * 86400:
        return
    heartbeat = pathlib.Path(".github/last-active.txt")
    heartbeat.parent.mkdir(exist_ok=True)
    heartbeat.write_text(f"{int(time.time())}\n", encoding="utf-8")
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], check=True)
    subprocess.run(["git", "add", str(heartbeat)], check=True)
    subprocess.run(["git", "commit", "-m", "chore: keep scheduled update check active"], check=True)
    subprocess.run(["git", "push", "origin", "HEAD:main"], check=True)
    print("Updated low-frequency schedule heartbeat")


def get_existing_release(tag):
    """Return release only if the tag is already published; propagate other errors."""
    repo = os.environ["GITHUB_REPOSITORY"]
    token = os.environ["GH_TOKEN"]
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/releases/tags/{tag}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "Via-Safari-Updater/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def main():
    req = urllib.request.Request(
        SOURCE, headers={"User-Agent": "Via-Safari-Updater/1.0", "Accept": "application/json"}
    )
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

    published = read_published_version()
    tag = f"via-{version}"
    build = False
    recover = False

    if version_int > published:
        # Version change detected: check if a previous run already published
        # its Release but failed before writing version.env.
        release = get_existing_release(tag)
        if release is None:
            build = True
        else:
            assets = {entry.get("name") for entry in release.get("assets", [])}
            if not {"Safari.apk", "latest_cn.json"}.issubset(assets):
                raise ValueError(f"Release {tag} exists but is incomplete: {assets}")
            recover = True

    if build:
        pathlib.Path("work").mkdir(exist_ok=True)
        pathlib.Path("work/upstream.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    print(
        f"Upstream={version}; published={published}; "
        f"build={build}; recover_release_state={recover}"
    )
    keep_schedule_alive_if_needed(build or recover)
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as f:
            f.write(
                f"version={version}\ntag={tag}\n"
                f"should_build={'true' if build else 'false'}\n"
                f"should_recover={'true' if recover else 'false'}\n"
            )


if __name__ == "__main__":
    main()
