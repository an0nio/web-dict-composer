# Review: lfi_traversal_steps_windows

- **Source:** OWASP directory traversal guidance, Windows path syntax, and SecLists LFI references.
- **Why it exists:** Keep the literal Windows parent-directory step separate from Unix traversal.
- **Must contain:** One literal backslash-based parent step.
- **Must not contain:** Drive prefixes, UNC paths, targets, encoded values, or repeated depths.
- **Doubtful entries:** Applications and intermediaries may normalize forward slashes separately;
  the Unix step is composed explicitly when that behavior is in scope.
- **Missing entries added:** None.
- **Entries removed:** Pre-expanded and target-bearing Windows payloads.
- **Final result:** One `..\` atom; encoded backslashes live in the encoded sets.
