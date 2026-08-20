# Review: lfi_php_index_dot_variants

- **Source:** URL percent-encoding conventions, OWASP normalization guidance, and Unicode dot forms
  reviewed from SecLists `LFI-Jhaddix.txt`.
- **Why it exists:** Exercise extension-dot filtering while keeping the PHP target fixed as
  `index.php`.
- **Generation rule:** `index{dot}php` over eleven reviewed dot variants.
- **Must contain:** Raw, single- and double-percent-encoded, overlong UTF-8, no-percent, one-dot
  leader, and fullwidth-dot representations in encoded and raw forms where applicable.
- **Must not contain:** Other PHP files, separators, traversal, terminators, suffixes, or more than
  two percent-decoding layers.
- **Doubtful entries:** Overlong, no-percent, and Unicode forms depend on application decoding and
  normalization and generally do not name `index.php` directly on disk.
- **Missing entries added:** None outside the documented generation matrix.
- **Entries removed:** Arbitrary Unicode lookalikes and unbounded recursive encoding.
- **Final result:** Eleven unique `index.php` target variants.
