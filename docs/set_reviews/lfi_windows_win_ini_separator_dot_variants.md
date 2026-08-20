# Review: lfi_windows_win_ini_separator_dot_variants

- **Source:** OWASP Path Traversal and WSTG Windows-specific normalization guidance, plus separator
  forms reviewed from SecLists `LFI-Jhaddix.txt`.
- **Why it exists:** Exercise independent filtering of path separators and extension dots while
  keeping the Windows target fixed as `Windows/win.ini`.
- **Generation rule:** `Windows{separator}win{dot}ini` over twenty-three separator variants and
  eleven dot variants, preserving deterministic separator-major order.
- **Must contain:** Forward- and backslash forms, duplicated/mixed separators, single and double
  percent encoding, legacy overlong forms, no-percent forms, and raw/encoded Unicode compatibility
  characters; every separator must be combined with every dot.
- **Must not contain:** Drive or UNC prefixes, traversal, other targets, terminators, suffixes, or
  unbounded recursive encoding.
- **Doubtful entries:** Most legacy and Unicode forms depend on decoding and normalization order;
  Windows acceptance also varies between shell, API, web server, framework, and filesystem layers.
- **Missing entries added:** None outside the documented Cartesian matrix.
- **Entries removed:** Arbitrary Unicode lookalikes and encoding beyond two percent-decoding layers.
- **Final result:** 253 unique `Windows/win.ini` target variants.
