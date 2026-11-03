#!/usr/bin/env python3
"""Create the exact update manifest only after a signed APK exists."""
import hashlib
import json
import os
import pathlib
import sys

def main():
    version = str(sys.argv[1])
    apk = pathlib.Path(sys.argv[2])
    source = json.loads(pathlib.Path("work/upstream.json").read_text(encoding="utf-8"))
    if str(source.get("version")) != version:
        raise ValueError("version mismatch between check and build")
    data = dict(source)
    data["url"] = f"https://github.com/Scluzlep/via-safari/releases/download/via-{version}/Safari.apk"
    data["md5"] = hashlib.md5(apk.read_bytes()).hexdigest()
    if "sha256" in data:
        data["sha256"] = hashlib.sha256(apk.read_bytes()).hexdigest()
    if "size" in data and isinstance(data["size"], int):
        data["size"] = apk.stat().st_size
    pathlib.Path("latest_cn.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"New update manifest: {data['url']} | MD5 {data['md5']}")

if __name__ == "__main__":
    main()
