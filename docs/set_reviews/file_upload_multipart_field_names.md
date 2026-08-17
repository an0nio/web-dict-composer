# Review: file_upload_multipart_field_names

- **Source:** Common HTML upload form conventions and SecLists parameter lists as contrast.
- **Why it exists:** Supply a small upload-specific parameter-name set for direct lookup.
- **Must contain:** Names conventionally associated with file-valued multipart fields.
- **Must not contain:** Generic application parameters, headers, values, or request fragments.
- **Doubtful entries:** `files[]` reflects a framework convention rather than an HTML requirement.
- **Missing entries added:** `attachment`, `media`, `photo`, and the array-style form.
- **Entries removed:** Broad parameter dictionaries with no upload-specific meaning.
- **Final result:** Nine field-name atoms.
