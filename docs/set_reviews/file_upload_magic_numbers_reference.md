# Review: file_upload_magic_numbers_reference

- **Source:** Common format specifications and the upstream `file` magic database.
- **Why it exists:** Make frequently useful file signatures discoverable without pretending that
  binary data is a line-oriented wordlist.
- **Must contain:** A compact human-readable table, exact copy-paste `printf` commands for each
  listed signature, an optional marker append example, and explicit validation caveats.
- **Must not contain:** Composable set values, committed generated binary samples, advanced
  polyglot construction, or claims that a short prefix alone creates a complete valid format.
- **Doubtful entries:** PE/DOS and WebP require additional structural checks, which remain stated
  next to their prefixes and in the signature-stub warning.
- **Missing entries added:** Exact shell commands for writing each listed signature without the
  newline that `echo` would normally add.
- **Entries removed:** None.
- **Final result:** A concise local signature reference with copy-paste commands and a link to the
  maintained upstream magic database.
