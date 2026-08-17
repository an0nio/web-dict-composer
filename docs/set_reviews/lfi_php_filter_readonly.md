# Review: lfi_php_filter_readonly

- **Source:** Official PHP supported-wrapper and `php://filter` documentation.
- **Why it exists:** Compose read-only source-disclosure candidates in controlled PHP labs.
- **Must contain:** Filter prefixes ending immediately before the resource path.
- **Must not contain:** `data://`, `expect://`, `php://input`, archive wrappers, write filters, or
  complete target paths.
- **Doubtful entries:** Availability still depends on the PHP function and application behavior.
- **Missing entries added:** None.
- **Entries removed:** All non-filter wrapper families remain out of scope.
- **Final result:** Two equivalent base64-read filter spellings.
