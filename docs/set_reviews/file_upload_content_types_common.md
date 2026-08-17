# Review: file_upload_content_types_common

- **Source:** IANA media-type registry and SecLists `web-all-content-types.txt` as a broad reference.
- **Why it exists:** Provide a bounded cross-section of MIME values commonly relevant to uploads.
- **Must contain:** Registered or broadly interoperable media types spanning images, documents,
  structured text, archives, and generic binary data.
- **Must not contain:** Extensions, magic bytes, multipart field names, or the full IANA registry.
- **Doubtful entries:** `application/octet-stream` is generic but useful when testing header-only
  validation.
- **Missing entries added:** `image/webp` and `image/avif`.
- **Entries removed:** None from the old compact set.
- **Final result:** 12 reviewable MIME atoms, with image-only values also available separately.
