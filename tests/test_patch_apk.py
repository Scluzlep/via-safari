"""Offline smoke test for APK resource/update patching with a decoded fixture."""
import pathlib
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
ANDROID = "http://schemas.android.com/apk/res/android"
NS = lambda key: f"{{{ANDROID}}}{key}"


class PatchApkTests(unittest.TestCase):
    def test_integer_version_code_and_launcher_branding(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp) / "decoded"
            (base / "smali" / "y8").mkdir(parents=True)
            (base / "res").mkdir()
            (base / "apktool.yml").write_text(
                "versionInfo:\n  versionCode: '20260822'\n  versionName: 7.3.2\n",
                encoding="utf-8",
            )
            (base / "smali" / "y8" / "h.smali").write_text(
                'const-string v0, "https://res.viayoo.com/v1/latest_cn.json"\n',
                encoding="utf-8",
            )
            (base / "AndroidManifest.xml").write_text(
                """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
          package="mark.via" android:versionCode="20260822">
  <application android:label="@string/app_name" android:icon="@mipmap/ic_launcher">
    <activity android:name=".MainActivity">
      <intent-filter>
        <action android:name="android.intent.action.MAIN" />
        <category android:name="android.intent.category.LAUNCHER" />
      </intent-filter>
    </activity>
  </application>
</manifest>
""",
                encoding="utf-8",
            )
            subprocess.run(
                [sys.executable, "scripts/patch_apk.py", "--decoded", str(base), "--version", "20260823"],
                cwd=ROOT, check=True, capture_output=True, text=True,
            )
            metadata = (base / "apktool.yml").read_text(encoding="utf-8")
            self.assertIn("versionCode: 20260823", metadata)
            self.assertNotIn("versionCode: '20260823'", metadata)
            manifest = ET.parse(base / "AndroidManifest.xml").getroot()
            self.assertEqual(manifest.get(NS("versionCode")), "20260823")
            app = manifest.find("application")
            self.assertEqual(app.get(NS("label")), "Safari")
            self.assertEqual(app.get(NS("icon")), "@drawable/safari_launcher")
            activity = app.find("activity")
            self.assertEqual(activity.get(NS("label")), "Safari")
            self.assertEqual(activity.get(NS("icon")), "@drawable/safari_launcher")
            self.assertTrue((base / "res" / "drawable-nodpi" / "safari_launcher.png").is_file())
            smali = (base / "smali" / "y8" / "h.smali").read_text(encoding="utf-8")
            self.assertIn("raw.githubusercontent.com/Scluzlep/via-safari/main/latest_cn.json", smali)
            self.assertNotIn("res.viayoo.com/v1/latest_cn.json", smali)


if __name__ == "__main__":
    unittest.main()
