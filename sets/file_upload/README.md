# File Upload sets

The active File Upload sets are small line-oriented atoms grouped by meaning:

- `extensions/` — handler candidates and application allowlist extensions;
- `filename/` — filename stems and literal/encoded separators;
- `mime/` — upload-relevant media types;
- `multipart/` — conventional file field names.

Profiles compose these atoms into complete filenames. Do not add double extensions, complete
bypass payloads, executable contents, web shells, magic bytes, metadata payloads, archives, or
binary fixtures to these directories.

Magic numbers, webshell sources, and reverse-shell sources are cataloged separately as
non-composable `reference` entries. This keeps them searchable for human consultation without
treating documentation, binary signatures, or executable content as input to the wizard or a
profile.

Small execution-verification files live under `fixtures/file_upload/` and are likewise exposed
only through a documentation reference. They must not be copied into these line-oriented sets.

Review sources include current Apache, IIS/ASP.NET, Tomcat, PHP, IANA, OWASP, and SecLists
documentation. SecLists and technique repositories remain external wordlists or references unless
a documented, reproducible derivation produces a clean set. Review records live in
`docs/set_reviews/`.
