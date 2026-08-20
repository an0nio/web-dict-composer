from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from web_dict_composer.core.errors import ComposerError
from web_dict_composer.core.resources import ACTIVE_DOMAINS, resource_root, resolve_resource
from web_dict_composer.sources.manager import load_sources


ALLOWED_KINDS = {
    "atom_set",
    "derived_set",
    "generated_set",
    "external_wordlist",
    "reference",
}
COMPOSABLE_KINDS = {"atom_set", "derived_set", "generated_set"}


@dataclass(frozen=True)
class CatalogEntry:
    id: str
    name: str
    domain: str
    kind: str
    source: str
    path: str
    tags: tuple[str, ...]
    description: str


def _from_mapping(data: dict[str, Any], origin: Path) -> CatalogEntry:
    required = ("id", "name", "domain", "kind", "source", "path", "description")
    allowed = {*required, "tags"}
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ComposerError(
            f"Catalog entry in {origin} uses unsupported fields: {', '.join(unknown)}"
        )
    missing = [key for key in required if not data.get(key)]
    if missing:
        raise ComposerError(f"Catalog entry in {origin} is missing: {', '.join(missing)}")

    entry_id = str(data["id"])
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", entry_id):
        raise ComposerError(
            f"Catalog entry ID must use lowercase letters, numbers, underscores, or hyphens: "
            f"{entry_id!r}"
        )

    kind = str(data["kind"])
    if kind not in ALLOWED_KINDS:
        raise ComposerError(
            f"Catalog entry {data['id']!r} uses unsupported kind {kind!r}."
        )
    domain = str(data["domain"])
    if domain not in ACTIVE_DOMAINS:
        raise ComposerError(
            f"Catalog entry {data['id']!r} uses unsupported domain {domain!r}."
        )
    tags = data.get("tags", [])
    if not isinstance(tags, list):
        raise ComposerError(f"Catalog entry {data['id']!r} tags must be a list.")
    return CatalogEntry(
        id=entry_id,
        name=str(data["name"]),
        domain=domain,
        kind=kind,
        source=str(data["source"]),
        path=str(data["path"]),
        tags=tuple(str(tag) for tag in tags if isinstance(tag, (str, int))),
        description=str(data["description"]),
    )


def load_catalog() -> list[CatalogEntry]:
    entries: list[CatalogEntry] = []
    catalog_root = resource_root() / "catalog"
    for domain in ACTIVE_DOMAINS:
        path = catalog_root / f"{domain}.yml"
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise ComposerError(f"Could not load catalog {path}: {exc}") from exc
        items = data.get("entries", []) if isinstance(data, dict) else data
        if not isinstance(items, list):
            raise ComposerError(f"Catalog file must contain an entries list: {path}")
        entries.extend(_from_mapping(item, path) for item in items if isinstance(item, dict))

    ids = [entry.id for entry in entries]
    if len(ids) != len(set(ids)):
        raise ComposerError("Catalog contains duplicate dictionary IDs.")
    return entries


def get_entry(dictionary_id: str) -> CatalogEntry:
    for entry in load_catalog():
        if entry.id == dictionary_id:
            return entry
    raise ComposerError(f"Dictionary not found: {dictionary_id}")


def list_entries(
    *,
    domain: str | None = None,
    kind: str | None = None,
    tag: str | None = None,
    include_references: bool = False,
) -> list[CatalogEntry]:
    entries = load_catalog()
    if not include_references:
        entries = [entry for entry in entries if entry.kind != "reference"]
    if domain:
        entries = [entry for entry in entries if entry.domain == domain]
    if kind:
        entries = [entry for entry in entries if entry.kind == kind]
    if tag:
        wanted = tag.casefold()
        entries = [entry for entry in entries if wanted in {item.casefold() for item in entry.tags}]
    return entries


def resolve_entry(entry: CatalogEntry) -> str | None:
    if entry.path.startswith(("https://", "http://")):
        return entry.path
    if entry.source == "local":
        path = resolve_resource(entry.path)
        return str(path) if path.exists() else None
    for source in load_sources():
        if source.name.casefold() == entry.source.casefold():
            root = source.resolved_path
            candidate = (root / entry.path).resolve()
            if not candidate.is_relative_to(root):
                return None
            if candidate.exists():
                return str(candidate)
    return None


def _tokens(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value.casefold())


def _match_score(entry: CatalogEntry, terms: list[str]) -> int | None:
    fields = {
        "id": entry.id.casefold(),
        "name": entry.name.casefold(),
        "domain": entry.domain.casefold(),
        "kind": entry.kind.casefold(),
        "tags": " ".join(entry.tags).casefold(),
        "description": entry.description.casefold(),
        "path": entry.path.casefold(),
    }
    searchable = " ".join(fields.values())
    if not all(term in searchable for term in terms):
        return None

    weights = {
        "id": 12,
        "domain": 10,
        "tags": 10,
        "name": 8,
        "kind": 6,
        "description": 4,
        "path": 2,
    }
    return sum(
        max(weight for field, weight in weights.items() if term in fields[field])
        for term in terms
    )


def search_catalog(
    query: str,
    *,
    limit: int = 50,
    include_references: bool = False,
) -> list[CatalogEntry]:
    terms = _tokens(query)
    if not terms:
        return []

    scored: list[tuple[int, CatalogEntry]] = []
    for entry in load_catalog():
        if entry.kind == "reference" and not include_references:
            continue
        score = _match_score(entry, terms)
        if score is not None:
            scored.append((score, entry))
    scored.sort(key=lambda item: (-item[0], item[1].id))
    return [entry for _, entry in scored[:limit]]
