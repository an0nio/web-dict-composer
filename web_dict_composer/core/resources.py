from __future__ import annotations

import os
import sys
from pathlib import Path

from web_dict_composer.core.errors import ComposerError, ProfileError


RESOURCE_MARKERS = ("catalog", "profiles", "sets")
ACTIVE_DOMAINS = ("file_upload", "lfi")


def _looks_like_root(path: Path) -> bool:
    return path.is_dir() and all((path / marker).is_dir() for marker in RESOURCE_MARKERS)


def resource_root() -> Path:
    """Locate resources in a checkout or in the wheel's shared-data directory."""
    configured = os.environ.get("WEB_DICT_COMPOSER_ROOT")
    candidates: list[Path] = []
    if configured:
        candidates.append(Path(configured).expanduser())

    candidates.extend([Path.cwd(), *Path.cwd().parents])
    package_parent = Path(__file__).resolve().parents[2]
    candidates.extend([package_parent, *package_parent.parents])
    candidates.append(Path(sys.prefix) / "share" / "web-dict-composer")

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in seen and _looks_like_root(resolved):
            return resolved
        seen.add(resolved)
    raise ComposerError(
        "Could not locate catalog, profiles, and sets. Set WEB_DICT_COMPOSER_ROOT."
    )


def resolve_resource(relative_path: str | Path) -> Path:
    root = resource_root().resolve()
    candidate = (root / relative_path).resolve()
    if not candidate.is_relative_to(root):
        raise ProfileError(f"Resource path escapes the project root: {relative_path}")
    return candidate


def profile_files(domain: str | None = None) -> list[Path]:
    base = resource_root() / "profiles"
    domains = (domain,) if domain else ACTIVE_DOMAINS
    files: list[Path] = []
    for active_domain in domains:
        directory = base / active_domain
        if directory.is_dir():
            files.extend([*directory.glob("*.yml"), *directory.glob("*.yaml")])
    return sorted(files)


def resolve_profile(reference: str | Path) -> Path:
    raw = Path(reference).expanduser()
    if raw.is_file():
        return raw.resolve()

    rooted = resolve_resource(raw)
    if rooted.is_file():
        return rooted

    normalized = str(reference).replace("\\", "/")
    normalized = normalized.removeprefix("profiles/")
    normalized = normalized.removesuffix(".yaml").removesuffix(".yml")
    matches = []
    for profile in profile_files():
        relative = profile.relative_to(resource_root() / "profiles").as_posix()
        relative_no_suffix = relative.rsplit(".", 1)[0]
        full_id = f"{profile.parent.name}_{profile.stem}"
        if normalized in {profile.stem, relative_no_suffix, full_id}:
            matches.append(profile)
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ProfileError(
            f"Ambiguous profile '{reference}'. Use a domain/name reference."
        )
    raise ProfileError(f"Profile not found: {reference}")
