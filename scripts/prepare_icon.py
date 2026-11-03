#!/usr/bin/env python3
"""Prefer the full-resolution Safari 26 icon; keep the checked-in extraction as fallback."""
import pathlib
import struct
import urllib.request

URL = "https://theapplewiki.com/images/applewiki/b/b0/Safari_26_icon.png"
FALLBACK = pathlib.Path("assets/safari26.png")

def main():
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "Via-Safari-Updater/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            content = resp.read(5 * 1024 * 1024 + 1)
        if len(content) > 5 * 1024 * 1024 or content[:8] != bytes.fromhex("89504e470d0a1a0a"):
            raise ValueError("Unexpected PNG response")
        width, height = struct.unpack(">II", content[16:24])
        if (width, height) != (1024, 1024):
            raise ValueError(f"Unexpected icon resolution {width}x{height}")
        FALLBACK.write_bytes(content)
        print("Using full-resolution 1024x1024 Safari 26 icon")
    except Exception as exc:
        print(f"Original icon unavailable: {exc}; using repository bundled fallback")
        if not FALLBACK.exists():
            raise

if __name__ == "__main__":
    main()
