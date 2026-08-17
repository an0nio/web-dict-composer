# Review: file_upload_limited_upload_candidates

- **Source:** IANA media types, browser handling behavior, and OWASP upload guidance.
- **Why it exists:** Isolate structured or browser-interpreted formats from passive images.
- **Must contain:** HTML, SVG, XML, and XHTML-related extension atoms.
- **Must not contain:** Markup payloads, scripts, MIME values, or executable server extensions.
- **Doubtful entries:** Actual impact depends on serving headers, sanitization, and origin context.
- **Missing entries added:** `.svgz` to keep the compressed SVG suffix visible but explicit.
- **Entries removed:** Passive raster formats remain in the image allowlist.
- **Final result:** Six extension atoms used only by the constrained SVG/XML profile.
