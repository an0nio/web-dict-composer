# LFI target atoms

Target paths are stored without a leading root or drive prefix so profiles can generate relative
and absolute forms without duplicating lists. Basic and sensitive targets stay separate.

The `*_variants.txt` sets are explicit broad targets for normalization fuzzing:

- `linux_passwd_separator_variants.txt` substitutes the separator in `etc/passwd`;
- `windows_win_ini_separator_dot_variants.txt` combines every reviewed Windows separator with
  every reviewed dot representation in `Windows/win.ini`;
- `php_index_dot_variants.txt` substitutes the extension boundary in `index.php`.

Their matrices are bounded to raw, duplicated/mixed, single- and double-percent-encoded, legacy,
no-percent, and Unicode representations. They do not imply that every parser accepts each value.

Do not add credentials, secrets, traversal prefixes, wrappers, suffix bypasses, or large framework
path dumps. Log locations must be tied to documented server or package defaults.
