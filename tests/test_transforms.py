from __future__ import annotations

import unittest

from web_dict_composer.transforms.library import (
    apply_transforms,
    transform_upper_bound,
    validate_transform_spec,
)


class FileUploadRequestPathTransformTests(unittest.TestCase):
    def spec(self, **overrides: object) -> dict[str, object]:
        spec: dict[str, object] = {
            "name": "file_upload_request_path_variants",
            "source": "stored",
            "target": "segment",
            "decode_depth": 2,
            "presets": [],
            "max_variants_per_input": 64,
        }
        spec.update(overrides)
        return spec

    def test_stored_literal_percent_and_decoding_hypotheses_are_both_emitted(self) -> None:
        values = apply_transforms("shell.jpg%00.phar", [self.spec()])
        self.assertIn("shell.jpg%00.phar", values)
        self.assertIn("shell.jpg%2500.phar", values)
        self.assertFalse(any("\x00" in value for value in values))

    def test_single_segment_encodes_slashes_while_paths_preserve_them(self) -> None:
        segment = apply_transforms("uploads/name.php", [self.spec()])
        relative = apply_transforms(
            "uploads/name.php",
            [self.spec(target="relative_path")],
        )
        self.assertIn("uploads%2Fname.php", segment)
        self.assertNotIn("uploads/name.php", segment)
        self.assertIn("uploads/name.php", relative)

    def test_accepted_mode_adds_control_sanitizer_hypotheses(self) -> None:
        values = apply_transforms(
            "shell.jpg%00.phar",
            [self.spec(source="accepted", presets=["common_web", "posix"])],
        )
        self.assertIn("shell.jpg%2500.phar", values)
        self.assertIn("shell.jpg.phar", values)
        self.assertIn("shell.jpg", values)

    def test_windows_unicode_extension_collision_and_length_are_bounded(self) -> None:
        spec = self.spec(
            source="accepted",
            presets=[
                "windows",
                "unicode",
                "extension_rewrite",
                "collision_suffixes",
                "length_limit",
            ],
            forced_extensions=["jpg"],
            collision_suffix_limit=2,
            filename_max_bytes=12,
            max_variants_per_input=20,
        )
        values = apply_transforms("café-long-name.PHP", [spec])
        self.assertLessEqual(len(values), 20)
        self.assertIn("caf%C3%A9-long-name.PHP", values)
        self.assertEqual(transform_upper_bound([spec]), 20)

    def test_transform_options_are_validated(self) -> None:
        errors = validate_transform_spec(
            self.spec(
                source="unknown",
                presets=["extension_rewrite"],
                forced_extensions=[],
            )
        )
        self.assertTrue(any("source" in error for error in errors))
        self.assertTrue(any("forced_extensions" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
