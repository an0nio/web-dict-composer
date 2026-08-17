# Review: lfi_log_file_targets

- **Source:** Default Apache HTTP Server and Nginx package/configuration paths on common Linux
  distributions.
- **Why it exists:** Keep log locations separate because defaults and sensitivity differ by stack.
- **Must contain:** Relative paths for common access and error logs only.
- **Must not contain:** Traversal, Windows Event Logs, dynamic virtual-host names, or rotated files.
- **Doubtful entries:** Package defaults can be overridden and differ between Debian and RHEL.
- **Missing entries added:** Both Debian-style `apache2` and RHEL-style `httpd` locations.
- **Entries removed:** Authentication/system logs and speculative application logs.
- **Final result:** Six Apache/Nginx log targets for the dedicated profile.
