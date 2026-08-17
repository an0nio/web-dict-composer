from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from web_dict_composer.cli.app import _replacement_candidates
from web_dict_composer.core.profile import load_profile


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(ROOT)
        environment["NO_COLOR"] = "1"
        environment["COLUMNS"] = "180"
        return subprocess.run(
            [sys.executable, "-m", "web_dict_composer", *arguments],
            cwd=ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_help_and_version_expose_reduced_cli(self) -> None:
        version = self.run_cli("--version")
        self.assertEqual(version.returncode, 0)
        self.assertIn("web-dict-composer 0.3.0", version.stdout)

        help_result = self.run_cli("--help")
        self.assertEqual(help_result.returncode, 0)
        self.assertIn("dicts", help_result.stdout)
        self.assertIn("profiles", help_result.stdout)
        self.assertIn("wizard", help_result.stdout)

        profile_help = self.run_cli("profiles", "--help")
        self.assertIn("estimate", profile_help.stdout)
        self.assertIn("build", profile_help.stdout)

    def test_dictionary_search_prints_schema_and_description(self) -> None:
        result = self.run_cli("dicts", "search", "file-upload", "content-type")
        self.assertEqual(result.returncode, 0, result.stderr)
        for heading in ("ID", "Kind", "Source", "Path", "Description"):
            self.assertIn(heading, result.stdout)
        self.assertIn("file_upload_content_types_common", result.stdout)
        self.assertIn("Small curated set of upload-relevant media types.", result.stdout)
        self.assertNotIn("PayloadsAllTheThings", result.stdout)

    def test_nested_estimate_json_is_valid(self) -> None:
        result = self.run_cli("profiles", "estimate", "lfi/linux_basic", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"profile": "lfi_linux_basic"', result.stdout)
        self.assertIn('"domain": "lfi"', result.stdout)

    def test_full_profile_id_is_resolved(self) -> None:
        result = self.run_cli(
            "profiles", "estimate", "lfi_traversal_prefixes_1_8", "--json"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"profile": "lfi_traversal_prefixes_1_8"', result.stdout)

    def test_profile_build_writes_wordlist_and_manifest_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "prefixes.txt"
            result = self.run_cli(
                "profiles",
                "build",
                "lfi/traversal_prefixes_1_8",
                "--output",
                str(output),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output.is_file())
            manifest = Path(temporary) / "prefixes.manifest.json"
            self.assertTrue(manifest.is_file())
            self.assertEqual(
                {path.name for path in Path(temporary).iterdir()},
                {"prefixes.txt", "prefixes.manifest.json"},
            )
            self.assertIn("../../", output.read_text(encoding="utf-8"))

    def test_wizard_replacements_follow_set_semantics(self) -> None:
        profile = load_profile("file_upload/php_jpg_quick")
        allowed = {
            entry.id for entry in _replacement_candidates(profile, "allowed")
        }
        self.assertEqual(
            allowed,
            {
                "file_upload_allowed_image_extensions",
                "file_upload_allowed_document_extensions",
                "file_upload_allowed_archive_extensions",
            },
        )
        self.assertNotIn("file_upload_filename_bases_common", allowed)


if __name__ == "__main__":
    unittest.main()
