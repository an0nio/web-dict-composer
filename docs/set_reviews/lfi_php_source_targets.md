# Review: lfi_php_source_targets

- **Source:** Common PHP front-controller and configuration conventions, including WordPress.
- **Why it exists:** Supply application-relative resource names for read-only PHP filter profiles.
- **Must contain:** Short, recognizable PHP source paths with no traversal or wrapper prefix.
- **Must not contain:** Credentials, vendor trees, framework dumps, or non-PHP targets.
- **Doubtful entries:** Framework configuration paths vary significantly by version and layout.
- **Missing entries added:** `public/index.php` and two common configuration locations.
- **Entries removed:** Large framework-specific path inventories.
- **Final result:** Six bounded PHP source targets.
