# Review: lfi_traversal_steps_filter_bypass

- **Source:** OWASP normalization guidance and manually reviewed SecLists LFI forms.
- **Why it exists:** Preserve a tiny experimental set for non-recursive filtering hypotheses.
- **Must contain:** One-step dot/separator forms that may normalize after a naive replacement.
- **Must not contain:** Targets, encodings, repeated depths, or claims of universal behavior.
- **Doubtful entries:** Every entry is parser- and filter-order-dependent.
- **Missing entries added:** Matching forward/backslash forms.
- **Entries removed:** Long evasions and any target-bearing payload.
- **Final result:** Four experimental atoms excluded from all default profiles.
