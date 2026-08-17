# Review: file_upload_filename_separators_basic

- **Source:** Apache multi-extension behavior, OWASP upload guidance, and filesystem syntax.
- **Why it exists:** Model literal boundaries separately from extensions and encoded controls.
- **Must contain:** Small literal separators with an explicit filename-normalization hypothesis.
- **Must not contain:** Percent encoding, slashes, path traversal, or whole filename payloads.
- **Doubtful entries:** Semicolon and colon behavior is server/filesystem-specific.
- **Missing entries added:** The two-dot form for normalization tests.
- **Entries removed:** Slashes and backslash sequences because those change the value into a path.
- **Final result:** `.`, `..`, `;`, and `:`.
