# Review: lfi_traversal_steps_encoded

- **Source:** OWASP directory traversal guidance and decomposition of SecLists LFI wordlists.
- **Why it exists:** Model one decoding-sensitive parent-directory step independently of depth.
- **Must contain:** Single-encoded slash/backslash and partially encoded dot variants.
- **Must not contain:** Targets, suffixes, repeated depths, or complete LFI payloads.
- **Doubtful entries:** Partial dot encodings depend on which layer decodes and normalizes paths.
- **Missing entries added:** Symmetric partially encoded dot variants for slash and backslash.
- **Entries removed:** Every two-step value from the former `encoded_traversal_sequences.txt`.
- **Final result:** 8 atomic single-encoded steps.
