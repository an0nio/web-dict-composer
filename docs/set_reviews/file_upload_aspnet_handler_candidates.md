# Review: file_upload_aspnet_handler_candidates

- **Source:** Microsoft IIS/ASP.NET handler mapping documentation, OWASP upload testing, and
  SecLists extension references.
- **Why it exists:** Cover classic ASP and ASP.NET request-handler extension candidates.
- **Must contain:** Handler-oriented extension atoms used by classic ASP or ASP.NET mappings.
- **Must not contain:** Configuration files, certificates, route suffixes, or complete payloads.
- **Doubtful entries:** All mappings remain dependent on installed IIS/ASP.NET components.
- **Missing entries added:** None.
- **Entries removed:** `.asa`, `.cer`, `.config`, and `.soap` because the old set mixed sensitive
  or configuration-related files with direct handler extensions.
- **Final result:** `.asp`, `.aspx`, `.ashx`, and `.asmx`.
