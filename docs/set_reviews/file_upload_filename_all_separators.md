# Review: file_upload_filename_all_separators

- **Source:** The reviewed basic and encoded filename separator sets plus explicitly requested
  path-like and Unicode normalization candidates.
- **Why it exists:** Provide one deliberate broad input for mass file-upload filename fuzzing.
- **Must contain:** Every built-in basic and encoded separator, plus `/`, `.\`, `...`, and `…`.
- **Must not contain:** Extensions, filename bases, complete filenames, traversal depths, or raw
  control bytes.
- **Doubtful entries:** `/`, `.\`, NUL encoding, and Unicode ellipsis are highly dependent on the
  filesystem, framework, decoding order, and filename normalization behavior.
- **Missing entries added:** Slash, dot-backslash, three-dot, and Unicode-ellipsis candidates that
  are intentionally absent from the narrower sets.
- **Entries removed:** None; duplicate values from the source sets are represented once.
- **Final result:** Fourteen unique broad separator candidates.
