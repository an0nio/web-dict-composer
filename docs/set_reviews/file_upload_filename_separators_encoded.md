# Review: file_upload_filename_separators_encoded

- **Source:** OWASP upload-testing guidance and controlled decoding/normalization test cases.
- **Why it exists:** Keep encoded whitespace and control candidates opt-in and reviewable.
- **Must contain:** Individual encoded space, NUL, tab, LF, CR, and CRLF candidates.
- **Must not contain:** Precomposed filenames, path separators, double encoding, or raw controls.
- **Doubtful entries:** NUL handling is mainly relevant to legacy or mismatched parser chains.
- **Missing entries added:** Explicit tab and CR variants.
- **Entries removed:** Unicode ellipsis, slash, and `.\` from the original mixed shell loop.
- **Final result:** Six bounded percent-encoded candidates.
