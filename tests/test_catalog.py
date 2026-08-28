from __future__ import annotations

import base64
import re
import unittest
from dataclasses import fields
from pathlib import Path

from web_dict_composer.catalog.service import (
    ALLOWED_KINDS,
    get_entry,
    load_catalog,
    resolve_entry,
    search_catalog,
)


class CatalogTests(unittest.TestCase):
    def _catalog_values(self, dictionary_id: str) -> list[str]:
        resolved = resolve_entry(get_entry(dictionary_id))
        self.assertIsNotNone(resolved)
        return Path(str(resolved)).read_text(encoding="utf-8").splitlines()

    def test_catalog_has_unique_entries_and_simplified_schema(self) -> None:
        entries = load_catalog()
        self.assertGreaterEqual(len(entries), 30)
        self.assertEqual(len(entries), len({entry.id for entry in entries}))
        self.assertEqual({entry.domain for entry in entries}, {"file_upload", "lfi"})
        self.assertTrue({entry.kind for entry in entries}.issubset(ALLOWED_KINDS))
        self.assertEqual(
            {field.name for field in fields(entries[0])},
            {"id", "name", "domain", "kind", "source", "path", "tags", "description"},
        )

    def test_precise_search_avoids_unrelated_references(self) -> None:
        results = search_catalog("file-upload content-type")
        ids = {entry.id for entry in results}
        self.assertIn("file_upload_content_types_common", ids)
        self.assertIn("seclists_web_all_content_types", ids)
        self.assertNotIn("patt_upload_insecure_files", ids)

    def test_original_dangerous_php_extension_query_is_supported(self) -> None:
        results = search_catalog("dangerous php ext")
        ids = {entry.id for entry in results}
        self.assertIn("file_upload_php_handler_candidates", ids)
        self.assertTrue(all(entry.kind != "reference" for entry in results))

    def test_references_require_explicit_search_flag(self) -> None:
        query = "file-upload php extensions"
        default_ids = {entry.id for entry in search_catalog(query)}
        reference_ids = {
            entry.id for entry in search_catalog(query, include_references=True)
        }
        self.assertNotIn("patt_upload_insecure_files", default_ids)
        self.assertIn("patt_upload_insecure_files", reference_ids)

    def test_magic_number_and_shell_resources_are_reference_only(self) -> None:
        reference_ids = {
            "file_upload_magic_numbers_reference",
            "file_magic_database_reference",
            "file_upload_shell_resources_reference",
            "file_upload_php_execution_markers_reference",
            "seclists_web_shells_reference",
            "pentestmonkey_php_reverse_shell_reference",
            "phpbash_web_shell_reference",
        }
        for dictionary_id in reference_ids:
            self.assertEqual(get_entry(dictionary_id).kind, "reference")

        default_ids = {
            entry.id for entry in search_catalog("file-upload magic numbers")
        }
        magic_reference_ids = {
            entry.id
            for entry in search_catalog(
                "file-upload magic numbers", include_references=True
            )
        }
        webshell_reference_ids = {
            entry.id
            for entry in search_catalog(
                "file-upload webshells", include_references=True
            )
        }
        reverse_shell_reference_ids = {
            entry.id
            for entry in search_catalog(
                "file-upload revshells", include_references=True
            )
        }
        all_shell_reference_ids = {
            entry.id
            for entry in search_catalog(
                "file-upload shell-resources", include_references=True
            )
        }
        self.assertFalse(default_ids & reference_ids)
        self.assertIn("file_upload_magic_numbers_reference", magic_reference_ids)
        self.assertIn("file_magic_database_reference", magic_reference_ids)
        self.assertTrue(
            {
                "file_upload_shell_resources_reference",
                "seclists_web_shells_reference",
                "phpbash_web_shell_reference",
            }.issubset(webshell_reference_ids)
        )
        self.assertTrue(
            {
                "file_upload_shell_resources_reference",
                "pentestmonkey_php_reverse_shell_reference",
            }.issubset(reverse_shell_reference_ids)
        )
        self.assertTrue(
            {
                "file_upload_shell_resources_reference",
                "seclists_web_shells_reference",
                "pentestmonkey_php_reverse_shell_reference",
                "phpbash_web_shell_reference",
            }.issubset(all_shell_reference_ids)
        )

    def test_magic_number_reference_has_exact_copy_paste_signature_commands(self) -> None:
        resolved = resolve_entry(get_entry("file_upload_magic_numbers_reference"))
        self.assertIsNotNone(resolved)
        reference = Path(str(resolved)).read_text(encoding="utf-8")
        commands = dict(
            re.findall(r"^printf '([^']+)' > (signature-[^\n]+)$", reference, re.MULTILINE)
        )
        expected = {
            "signature-jpeg.jpg": "FF D8 FF",
            "signature-png.png": "89 50 4E 47 0D 0A 1A 0A",
            "signature-gif87a.gif": "47 49 46 38 37 61",
            "signature-gif89a.gif": "47 49 46 38 39 61",
            "signature-pdf.pdf": "25 50 44 46 2D",
            "signature-zip.zip": "50 4B 03 04",
            "signature-gzip.gz": "1F 8B 08",
            "signature-bmp.bmp": "42 4D",
            "signature-tiff-le.tiff": "49 49 2A 00",
            "signature-tiff-be.tiff": "4D 4D 00 2A",
            "signature-webp.webp": "52 49 46 46 00 00 00 00 57 45 42 50",
            "signature-ole.bin": "D0 CF 11 E0 A1 B1 1A E1",
            "signature-elf.bin": "7F 45 4C 46",
            "signature-pe.exe": "4D 5A",
        }
        self.assertEqual(set(commands.values()), set(expected))
        for escaped, filename in commands.items():
            actual = bytes(escaped, "ascii").decode("unicode_escape").encode("latin-1")
            self.assertEqual(actual, bytes.fromhex(expected[filename]))

        self.assertIn(
            "cat -- fixtures/file_upload/php/php_execution_marker.php "
            ">> signature-gif89a.gif",
            reference,
        )
        for advanced in ("base64 --decode", "python3 - <<", "zlib.crc32", "tEXt"):
            self.assertNotIn(advanced, reference)

    def test_local_path_and_reference_url_resolve(self) -> None:
        local = resolve_entry(get_entry("file_upload_php_handler_candidates"))
        reference = resolve_entry(get_entry("owasp_file_upload_testing"))
        self.assertTrue(local and local.endswith("extensions/php_handler_candidates.txt"))
        self.assertTrue(reference and reference.startswith("https://owasp.org/"))

        for dictionary_id in (
            "file_upload_magic_numbers_reference",
            "file_upload_shell_resources_reference",
            "file_upload_php_execution_markers_reference",
        ):
            resolved = resolve_entry(get_entry(dictionary_id))
            self.assertTrue(resolved and Path(resolved).is_file())

    def test_php_execution_markers_are_stable_non_composable_fixtures(self) -> None:
        entry = get_entry("file_upload_php_execution_markers_reference")
        self.assertEqual(entry.kind, "reference")

        default_ids = {entry.id for entry in search_catalog("php marker ffuf")}
        reference_ids = {
            entry.id
            for entry in search_catalog("php marker ffuf", include_references=True)
        }
        self.assertNotIn("file_upload_php_execution_markers_reference", default_ids)
        self.assertIn("file_upload_php_execution_markers_reference", reference_ids)

        root = Path(__file__).resolve().parents[1]
        fixture_root = root / "fixtures" / "file_upload" / "php"
        minimal = fixture_root / "php_execution_marker.php"
        diagnostic = fixture_root / "php_execution_and_path_marker.php"
        for fixture in (minimal, diagnostic):
            source = fixture.read_text(encoding="utf-8")
            self.assertNotIn("php_funciona", source)
            encoded = re.search(r'base64_decode\("([A-Za-z0-9+/=]+)"\)', source)
            self.assertIsNotNone(encoded)
            self.assertEqual(
                base64.b64decode(encoded.group(1)).decode("ascii"),
                "php_funciona",
            )

        diagnostic_source = diagnostic.read_text(encoding="utf-8")
        for label in (
            "basename_hex=",
            "file_hex=",
            "realpath_hex=",
            "script_filename_hex=",
            "document_root_hex=",
            "request_uri=",
        ):
            self.assertIn(label, diagnostic_source)

    def test_every_local_catalog_resource_has_a_review_record(self) -> None:
        review_root = Path(__file__).resolve().parents[1] / "docs" / "set_reviews"
        reviewed = {path.stem for path in review_root.glob("*.md")}
        local_ids = {entry.id for entry in load_catalog() if entry.source == "local"}
        self.assertTrue(local_ids.issubset(reviewed))

    def test_broad_aggregate_sets_cover_the_reviewed_narrow_sets(self) -> None:
        for dictionary_id in (
            "file_upload_filename_all_separators",
            "lfi_traversal_steps_all_linux",
            "lfi_traversal_steps_all_windows",
        ):
            self.assertEqual(get_entry(dictionary_id).kind, "derived_set")

        separators = self._catalog_values("file_upload_filename_all_separators")
        basic = self._catalog_values("file_upload_filename_separators_basic")
        encoded = self._catalog_values("file_upload_filename_separators_encoded")
        self.assertEqual(len(separators), len(set(separators)))
        self.assertEqual(
            set(separators),
            {*basic, *encoded, "/", ".\\", "...", "…"},
        )

        unix = self._catalog_values("lfi_traversal_steps_unix")
        windows = self._catalog_values("lfi_traversal_steps_windows")
        traversal_encoded = self._catalog_values("lfi_traversal_steps_encoded")
        double_encoded = self._catalog_values("lfi_traversal_steps_double_encoded")
        filter_bypass = self._catalog_values("lfi_traversal_steps_filter_bypass")
        all_reviewed = {
            *unix,
            *windows,
            *traversal_encoded,
            *double_encoded,
            *filter_bypass,
        }
        linux_reviewed = {
            *unix,
            *(
                value
                for value in (*traversal_encoded, *double_encoded)
                if value.casefold().endswith(("%2f", "%252f"))
            ),
            *(value for value in filter_bypass if value.endswith("/")),
        }
        jhaddix_linux = {
            ".../",
            "..//",
            "....\\/",
            "..%2F",
            "%2e%2e/",
            "%c0%ae%c0%ae/",
            "..%c0%af",
            "..2f",
            ".\\\\./",
            "%e2%80%a5%ef%bc%8f",
            "..%ef%bc%8f",
            "Li4v",
        }
        jhaddix_windows = {
            "%25%5c..",
            "….." + "\\" * 3,
            "%e2%80%a5%ef%b9%a8",
            "..%ef%b9%a8",
            "..%ef%bc%bc",
        }
        all_linux = self._catalog_values("lfi_traversal_steps_all_linux")
        all_windows = self._catalog_values("lfi_traversal_steps_all_windows")

        self.assertEqual(len(all_linux), len(set(all_linux)))
        self.assertEqual(len(all_windows), len(set(all_windows)))
        self.assertEqual(len(all_linux), 21)
        self.assertEqual(len(all_windows), 35)
        self.assertEqual(set(all_linux), linux_reviewed | jhaddix_linux)
        self.assertEqual(
            set(all_windows),
            all_reviewed | set(all_linux) | jhaddix_windows,
        )

        linux_search = {
            entry.id for entry in search_catalog("linux traversal all mass-fuzzing")
        }
        self.assertIn("lfi_traversal_steps_all_linux", linux_search)
        advanced_search = {
            entry.id for entry in search_catalog("linux base64 overlong-utf8 jhaddix")
        }
        self.assertIn("lfi_traversal_steps_all_linux", advanced_search)

    def test_generated_target_variant_matrices_are_complete(self) -> None:
        forward_separators = (
            "/",
            "//",
            "\\/",
            "%2f",
            "%2F",
            "%252f",
            "%252F",
            "%c0%af",
            "2f",
            "%ef%bc%8f",
            "／",
        )
        backslash_separators = (
            "\\",
            "\\\\",
            "%5c",
            "%5C",
            "%255c",
            "%255C",
            "%c1%9c",
            "5c",
            "%ef%b9%a8",
            "﹨",
            "%ef%bc%bc",
            "＼",
        )
        dots = (
            ".",
            "%2e",
            "%2E",
            "%252e",
            "%252E",
            "%c0%ae",
            "2e",
            "%e2%80%a4",
            "․",
            "%ef%bc%8e",
            "．",
        )
        expected = {
            "lfi_linux_passwd_separator_variants": [
                f"etc{separator}passwd" for separator in forward_separators
            ],
            "lfi_windows_win_ini_separator_dot_variants": [
                f"Windows{separator}win{dot}ini"
                for separator in (*forward_separators, *backslash_separators)
                for dot in dots
            ],
            "lfi_php_index_dot_variants": [f"index{dot}php" for dot in dots],
        }

        for dictionary_id, expected_values in expected.items():
            self.assertEqual(get_entry(dictionary_id).kind, "generated_set")
            actual = self._catalog_values(dictionary_id)
            self.assertEqual(actual, expected_values)
            self.assertEqual(len(actual), len(set(actual)))

        search_ids = {
            entry.id for entry in search_catalog("windows win-ini cartesian dots")
        }
        self.assertIn("lfi_windows_win_ini_separator_dot_variants", search_ids)


if __name__ == "__main__":
    unittest.main()
