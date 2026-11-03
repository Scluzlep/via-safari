"""Tests for version inspection when Apktool removes code from decoded Manifest."""
import pathlib
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from verify_upstream import read_apktool_version, verify


class UpstreamVersionTests(unittest.TestCase):
    def test_quoted_and_unquoted_version(self):
        self.assertEqual(read_apktool_version("versionInfo:\n  versionCode: '20260823'\n"), 20260823)
        self.assertEqual(read_apktool_version("versionInfo:\n  versionCode: 20260823\n"), 20260823)

    def test_manifest_without_version_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            (base / "AndroidManifest.xml").write_text(
                '<?xml version="1.0"?><manifest package="mark.via" />',
                encoding="utf-8",
            )
            (base / "apktool.yml").write_text(
                'versionInfo:\n  versionCode: 20260823\n  versionName: 7.3.3\n',
                encoding="utf-8",
            )
            verify(base, 20260823)
            with self.assertRaises(ValueError):
                verify(base, 20260824)

    def test_bad_metadata_fails_closed(self):
        with self.assertRaises(ValueError):
            read_apktool_version("versionInfo:\n  versionName: 7.3.3\n")
        with self.assertRaises(ValueError):
            read_apktool_version("versionCode: 20260823\nversionCode: 20260823\n")


if __name__ == "__main__":
    unittest.main()
