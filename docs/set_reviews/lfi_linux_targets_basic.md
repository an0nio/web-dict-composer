# Review: lfi_linux_targets_basic

- **Source:** Linux filesystem conventions, Linux kernel procfs documentation, and systemd
  `os-release` documentation.
- **Why it exists:** Supply recognizable file-read targets independently of traversal syntax.
- **Must contain:** Stable relative paths with no leading slash.
- **Must not contain:** Traversal prefixes, application secrets, log paths, or wrapper syntax.
- **Doubtful entries:** Distribution-specific files and permissions are intentionally excluded from
  the basic set.
- **Missing entries added:** None.
- **Entries removed:** `proc/self/environ`, `proc/self/cmdline`, and log paths moved to sensitive or
  log-specific sets.
- **Final result:** Four basic Linux targets.
