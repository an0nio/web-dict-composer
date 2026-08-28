from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from web_dict_composer.catalog.service import get_entry
from web_dict_composer.cli.app import (
    _choose_runtime_inputs,
    _configure_file_upload_request_paths,
    _filter_catalog_entries,
    _interactive_catalog_search,
    _optional_number_selection,
    _parse_number_selection,
    _pattern_options,
    _prepare_wizard_entry,
    _preview_wizard_entry,
    _remaining_tags,
    _replacement_candidates,
    _select_catalog_selector,
    _wizard_entry_target,
    _wizard_entries,
    console,
)
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
        self.assertIn("guided", help_result.stdout)

        profile_help = self.run_cli("profiles", "--help")
        self.assertIn("estimate", profile_help.stdout)
        self.assertIn("build", profile_help.stdout)

    def test_dictionary_search_prints_schema_and_description(self) -> None:
        result = self.run_cli("dicts", "search", "file-upload", "content-type")
        self.assertEqual(result.returncode, 0, result.stderr)
        for heading in ("ID", "Kind", "Source", "Path", "Tags", "Description"):
            self.assertIn(heading, result.stdout)
        self.assertIn("file_upload_content_types_common", result.stdout)
        self.assertIn("Small curated set of", result.stdout)
        self.assertIn("upload-relevant media types.", result.stdout)
        self.assertIn("file-upload, mime, content-type", result.stdout)
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

    def test_guided_replacements_follow_set_semantics(self) -> None:
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

    def test_guided_catalog_selector_accepts_multiple_entries_and_preview(self) -> None:
        profile = load_profile("file_upload/handler_against_allowlist")
        with patch(
            "web_dict_composer.cli.app.Prompt.ask",
            side_effect=[":show 2", "1,3"],
        ), patch(
            "web_dict_composer.cli.app._preview_wizard_entry",
            return_value=True,
        ) as preview:
            with console.capture() as capture:
                selected = _select_catalog_selector(profile, "dangerous")

        self.assertEqual(
            selected,
            (
                "file_upload_php_handler_candidates",
                "file_upload_aspnet_handler_candidates",
            ),
        )
        self.assertEqual(
            profile.sets_spec["dangerous"],
            {
                "catalogs": [
                    "file_upload_php_handler_candidates",
                    "file_upload_aspnet_handler_candidates",
                ]
            },
        )
        preview.assert_called_once_with(get_entry("file_upload_php_legacy_candidates"))
        self.assertIn("Selected for dangerous", capture.get())

    def test_guided_request_path_transform_resolves_best_effort_options(self) -> None:
        spec: dict[str, object] = {
            "name": "file_upload_request_path_variants",
            "guided": True,
        }
        with patch(
            "web_dict_composer.cli.app.IntPrompt.ask",
            side_effect=[2, 1, 3, 255],
        ), patch(
            "web_dict_composer.cli.app.Prompt.ask",
            side_effect=["1,3,5-7", "jpg, webp"],
        ):
            with console.capture():
                _configure_file_upload_request_paths(spec)

        self.assertEqual(spec["source"], "accepted")
        self.assertEqual(spec["target"], "segment")
        self.assertEqual(
            spec["presets"],
            [
                "common_web",
                "windows",
                "extension_rewrite",
                "collision_suffixes",
                "length_limit",
            ],
        )
        self.assertEqual(spec["forced_extensions"], ["jpg", "webp"])
        self.assertEqual(spec["collision_suffix_limit"], 3)
        self.assertEqual(spec["filename_max_bytes"], 255)
        self.assertNotIn("guided", spec)
        self.assertEqual(_optional_number_selection("none", 7), [])

    def test_guided_runtime_input_can_resolve_a_local_dictionary(self) -> None:
        profile = load_profile("file_upload/request_path_variants")
        dictionary = Path("/tmp/accepted-filenames.txt")
        with patch(
            "web_dict_composer.cli.app.IntPrompt.ask",
            return_value=1,
        ), patch(
            "web_dict_composer.cli.app._wizard_local_file",
            return_value=(dictionary, ("shell.php.jpg",)),
        ):
            with console.capture():
                _choose_runtime_inputs(profile)

        self.assertEqual(profile.runtime_files["filename"], dictionary)
        self.assertEqual(profile.sets_spec["filename"], {"file": str(dictionary)})

    def test_wizard_filters_dictionaries_by_accumulated_terms(self) -> None:
        entries = _wizard_entries()
        matches = _filter_catalog_entries(
            entries,
            ["file-upload", "dangerous", "php"],
        )
        self.assertEqual(
            {entry.id for entry in matches},
            {
                "file_upload_php_handler_candidates",
                "file_upload_php_legacy_candidates",
                "file_upload_php_source_candidates",
            },
        )
        self.assertNotIn("file-upload", _remaining_tags(matches[0], ["file-upload"]))

    def test_wizard_includes_external_wordlists_but_never_references(self) -> None:
        entries = _wizard_entries("file_upload")
        kinds = {entry.kind for entry in entries}
        ids = {entry.id for entry in entries}
        self.assertIn("external_wordlist", kinds)
        self.assertIn("seclists_web_all_content_types", ids)
        self.assertNotIn("reference", kinds)
        self.assertNotIn("owasp_file_upload_testing", ids)
        self.assertNotIn("file_upload_php_execution_markers_reference", ids)

    def test_wizard_finds_unregistered_seclists_when_external_is_selected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            seclists = base / "SecLists"
            target = seclists / "Discovery" / "Web-Content" / "web-extensions.txt"
            target.parent.mkdir(parents=True)
            (seclists / "Fuzzing").mkdir()
            (seclists / "README.md").write_text("SecLists fixture\n", encoding="utf-8")
            target.write_text("php\nhtml\n", encoding="utf-8")
            environment = {
                "SECLISTS_PATH": str(seclists),
                "XDG_CONFIG_HOME": str(base / "config"),
            }
            with patch.dict(os.environ, environment, clear=False):
                self.assertTrue(_prepare_wizard_entry(get_entry("seclists_web_extensions")))

    def test_wizard_can_preview_by_number_or_id_without_selecting(self) -> None:
        entry = get_entry("file_upload_allowed_image_extensions")
        pool = _wizard_entries("file_upload")
        self.assertEqual(_wizard_entry_target("1", pool, [entry]), entry)
        self.assertEqual(_wizard_entry_target(entry.id, pool, []), entry)

        with patch("web_dict_composer.cli.app.pydoc.pager") as mocked_pager:
            with console.capture() as capture:
                self.assertTrue(_preview_wizard_entry(entry))
        output = capture.get()
        mocked_pager.assert_called_once()
        pager_content = mocked_pager.call_args.args[0]
        self.assertIn("Dictionary: file_upload_allowed_image_extensions", pager_content)
        self.assertIn("Usable entries: 6", pager_content)
        self.assertIn("Navigation:", pager_content)
        self.assertIn(".jpg", pager_content)
        self.assertIn(".avif", pager_content)
        self.assertIn("Pager closed; the dictionary has not been selected.", output)

    def test_parameterless_search_requires_a_terminal_in_scripts(self) -> None:
        result = self.run_cli("dicts", "search")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Interactive search needs a terminal", result.stderr)

    def test_interactive_search_accumulates_tags_and_searches_exact_names(self) -> None:
        with patch(
            "web_dict_composer.cli.app.Prompt.ask",
            side_effect=["file-upload", "content-type", ":quit"],
        ):
            with console.capture() as capture:
                self.assertEqual(
                    _interactive_catalog_search(limit=50, include_references=False),
                    0,
                )
        tag_output = capture.get()
        self.assertIn("Active filters: file-upload + content-type", tag_output)
        self.assertIn("file_upload_content_types_common", tag_output)
        self.assertIn("seclists_web_all_content_types", tag_output)

        with patch(
            "web_dict_composer.cli.app.Prompt.ask",
            side_effect=["Common allowed image extensions", ":quit"],
        ):
            with console.capture() as capture:
                self.assertEqual(
                    _interactive_catalog_search(limit=50, include_references=False),
                    0,
                )
        name_output = capture.get()
        self.assertIn("file_upload_allowed_image_extensions", name_output)
        self.assertNotIn("owasp_file_upload_testing", name_output)

    def test_wizard_generates_orderings_and_parses_friendly_selection(self) -> None:
        aliases = ["base", "dangerous", "allowed"]
        patterns = _pattern_options(aliases)
        self.assertEqual(len(patterns), 6)
        self.assertIn("{base}{dangerous}{allowed}", patterns)
        self.assertIn("{base}{allowed}{dangerous}", patterns)
        self.assertEqual(_parse_number_selection("1,3-4,3", 6), [0, 2, 3])
        self.assertEqual(_parse_number_selection("all", 3), [0, 1, 2])

        subset_patterns = _pattern_options(aliases, include_subsets=True)
        self.assertEqual(len(subset_patterns), 12)
        self.assertIn("{dangerous}{allowed}", subset_patterns)


if __name__ == "__main__":
    unittest.main()
