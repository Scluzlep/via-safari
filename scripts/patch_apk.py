#!/usr/bin/env python3
"""Patch decoded Apktool files without assuming stable obfuscated class names."""
import argparse
import pathlib
import re
import shutil
import xml.etree.ElementTree as ET

OLD_URL = "https://res.viayoo.com/v1/latest_cn.json"
NEW_URL = "https://raw.githubusercontent.com/Scluzlep/via-safari/main/latest_cn.json"
ANDROID_NS = "http://schemas.android.com/apk/res/android"
A = lambda name: f"{{{ANDROID_NS}}}{name}"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decoded", type=pathlib.Path, required=True)
    parser.add_argument("--version", type=int, required=True)
    args = parser.parse_args()
    base = args.decoded
    if not (1 <= args.version < 2147483648):
        raise ValueError("Invalid versionCode")
    manifest = base / "AndroidManifest.xml"
    ET.register_namespace("android", ANDROID_NS)
    tree = ET.parse(manifest)
    root = tree.getroot()
    if root.get("package") != "mark.via":
        raise ValueError(f"Incorrect package: {root.get('package')}")
    root.set(A("versionCode"), str(args.version))
    app = root.find("application")
    if app is None:
        raise ValueError("Missing application entry")
    app.set(A("label"), "Safari")
    app.set(A("icon"), "@drawable/safari_launcher")
    app.set(A("roundIcon"), "@drawable/safari_launcher")

    launchers = 0
    for entry in app:
        if entry.tag not in ("activity", "activity-alias"):
            continue
        for intent in entry.findall("intent-filter"):
            has_main = any(x.get(A("name")) == "android.intent.action.MAIN" for x in intent.findall("action"))
            has_launcher = any(x.get(A("name")) == "android.intent.category.LAUNCHER" for x in intent.findall("category"))
            if has_main and has_launcher:
                entry.set(A("label"), "Safari")
                entry.set(A("icon"), "@drawable/safari_launcher")
                entry.set(A("roundIcon"), "@drawable/safari_launcher")
                launchers += 1
    if launchers < 1:
        raise ValueError("No launcher entry found; refuse to publish")
    tree.write(manifest, encoding="utf-8", xml_declaration=True)

    source = pathlib.Path("assets/safari26.png")
    if source.read_bytes()[:8] != b"\\x89PNG\\r\\n\\x1a\\n":
        raise ValueError("Source icon is not PNG")
    target_dir = base / "res" / "drawable-nodpi"
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target_dir / "safari_launcher.png")

    yaml = base / "apktool.yml"
    y = yaml.read_text(encoding="utf-8")
    y, num = re.subn(r"(?m)^(\s*versionCode:)\s*.*$", lambda m: m.group(1) + f" '{args.version}'", y)
    if num != 1:
        raise ValueError("apktool.yml versionCode not found or ambiguous")
    yaml.write_text(y, encoding="utf-8")

    patched = []
    for file in base.rglob("*.smali"):
        content = file.read_text(encoding="utf-8")
        if OLD_URL not in content:
            continue
        count = content.count(OLD_URL)
        file.write_text(content.replace(OLD_URL, NEW_URL), encoding="utf-8")
        patched.append((str(file), count))
    if sum(count for _, count in patched) != 1:
        raise ValueError(f"Expected one official update URL in smali; found: {patched}")
    print(f"Launcher entries: {launchers}; URL replacement: {patched}; versionCode={args.version}")

if __name__ == "__main__":
    main()
