#!/usr/bin/env python3
"""Download original CN APK from the download link advertised on Via's official homepage."""
import hashlib
import json
import pathlib
import re
import urllib.request

URL = "https://res.viayoo.com/v1/via-release-cn.apk"
OUT = pathlib.Path("work/upstream.apk")

def main():
    upstream = json.loads(pathlib.Path("work/upstream.json").read_text(encoding="utf-8"))
    req = urllib.request.Request(URL, headers={"User-Agent": "Via-Safari-Updater/1.0"})
    OUT.parent.mkdir(exist_ok=True, parents=True)
    with urllib.request.urlopen(req, timeout=90) as response, OUT.open("wb") as f:
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            f.write(block)
            if f.tell() > 40 * 1024 * 1024:
                raise ValueError("APK exceeds sanity limit")
    content = OUT.read_bytes()
    if not content.startswith(b"PK\x03\x04"):
        raise ValueError("Downloaded object is not a ZIP/APK")
    md5 = hashlib.md5(content).hexdigest()
    expected = upstream.get("md5")
    if isinstance(expected, str) and re.fullmatch(r"[0-9a-fA-F]{32}", expected):
        if expected.lower() != md5:
            raise ValueError(f"Original APK MD5 does not match upstream manifest: {md5} != {expected}")
    print(f"Official APK: {len(content)} bytes, MD5={md5}")

if __name__ == "__main__":
    main()
