from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from web_dict_composer.sources.manager import (
    add_source,
    load_sources,
    looks_like_seclists,
    scan_seclists,
)


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


if __name__ == "__main__":
    unittest.main()
