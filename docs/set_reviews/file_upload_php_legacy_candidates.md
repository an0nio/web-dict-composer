# Review: file_upload_php_legacy_candidates

- **Source:** Historical Apache/PHP mappings and SecLists extension inventories.
- **Why it exists:** Keep version-like legacy candidates out of the current/common handler set.
- **Must contain:** Small PHP-version suffixes documented in historical deployments.
- **Must not contain:** Current handler candidates, source formats, or compound filenames.
- **Doubtful entries:** Every value is configuration-dependent and many are obsolete.
- **Missing entries added:** None; breadth is intentionally constrained.
- **Entries removed:** `.php6` because it lacks a corresponding released PHP major version.
- **Final result:** Five legacy atoms from `.php2` through selected deployed versions.
