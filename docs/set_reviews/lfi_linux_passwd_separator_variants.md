# Review: lfi_linux_passwd_separator_variants

- **Source:** OWASP Path Traversal encoding guidance and the separator forms reviewed from SecLists
  `LFI-Jhaddix.txt`.
- **Why it exists:** Exercise slash filtering and normalization while keeping the Linux target fixed
  as `etc/passwd`.
- **Generation rule:** `etc{separator}passwd` over eleven reviewed forward-separator variants.
- **Must contain:** Raw, doubled, mixed, single- and double-percent-encoded, overlong UTF-8,
  no-percent, percent-encoded fullwidth, and raw fullwidth slash representations.
- **Must not contain:** A leading root, traversal prefixes, other targets, terminators, suffixes, or
  more than two percent-decoding layers.
- **Doubtful entries:** Mixed, overlong, no-percent, and Unicode forms are parser- and
  normalization-dependent and are not universally valid filesystem paths.
- **Missing entries added:** None outside the documented generation matrix.
- **Entries removed:** Infinite encoding-depth and arbitrary Unicode lookalike expansion.
- **Final result:** Eleven unique `etc/passwd` target variants.
