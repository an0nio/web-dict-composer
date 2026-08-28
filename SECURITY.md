# Security policy and intended use

`web-dict-composer` is an artifact generator for education, labs, CTFs, and explicitly authorized
security testing. It does not contact targets or validate vulnerabilities. Its only optional
network operation is a user-confirmed download from a direct URL cataloged as an
`external_wordlist`; downloaded text is size-limited and cached locally.

The wizard may read an arbitrary local UTF-8 dictionary only when the user enters its path with
`:file` and confirms it. YAML profile `file:` references remain contained within the project root.
Catalog entries for magic-number documentation, webshell resources, and reverse-shell resources
are metadata-only `reference` entries. The tool never downloads, copies, executes, or composes
their contents.

The package includes two inert-on-disk PHP execution-marker fixtures for deliberate upload by an
authorized tester. They contain no command execution, shell, network callback, or file mutation.
The application never uploads, executes, modifies, or composes them. The diagnostic variant can
reveal server filesystem paths when a separately operated PHP server executes it, so remove it
from the tested environment after use.

Please report path traversal in resource/profile handling, unsafe file writes, dependency issues,
or unexpected network behavior through the repository's private security reporting channel. Do
not include live target data, credentials, or unredacted customer artifacts in a report.

Generated wordlists can contain strings that endpoint protection tools classify as security-test
payloads. Store them on a dedicated testing workstation rather than a production web server.
