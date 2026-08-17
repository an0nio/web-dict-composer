# Review: file_upload_content_types_images

- **Source:** IANA media-type registry plus the widely observed legacy `image/pjpeg` value.
- **Why it exists:** Offer an image-only header set distinct from the cross-format MIME set.
- **Must contain:** Media types corresponding to the reviewed image extension groups.
- **Must not contain:** Extensions, magic bytes, arbitrary `x-` aliases, or complete headers.
- **Doubtful entries:** `image/pjpeg` is not a current registered type and remains for compatibility.
- **Missing entries added:** WebP and AVIF registered media types.
- **Entries removed:** BMP/TIFF because they are absent from the built-in image allowlist.
- **Final result:** Seven image media-type atoms.
