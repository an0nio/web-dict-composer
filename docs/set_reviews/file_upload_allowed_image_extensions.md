# Review: file_upload_allowed_image_extensions

- **Source:** IANA media-type registry, common browser formats, and application upload allowlists.
- **Why it exists:** Provide a short image allowlist for filename composition profiles.
- **Must contain:** Widely accepted passive raster image extensions.
- **Must not contain:** MIME values, active document formats, or compound filenames.
- **Doubtful entries:** AVIF support depends on the application processing stack.
- **Missing entries added:** `.avif`.
- **Entries removed:** `.svg` remains in the limited-upload set because it is structured and may
  carry active content.
- **Final result:** JPG/JPEG, PNG, GIF, WebP, and AVIF extension atoms.
