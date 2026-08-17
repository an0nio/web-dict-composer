# Review: file_upload_php_handler_candidates

- **Source:** Apache `mod_mime`, OWASP upload testing, SecLists `web-extensions.txt`, and common
  Apache/PHP-FPM package mappings.
- **Why it exists:** Provide a compact PHP-related handler candidate set for filename composition.
- **Must contain:** Extension atoms plausibly mapped to PHP handlers in current or commonly seen
  configurations.
- **Must not contain:** Complete filenames, double extensions, MIME values, or source-only formats.
- **Doubtful entries:** `.pht`, `.phtm`, and `.phar` remain configuration-dependent; the set name
  deliberately says candidates rather than valid extensions.
- **Missing entries added:** None beyond the reviewed current/common candidate group.
- **Entries removed:** `.php2`–`.php7` moved to the legacy set; `.phps`, `.inc`, and `.phpt` moved
  to the source/include set; `.pgif` was removed as an unsupported mixed-format assumption.
- **Final result:** 5 atoms in `php_handler_candidates.txt`.
