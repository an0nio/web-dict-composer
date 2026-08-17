from __future__ import annotations

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

    def test_local_path_and_reference_url_resolve(self) -> None:
        local = resolve_entry(get_entry("file_upload_php_handler_candidates"))
        reference = resolve_entry(get_entry("owasp_file_upload_testing"))
        self.assertTrue(local and local.endswith("extensions/php_handler_candidates.txt"))
        self.assertTrue(reference and reference.startswith("https://owasp.org/"))

    def test_every_local_catalog_set_has_a_review_record(self) -> None:
        review_root = Path(__file__).resolve().parents[1] / "docs" / "set_reviews"
        reviewed = {path.stem for path in review_root.glob("*.md")}
        local_ids = {entry.id for entry in load_catalog() if entry.source == "local"}
        self.assertTrue(local_ids.issubset(reviewed))


if __name__ == "__main__":
    unittest.main()
