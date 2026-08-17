# Review: file_upload_allowed_archive_extensions

- **Source:** IANA media types and common archive-upload allowlists.
- **Why it exists:** Provide extension atoms without creating or describing archive contents.
- **Must contain:** Widely encountered archive and compression suffixes.
- **Must not contain:** Compound traversal names, archive members, bombs, or MIME values.
- **Doubtful entries:** Availability of RAR and 7z processors varies by deployment.
- **Missing entries added:** `.tgz` as a common shorthand distinct from `.tar` and `.gz` atoms.
- **Entries removed:** Multi-part and platform-specific archive suffixes.
- **Final result:** Six bounded archive/compression extension atoms.
