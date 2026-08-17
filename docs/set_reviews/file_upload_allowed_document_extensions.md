# Review: file_upload_allowed_document_extensions

- **Source:** IANA media-type registrations and common document-upload allowlists.
- **Why it exists:** Supply a bounded document allowlist dimension for custom profiles.
- **Must contain:** Common text, PDF, CSV, and current Office container extensions.
- **Must not contain:** Executables, scripts, MIME values, or legacy macro-enabled formats.
- **Doubtful entries:** Office formats require application-specific content validation.
- **Missing entries added:** `.csv` as a common text-data upload format.
- **Entries removed:** Macro-enabled and legacy binary Office suffixes.
- **Final result:** Six familiar document extension atoms.
