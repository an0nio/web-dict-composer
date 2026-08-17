# Review: lfi_suffix_bypasses_experimental

- **Source:** OWASP path traversal guidance and historical parser-termination techniques.
- **Why it exists:** Expose a small optional set without implying current universal effectiveness.
- **Must contain:** Single suffix atoms whose interpretation depends on URL or legacy parser layers.
- **Must not contain:** Targets, traversal prefixes, raw controls, or complete payloads.
- **Doubtful entries:** All entries are environment-specific; NUL termination is primarily legacy.
- **Missing entries added:** Encoded question-mark and fragment delimiter variants.
- **Entries removed:** Version-specific length padding and large suffix collections.
- **Final result:** Four experimental suffix atoms excluded from default profiles.
