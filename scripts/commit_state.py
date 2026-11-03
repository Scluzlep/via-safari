#!/usr/bin/env python3
"""Publish a completed Release's JSON + version file without clobbering new commits."""
import json
import pathlib
import re
import subprocess
import sys
import time

REPO = "Scluzlep/via-safari"


def run(*args, check=True):
    return subprocess.run(list(args), check=check, text=True, capture_output=True)


def load_version():
    contents = pathlib.Path("version.env").read_text(encoding="utf-8")
    found = re.findall(r"(?m)^VIA_VERSION_CODE=([0-9]+)[ \\t]*$", contents)
    if len(found) != 1:
        raise ValueError("version.env must contain a single numeric VIA_VERSION_CODE")
    return int(found[0])


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: commit_state.py VERSION RELEASE_JSON_PATH")
    version = str(sys.argv[1])
    if not re.fullmatch(r"[1-9][0-9]{0,9}", version):
        raise ValueError("Invalid version")
    data = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
    expected_url = f"https://github.com/{REPO}/releases/download/via-{version}/Safari.apk"
    if str(data.get("version")) != version or data.get("url") != expected_url:
        raise ValueError("Release JSON version or URL mismatch")
    if not re.fullmatch(r"[0-9a-fA-F]{32}", str(data.get("md5", ""))):
        raise ValueError("Release JSON missing signed APK MD5")

    run("git", "config", "user.name", "github-actions[bot]")
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")

    # The checkout may be several commits old by the time the APK is signed.
    # Rebase via a clean checkout of current origin/main; only generated files
    # are authored here. Never force-push or discard published versions.
    for attempt in range(1, 6):
        run("git", "fetch", "--no-tags", "origin", "main")
        run("git", "reset", "--hard", "origin/main")
        current = load_version()
        requested = int(version)
        if requested < current:
            raise ValueError(f"Refusing version rollback: {requested} < {current}")
        manifest = pathlib.Path("latest_cn.json")
        if current == requested and manifest.is_file():
            existing = json.loads(manifest.read_text(encoding="utf-8"))
            if existing.get("url") == expected_url and existing.get("md5") == data["md5"]:
                print("Release state already published; no further commit")
                return

        manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        pathlib.Path("version.env").write_text(
            "# Last successfully published Via Safari versionCode (not the last detected official version)\n"
            f"VIA_VERSION_CODE={version}\n",
            encoding="utf-8",
        )
        run("git", "add", "latest_cn.json", "version.env")
        if run("git", "diff", "--cached", "--quiet", check=False).returncode == 0:
            print("No update required")
            return
        run("git", "commit", "-m", f"chore: publish Safari update {version}")
        push = run("git", "push", "origin", "HEAD:main", check=False)
        if push.returncode == 0:
            print(f"Published latest_cn.json and version.env={version}")
            return
        if "non-fast-forward" not in push.stderr and "fetch first" not in push.stderr:
            raise RuntimeError(f"git push failed: {push.stderr}")
        print(f"Concurrent push, refreshing main (attempt {attempt}/5)")
        time.sleep(min(attempt, 5))
    raise RuntimeError("Could not publish release state after 5 concurrent-update retries")


if __name__ == "__main__":
    main()
