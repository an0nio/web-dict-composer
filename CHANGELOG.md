# Changelog

## Unreleased

- Redesign `wizard` around progressive tag filtering, direct name/ID lookup, inline custom
  dictionaries, and explicit pattern selection.
- Preserve the former built-in profile flow as the `guided` command.
- Show catalog tags alongside descriptions in dictionary search results.
- Add user-facing tag aliases for dangerous handlers, allowed extensions, and traversal steps.
- Allow the wizard to select `external_wordlist` entries while continuing to exclude references.
- Locate SecLists automatically on selection and support confirmed, size-limited URL downloads
  cached under the XDG cache directory.
- Preview complete dictionaries through the system pager before wizard selection.
- Run `dicts search` as a progressive tag/name search session when no query is supplied.
- Load an arbitrary explicit UTF-8 dictionary path from the wizard without relaxing YAML profile
  path containment.
- Add broad aggregate sets for file-upload separators and Linux/Windows traversal steps, including
  reviewed separator atoms derived from SecLists `LFI-Jhaddix.txt`.
- Add bounded generated target matrices for `etc/passwd`, `Windows/win.ini`, and `index.php`
  separator/dot normalization fuzzing.
- Catalog magic-number documentation, Kali webshell locations, and selected upstream webshell and
  reverse-shell projects as searchable, non-composable references.
- Add deterministic `catalog_selector` profile inputs with explicit options/defaults and
  multi-selection plus pager previews in `guided`.
- Add a generic File Upload handler-against-allowlist profile covering selectable PHP, ASP.NET,
  JSP, image, document, archive, and separator sets.
- Convert the existing multistack-images handler union into a selector while preserving all three
  stacks as its non-interactive default.
- Add a guided-only File Upload request-path profile with runtime file/paste input, explicit stored
  versus accepted filename semantics, URL segment/path/object-key modes, bounded storage
  sanitizer presets, and transform options recorded in the manifest.
- Package minimal and path-diagnostic PHP execution markers whose stable `php_funciona` response
  can be matched by ffuf, and catalog their documentation as a non-composable reference.
- Add copy-paste `printf` commands for every documented magic-number signature and a minimal PHP
  marker append example, while keeping complete polyglot construction out of scope.

## 0.3.0 — 2026-08-17

- Provide a focused File Upload and LFI / Path Traversal catalog.
- Show dictionary descriptions in searchable, responsive tables.
- Resolve profile inputs through validated `catalog` and `catalogs` references.
- Include reviewed extension, filename, MIME, multipart, traversal, target, wrapper, and suffix
  sets.
- Generate traversal depth from atomic steps with bounded repeat rules.
- Estimate every profile before composition and enforce deterministic output caps.
- Generate a wordlist and a compact JSON manifest for each build.
- Detect and register SecLists without copying or indexing its complete tree.
