# Review: lfi_traversal_steps_unix

- **Source:** POSIX path syntax and OWASP path traversal guidance.
- **Why it exists:** Represent one parent-directory movement independently of depth and target.
- **Must contain:** Exactly one literal Unix-style parent step.
- **Must not contain:** Repeated depth, targets, encodings, absolute roots, or suffixes.
- **Doubtful entries:** None at the syntax level; acceptance still depends on the application.
- **Missing entries added:** None.
- **Entries removed:** Every pre-expanded `../../...` form.
- **Final result:** The single atom `../`.
