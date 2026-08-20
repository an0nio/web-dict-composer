from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from web_dict_composer.core.artifacts import build_artifacts
from web_dict_composer.core.engine import compose, estimate_profile
from web_dict_composer.core.errors import ProfileError, SafetyLimitError
from web_dict_composer.core.profile import Profile, load_local_dictionary_file, load_profile
from web_dict_composer.core.resources import profile_files
from web_dict_composer.sources.manager import add_source


class EngineTests(unittest.TestCase):
    def test_every_active_profile_validates_and_stays_bounded(self) -> None:
        paths = profile_files()
        self.assertEqual(len(paths), 10)
        domains = set()
        for path in paths:
            profile = load_profile(path)
            domains.add(profile.domain)
            estimate = estimate_profile(profile)
            self.assertGreater(estimate.raw_combinations, 0, profile.id)
            self.assertLessEqual(estimate.expanded_upper_bound, estimate.max_outputs, profile.id)
            result = compose(profile)
            self.assertTrue(result.values, profile.id)
            self.assertFalse(result.truncated, profile.id)
        self.assertEqual(domains, {"file_upload", "lfi"})

    def test_quick_profile_has_deterministic_estimate_and_output(self) -> None:
        profile = load_profile("file_upload/php_jpg_quick")
        estimate = estimate_profile(profile)
        self.assertEqual(estimate.raw_combinations, 210)
        result = compose(profile)
        self.assertEqual(len(result.values), 210)
        self.assertEqual(result.values[0], "shell.php.jpg")
        self.assertIn("shell.php%00.jpg", result.values)

    def test_traversal_prefix_profile_repeats_atomic_steps(self) -> None:
        profile = load_profile("lfi/traversal_prefixes_1_8")
        result = compose(profile)
        self.assertEqual(len(result.values), 112)
        self.assertIn("../", result.values)
        self.assertIn("../../../../../../../../", result.values)
        self.assertIn("..%2f..%2f", result.values)

    def test_build_writes_exactly_wordlist_and_manifest(self) -> None:
        profile = load_profile("lfi/php_filter_source")
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "filters.txt"
            artifacts = build_artifacts(profile, output_override=output)
            self.assertTrue(artifacts.wordlist.is_file())
            self.assertTrue(artifacts.manifest.is_file())
            self.assertEqual(
                {path.name for path in Path(temporary).iterdir()},
                {"filters.txt", "filters.manifest.json"},
            )
            manifest = json.loads(artifacts.manifest.read_text(encoding="utf-8"))
            self.assertEqual(manifest["profile"], "lfi_php_filter_source")
            self.assertEqual(manifest["domain"], "lfi")
            self.assertEqual(manifest["sets"]["wrapper"], "lfi_php_filter_readonly")
            self.assertEqual(manifest["output_lines"], artifacts.lines)
            self.assertFalse(manifest["truncated"])

    def test_over_limit_profile_requires_force_and_remains_capped(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "large.yml"
            data = {
                "id": "large_test",
                "domain": "file_upload",
                "description": "Exercise the hard limit.",
                "sets": {
                    "left": {"inline": list(range(20))},
                    "right": {"inline": list(range(20))},
                },
                "patterns": ["{left}-{right}"],
                "filters": {"dedupe": True, "max_length": 20, "max_outputs": 10},
            }
            path.write_text(yaml.safe_dump(data), encoding="utf-8")
            profile = load_profile(path)
            with self.assertRaises(SafetyLimitError):
                compose(profile)
            result = compose(profile, force=True)
            self.assertEqual(len(result.values), 10)
            self.assertTrue(result.truncated)

    def test_external_wordlist_cannot_be_used_by_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "invalid-kind.yml"
            data = {
                "id": "invalid_kind",
                "domain": "file_upload",
                "description": "Invalid external input.",
                "sets": {"extensions": {"catalog": "seclists_web_extensions"}},
                "patterns": ["{extensions}"],
            }
            path.write_text(yaml.safe_dump(data), encoding="utf-8")
            with self.assertRaisesRegex(ProfileError, "external_wordlist"):
                load_profile(path)

    def test_wizard_profile_can_compose_a_resolved_external_wordlist(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            seclists = base / "SecLists"
            wordlist = seclists / "Discovery" / "Web-Content" / "web-extensions.txt"
            wordlist.parent.mkdir(parents=True)
            (seclists / "Fuzzing").mkdir()
            (seclists / "README.md").write_text("SecLists fixture\n", encoding="utf-8")
            wordlist.write_text("php\nhtml\n", encoding="utf-8")
            with patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(base / "config")},
                clear=False,
            ):
                add_source("seclists", seclists)
                profile = Profile(
                    path=Path("<wizard-test>"),
                    id="wizard_external_test",
                    domain="file_upload",
                    description="Wizard external wordlist fixture.",
                    sets_spec={
                        "extension": {"catalog": "seclists_web_extensions"},
                    },
                    patterns=["{extension}"],
                    filters={"max_outputs": 10},
                )
                result = compose(profile)

            self.assertEqual(result.values, ["php", "html"])

    def test_wizard_profile_can_read_an_explicit_file_outside_the_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "allowed_extensions.txt"
            path.write_text(".jpg\n.jpeg\n# ignored\n.jpg\n", encoding="utf-8")
            resolved, values = load_local_dictionary_file(path)
            profile = Profile(
                path=Path("<wizard-file-test>"),
                id="wizard_file_test",
                domain="file_upload",
                description="Wizard local file fixture.",
                sets_spec={"allowed_extensions": {"file": str(resolved)}},
                patterns=["{allowed_extensions}"],
                runtime_files={"allowed_extensions": resolved},
            )
            result = compose(profile)

            self.assertEqual(values, (".jpg", ".jpeg", ".jpg"))
            self.assertEqual(result.values, [".jpg", ".jpeg"])
            self.assertEqual(result.sets["allowed_extensions"].source, str(resolved))

    def test_saved_yaml_profile_still_cannot_read_an_absolute_external_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            dictionary = base / "outside.txt"
            dictionary.write_text("value\n", encoding="utf-8")
            profile_path = base / "outside-profile.yml"
            profile_path.write_text(
                yaml.safe_dump(
                    {
                        "id": "outside_file_test",
                        "domain": "file_upload",
                        "description": "External path guard fixture.",
                        "sets": {"value": {"file": str(dictionary)}},
                        "patterns": ["{value}"],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ProfileError, "escapes the project root"):
                load_profile(profile_path)

    def test_unknown_placeholder_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "invalid.yml"
            data = {
                "id": "invalid_test",
                "domain": "lfi",
                "description": "Invalid on purpose.",
                "sets": {"known": {"inline": ["one"]}},
                "patterns": ["{unknown}"],
            }
            path.write_text(yaml.safe_dump(data), encoding="utf-8")
            with self.assertRaises(ProfileError):
                load_profile(path)

    def test_unsupported_profile_metadata_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "unsupported.yml"
            data = {
                "id": "unsupported_test",
                "domain": "file_upload",
                "description": "Unsupported schema on purpose.",
                "sets": {"value": {"inline": ["one"]}},
                "patterns": ["{value}"],
                "unexpected": ["Not part of the schema."],
            }
            path.write_text(yaml.safe_dump(data), encoding="utf-8")
            with self.assertRaisesRegex(ProfileError, "unsupported fields"):
                load_profile(path)


if __name__ == "__main__":
    unittest.main()
