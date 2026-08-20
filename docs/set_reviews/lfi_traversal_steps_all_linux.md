# Review: lfi_traversal_steps_all_linux

- **Source:** The reviewed Unix, encoded, double-encoded, and filter-bypass traversal step sets,
  plus separator patterns manually decomposed from SecLists
  [`LFI-Jhaddix.txt`](https://github.com/danielmiessler/SecLists/blob/master/Fuzzing/LFI/LFI-Jhaddix.txt).
- **Why it exists:** Provide a single broad Linux-oriented step set for bounded mass fuzzing.
- **Must contain:** Every reviewed Linux-relevant separator atom, including literal, encoded,
  double-encoded, mixed-separator, overlong UTF-8, Unicode, no-percent, and Base64 ideas found in
  the source list.
- **Must not contain:** Repeated depths, targets, leading absolute roots, terminators, wrappers,
  suffixes, complete LFI payloads, or malformed prose copied into the source wordlist.
- **Doubtful entries:** Overlong UTF-8 is rejected by modern conforming decoders; Unicode
  compatibility, no-percent encoding, Base64, and filter-bypass forms depend entirely on the target
  stack and normalization order.
- **Missing entries added:** Three-dot and double-slash forms; encoded-dot/literal-slash and uppercase
  URL variants; mixed slash/backslash bypasses; overlong UTF-8; no-percent `2f`; Base64 `../`; and
  fullwidth/Unicode separator forms.
- **Entries removed:** Targets, `%00` suffixes, expanded depths, whole encoded payloads, and
  Windows-only backslash forms from the source list.
- **Final result:** Twenty-one unique Linux-oriented traversal-separator atoms.
