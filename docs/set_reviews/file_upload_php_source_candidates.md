# Review: file_upload_php_source_candidates

- **Source:** PHP source-distribution conventions, PHP test format documentation, and SecLists.
- **Why it exists:** Separate disclosure/include/test candidates from request-handler candidates.
- **Must contain:** PHP-adjacent extension atoms whose main relevance is source or include handling.
- **Must not contain:** Values claimed to execute by default or complete filenames.
- **Doubtful entries:** `.inc` is a convention and `.phps` depends on explicit server mapping.
- **Missing entries added:** `.phpt` to represent PHP test files without treating it as a handler.
- **Entries removed:** Handler and legacy version suffixes moved to their respective sets.
- **Final result:** `.phps`, `.inc`, and `.phpt` as a non-handler review set.
