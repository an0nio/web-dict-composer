# Review: lfi_linux_targets_sensitive

- **Source:** Linux filesystem conventions and Linux kernel procfs documentation.
- **Why it exists:** Keep higher-sensitivity confirmation targets away from the basic profile.
- **Must contain:** Stable relative paths whose content can expose credentials or process context.
- **Must not contain:** Traversal, logs, application secrets, kernel memory, or destructive endpoints.
- **Doubtful entries:** Procfs readability and content vary by kernel and process isolation.
- **Missing entries added:** `proc/self/cmdline` and `proc/self/maps` for explicit opt-in review.
- **Entries removed:** Basic identity files and web logs moved to their own sets.
- **Final result:** Four sensitive targets not consumed by built-in profiles.
