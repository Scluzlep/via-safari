#!/usr/bin/env python3
"""Atomically commit a published Release's JSON and last successful version."""
import json
import pathlib
import re
import shutil
import subprocess
import sys

REPO = "Scluzlep/via-safari"


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: commit_state.py VERSION RELEASE_JSON_PATH")
    version = str(sys.argv[1])
    if not re.fullmatch(r"[1-9][0-9]{0,9}", version):
        raise ValueError("Invalid version")
    source = pathlib.Path(sys.argv[2])
    data = json.loads(source.read_text(encoding="utf-8"))
    expected_url = (
        f"https://github.com/{REPO}/releases/download/via-{version}/Safari.apk"
    )
    if str(data.get("version")) != version or data.get("url") != expected_url:
        raise ValueError("Release manifest version or APK URL mismatch")
    if not re.fullmatch(r"[0-9a-fA-F]{32}", str(data.get("md5", ""))):
        raise ValueError("Release manifest missing signed APK MD5")

    version_file = pathlib.Path("version.env")
    old_contents = version_file.read_text(encoding="utf-8")
    match = re.search(r"(?m)^VIA_VERSION_CODE=([0-9]+)[ \t]*$", old_contents)
    if not match:
        raise ValueError("version.env missing valid VIA_VERSION_CODE")
    if int(version) < int(match.group(1)):
        raise ValueError("Refusing to move version.env backwards")

    pathlib.Path("latest_cn.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    version_file.write_text(
        "# Last successfully published Via Safari versionCode (not the last detected official version)\n"
        f"VIA_VERSION_CODE={version}\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(
        ["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"],
        check=True,
    )
    subprocess.run(["git", "add", "version.env", "latest_cn.json"], check=True)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], check=False)
    if staged.returncode == 0:
        print("Published state already current; no commit required")
        return
    if staged.returncode != 1:
        raise RuntimeError("git diff failed")
    subprocess.run(
        ["git", "commit", "-m", f"chore: publish Safari update {version}"],
        check=True,
    )
    subprocess.run(["git", "push", "origin", "HEAD:main"], check=True)
    print(f"Published latest_cn.json and version.env={version}")


if __name__ == "__main__":
    main()
