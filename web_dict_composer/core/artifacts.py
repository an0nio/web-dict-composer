from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from web_dict_composer.core.engine import Composition, compose
from web_dict_composer.core.profile import LoadedSet, Profile


@dataclass(frozen=True)
class BuildArtifacts:
    wordlist: Path
    manifest: Path
    lines: int
    truncated: bool


def atomic_text_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temp_name, path)
    finally:
        temp_path = Path(temp_name)
        if temp_path.exists():
            temp_path.unlink()


def _paths(profile: Profile, override: str | Path | None) -> tuple[Path, Path]:
    if override:
        wordlist = Path(override).expanduser()
        stem = wordlist.with_suffix("") if wordlist.suffix else wordlist
        return wordlist, Path(f"{stem}.manifest.json")
    wordlist = Path(profile.output.get("file", f"output/{profile.id}.txt")).expanduser()
    manifest = Path(
        profile.output.get("manifest", f"output/{profile.id}.manifest.json")
    ).expanduser()
    return wordlist, manifest


def _set_reference(item: LoadedSet) -> str | list[str]:
    if not item.catalog_ids:
        return item.source
    if len(item.catalog_ids) == 1:
        return item.catalog_ids[0]
    return list(item.catalog_ids)


def _manifest(profile: Profile, result: Composition) -> dict[str, object]:
    return {
        "schema_version": 1,
        "profile": profile.id,
        "domain": profile.domain,
        "sets": {name: _set_reference(item) for name, item in result.sets.items()},
        "pattern_count": len(profile.patterns),
        "candidate_lines": result.accepted_before_dedupe,
        "output_lines": len(result.values),
        "duplicates_removed": result.duplicates_removed,
        "truncated": result.truncated,
    }


def build_artifacts(
    profile: Profile,
    *,
    output_override: str | Path | None = None,
    force: bool = False,
) -> BuildArtifacts:
    result = compose(profile, force=force)
    wordlist, manifest_path = _paths(profile, output_override)
    wordlist_content = "\n".join(result.values)
    if result.values:
        wordlist_content += "\n"
    manifest_content = json.dumps(_manifest(profile, result), indent=2, sort_keys=True) + "\n"

    atomic_text_write(wordlist, wordlist_content)
    atomic_text_write(manifest_path, manifest_content)
    return BuildArtifacts(
        wordlist=wordlist.resolve(),
        manifest=manifest_path.resolve(),
        lines=len(result.values),
        truncated=result.truncated,
    )
