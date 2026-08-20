# Review: lfi_traversal_steps_all_windows

- **Source:** The reviewed Unix, Windows, encoded, double-encoded, and filter-bypass traversal step
  sets, plus separator patterns manually decomposed from SecLists
  [`LFI-Jhaddix.txt`](https://github.com/danielmiessler/SecLists/blob/master/Fuzzing/LFI/LFI-Jhaddix.txt).
- **Why it exists:** Provide a single broad Windows-oriented step set for bounded mass fuzzing.
- **Must contain:** Every Linux aggregate atom because Windows stacks may normalize `/`, plus all
  reviewed backslash, encoded-backslash, Unicode reverse-solidus, and reversed encoded-separator
  ideas found in the source list.
- **Must not contain:** Repeated depths, drive or UNC prefixes, targets, leading absolute roots,
  terminators, wrappers, suffixes, complete LFI payloads, or malformed source lines.
- **Doubtful entries:** Forward-slash support, Unicode compatibility, overlong UTF-8, no-percent
  encoding, Base64, and every encoded or bypass form depend on the target stack and its
  normalization order.
- **Missing entries added:** The Linux-derived variants plus percent-encoded separator-before-dots,
  Unicode ellipsis with backslashes, two-dot-leader/small-reverse-solidus, and fullwidth/small
  reverse-solidus variants.
- **Entries removed:** Targets, `%00` suffixes, expanded depths, whole encoded payloads, and malformed
  prose from the source list.
- **Final result:** Thirty-five unique Windows-oriented traversal-separator atoms.
