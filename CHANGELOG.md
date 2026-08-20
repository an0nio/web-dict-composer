# Changelog

## Unreleased

- Redesign `wizard` around progressive tag filtering, direct name/ID lookup, inline custom
  dictionaries, and explicit pattern selection.
- Preserve the former built-in profile flow as the `guided` command.
- Show catalog tags alongside descriptions in dictionary search results.
- Add user-facing tag aliases for dangerous handlers, allowed extensions, and traversal steps.

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
