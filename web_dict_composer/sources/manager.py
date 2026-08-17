from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from web_dict_composer.core.config import atomic_json_write, config_file, load_json
from web_dict_composer.core.errors import SourceError


@dataclass(frozen=True)
class DictionarySource:
    name: str
    path: str

    @property
    def resolved_path(self) -> Path:
        return Path(self.path).expanduser().resolve()


def looks_like_seclists(path: Path) -> bool:
    path = path.expanduser().resolve()
    return (
        path.is_dir()
        and (path / "Discovery").is_dir()
        and (path / "Fuzzing").is_dir()
        and ((path / "README.md").is_file() or path.name.casefold() == "seclists")
    )


def load_sources() -> list[DictionarySource]:
    data = load_json(config_file(), {"sources": []})
    result = []
    for item in data.get("sources", []) if isinstance(data, dict) else []:
        if isinstance(item, dict) and item.get("name") and item.get("path"):
            result.append(
                DictionarySource(
                    name=str(item["name"]),
                    path=str(item["path"]),
                )
            )
    return result


def save_sources(sources: list[DictionarySource]) -> None:
    unique: dict[tuple[str, str], DictionarySource] = {}
    for source in sources:
        key = (source.name.casefold(), str(source.resolved_path))
        unique[key] = source
    ordered = sorted(unique.values(), key=lambda item: (item.name.casefold(), item.path))
    atomic_json_write(config_file(), {"schema_version": 1, "sources": [asdict(x) for x in ordered]})


def _candidate_paths() -> list[Path]:
    candidates: list[Path] = []
    configured = os.environ.get("SECLISTS_PATH")
    if configured:
        candidates.extend(Path(item).expanduser() for item in configured.split(os.pathsep) if item)
    candidates.extend(
        Path(item).expanduser()
        for item in (
            "/usr/share/seclists",
            "/usr/share/wordlists/seclists",
            "/opt/SecLists",
            "/var/lib/seclists",
            "/wordlists/SecLists",
            "/data/SecLists",
            "/app/SecLists",
            "~/SecLists",
            "~/wordlists/SecLists",
            "~/.local/share/SecLists",
        )
    )
    shallow_parents = [
        Path("/usr/share"),
        Path("/usr/share/wordlists"),
        Path("/opt"),
        Path.home(),
        Path.home() / "wordlists",
        Path.home() / ".local" / "share",
    ]
    for parent in shallow_parents:
        try:
            candidates.extend(
                child for child in parent.iterdir() if child.name.casefold() == "seclists"
            )
        except (OSError, PermissionError):
            continue
    return candidates


def scan_seclists(*, persist: bool = True) -> list[DictionarySource]:
    discovered: list[DictionarySource] = []
    seen: set[Path] = set()
    for candidate in _candidate_paths():
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved in seen or not looks_like_seclists(resolved):
            continue
        seen.add(resolved)
        discovered.append(DictionarySource("seclists", str(resolved)))
    if persist and discovered:
        existing = load_sources()
        known_paths = {(item.name.casefold(), item.resolved_path) for item in existing}
        additions = [
            item
            for item in discovered
            if (item.name.casefold(), item.resolved_path) not in known_paths
        ]
        save_sources([*existing, *additions])
    return discovered


def add_source(name: str, path: str | Path) -> DictionarySource:
    normalized_name = name.strip().casefold()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", normalized_name):
        raise SourceError("Source name must use letters, numbers, underscores, or hyphens.")
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_dir():
        raise SourceError(f"Source path is not a directory: {resolved}")
    if normalized_name == "seclists" and not looks_like_seclists(resolved):
        raise SourceError(
            f"Path does not look like SecLists (Discovery/ and Fuzzing/ are required): {resolved}"
        )
    source = DictionarySource(normalized_name, str(resolved))
    existing = [
        item
        for item in load_sources()
        if not (item.name.casefold() == normalized_name and item.resolved_path == resolved)
    ]
    save_sources([*existing, source])
    return source
