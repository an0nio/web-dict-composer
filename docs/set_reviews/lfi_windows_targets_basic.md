# Review: lfi_windows_targets_basic

- **Source:** Microsoft Windows/IIS documentation, clean Windows/IIS lab installations, and
  SecLists Windows LFI references.
- **Why it exists:** Supply recognizable Windows read targets without traversal or drive prefixes.
- **Must contain:** Stable OS/IIS paths useful for confirming path resolution behavior.
- **Must not contain:** User profiles, secrets, dynamic log filenames, UNC paths, or traversal.
- **Doubtful entries:** `inetpub/wwwroot/web.config` depends on IIS layout but is retained as a
  stack-specific application target.
- **Missing entries added:** None.
- **Entries removed:** None from the former compact set.
- **Final result:** Three bounded Windows targets.
