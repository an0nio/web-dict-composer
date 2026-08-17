# Security policy and intended use

`web-dict-composer` is an offline artifact generator for education, labs, CTFs, and explicitly
authorized security testing. It does not send requests or validate vulnerabilities.

Please report path traversal in resource/profile handling, unsafe file writes, dependency issues,
or accidental network behavior through the repository's private security reporting channel. Do
not include live target data, credentials, or unredacted customer artifacts in a report.

Generated wordlists can contain strings that endpoint protection tools classify as security-test
payloads. Store them on a dedicated testing workstation rather than a production web server.
