# Review: lfi_traversal_steps_double_encoded

- **Source:** OWASP path traversal guidance and double-decoding cases represented in SecLists.
- **Why it exists:** Make an additional decoding-layer assumption explicit and opt-in.
- **Must contain:** One double-encoded slash/backslash parent step per line.
- **Must not contain:** Single encoding, targets, repeated depths, or mixed complete payloads.
- **Doubtful entries:** These forms only matter when separate layers decode more than once.
- **Missing entries added:** Symmetric fully encoded slash and backslash variants.
- **Entries removed:** Redundant capitalization variants and pre-expanded paths.
- **Final result:** Four double-encoded atomic steps.
