from __future__ import annotations

import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from web_dict_composer.catalog.service import CatalogEntry
from web_dict_composer.core.errors import SourceError
from web_dict_composer.sources.external import (
    cached_external_wordlist,
    download_external_wordlist,
)
from web_dict_composer.sources.manager import (
    add_source,
    load_sources,
    looks_like_seclists,
    scan_seclists,
)


class FakeResponse:
    def __init__(self, content: bytes) -> None:
        self.stream = BytesIO(content)
        self.headers = {
            "Content-Length": str(len(content)),
            "Content-Type": "text/plain; charset=utf-8",
        }

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def geturl(self) -> str:
        return "https://example.test/wordlist.txt"

    def read(self, size: int = -1) -> bytes:
        return self.stream.read(size)


class SourceTests(unittest.TestCase):
    def _make_seclists(self, parent: Path) -> Path:
        root = parent / "sEcLiStS"
        (root / "Discovery" / "Web-Content").mkdir(parents=True)
        (root / "Fuzzing" / "LFI").mkdir(parents=True)
        (root / "README.md").write_text("SecLists fixture\n", encoding="utf-8")
        (root / "Discovery" / "Web-Content" / "web-extensions.txt").write_text(
            "php\nhtml\n", encoding="utf-8"
        )
        (root / "Fuzzing" / "LFI" / "LFI-test.txt").write_text(
            "../etc/passwd\n", encoding="utf-8"
        )
        return root

    def test_scan_and_register_case_insensitive_seclists_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source_root = self._make_seclists(base)
            environment = {
                "SECLISTS_PATH": str(source_root),
                "XDG_CONFIG_HOME": str(base / "config"),
            }
            with patch.dict(os.environ, environment, clear=False):
                self.assertTrue(looks_like_seclists(source_root))
                found = scan_seclists(persist=True)
                self.assertEqual(len(found), 1)
                registered = load_sources()
                self.assertEqual(len(registered), 1)
                self.assertEqual(registered[0].name, "seclists")
                self.assertEqual(registered[0].resolved_path, source_root.resolve())

    def test_add_source_persists_registered_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source_root = self._make_seclists(base)
            with patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(base / "config")},
                clear=False,
            ):
                added = add_source("SecLists", source_root)
                self.assertEqual(added.name, "seclists")
                self.assertEqual(load_sources(), [added])

    def test_invalid_seclists_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            environment = {
                "XDG_CONFIG_HOME": str(base / "config"),
            }
            with patch.dict(os.environ, environment, clear=False):
                with self.assertRaisesRegex(Exception, "does not look like SecLists"):
                    add_source("seclists", base)

    def test_external_url_wordlist_is_downloaded_once_to_cache(self) -> None:
        entry = CatalogEntry(
            id="test_external_wordlist",
            name="Test external wordlist",
            domain="file_upload",
            kind="external_wordlist",
            source="example",
            path="https://example.test/wordlist.txt",
            tags=("file-upload", "test"),
            description="Test fixture.",
        )
        with tempfile.TemporaryDirectory() as temporary:
            with patch.dict(
                os.environ,
                {"XDG_CACHE_HOME": str(Path(temporary) / "cache")},
                clear=False,
            ):
                with patch(
                    "web_dict_composer.sources.external.urlopen",
                    return_value=FakeResponse(b"one\ntwo\n"),
                ) as mocked_urlopen:
                    downloaded = download_external_wordlist(entry)
                    cached = download_external_wordlist(entry)

                self.assertEqual(downloaded, cached)
                self.assertEqual(cached_external_wordlist(entry), downloaded)
                self.assertEqual(downloaded.read_text(encoding="utf-8"), "one\ntwo\n")
                mocked_urlopen.assert_called_once()

    def test_reference_url_cannot_be_downloaded_as_a_wordlist(self) -> None:
        entry = CatalogEntry(
            id="test_reference",
            name="Test reference",
            domain="file_upload",
            kind="reference",
            source="example",
            path="https://example.test/documentation",
            tags=("file-upload", "reference"),
            description="Test fixture.",
        )
        with self.assertRaisesRegex(SourceError, "Only external_wordlist"):
            download_external_wordlist(entry)


if __name__ == "__main__":
    unittest.main()
