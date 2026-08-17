# LFI target atoms

Target paths are stored without a leading root or drive prefix so profiles can generate relative
and absolute forms without duplicating lists. Basic and sensitive targets stay separate.

Do not add credentials, secrets, traversal prefixes, wrappers, suffix bypasses, or large framework
path dumps. Log locations must be tied to documented server or package defaults.
