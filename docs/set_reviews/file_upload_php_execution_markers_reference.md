# Review: file_upload_php_execution_markers_reference

- **Source:** A stable local PHP execution marker and the path-diagnostic variant supplied for this
  project.
- **Why it exists:** Confirm that an uploaded file is both retrievable and interpreted as PHP,
  while making the fixtures discoverable without treating executable source as a dictionary.
- **Must contain:** A fixed marker absent as literal text from the PHP fixtures, a minimal execution
  variant, an optional hexadecimal path-diagnostic variant, and an authorized-use warning.
- **Must not contain:** Command execution, shell functionality, network callbacks, file mutation,
  authentication bypasses, random marker generation, or inclusion in wizard/profile inputs.
- **Doubtful entries:** Filesystem diagnostics disclose local paths and are therefore separated
  from the minimal marker and accompanied by an explicit cleanup warning.
- **Missing entries added:** A minimal marker was separated from the original diagnostic form so
  execution-only checks do not expose unnecessary server metadata.
- **Entries removed:** None.
- **Final result:** Two packaged, non-composable PHP fixtures referenced by one searchable local
  catalog document.
