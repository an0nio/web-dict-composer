from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from web_dict_composer.catalog.service import COMPOSABLE_KINDS, get_entry, resolve_entry
from web_dict_composer.core.errors import ComposerError, ProfileError
from web_dict_composer.core.resources import resolve_profile, resolve_resource
from web_dict_composer.transforms.library import TRANSFORMS


PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


@dataclass(frozen=True)
class LoadedSet:
    name: str
    values: tuple[str, ...]
    source: str
    catalog_ids: tuple[str, ...] = ()

    @property
    def count(self) -> int:
        return len(self.values)


@dataclass
class Profile:
    path: Path
    id: str
    domain: str
    description: str
    sets_spec: dict[str, dict[str, Any]]
    patterns: list[str]
    transforms: list[dict[str, Any]] = field(default_factory=list)
    filters: dict[str, Any] = field(default_factory=dict)
    output: dict[str, Any] = field(default_factory=dict)

def _normalize_transforms(raw: Any) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ProfileError("'transforms' must be a list.")
    normalized = []
    for item in raw:
        if isinstance(item, str):
            normalized.append({"name": item})
        elif isinstance(item, dict):
            normalized.append(dict(item))
        else:
            raise ProfileError("Each transform must be a name or a mapping.")
    return normalized


def load_profile(reference: str | Path) -> Profile:
    path = resolve_profile(reference)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ProfileError(f"Could not load profile {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ProfileError(f"Profile must contain a YAML mapping: {path}")
    allowed_fields = {
        "id",
        "domain",
        "description",
        "sets",
        "patterns",
        "transforms",
        "filters",
        "output",
    }
    unknown_fields = sorted(set(data) - allowed_fields)
    if unknown_fields:
        raise ProfileError(
            f"Profile uses unsupported fields: {', '.join(unknown_fields)}"
        )

    profile = Profile(
        path=path,
        id=str(data.get("id", "")),
        domain=str(data.get("domain", "")),
        description=str(data.get("description", "")),
        sets_spec=data.get("sets") if isinstance(data.get("sets"), dict) else {},
        patterns=data.get("patterns") if isinstance(data.get("patterns"), list) else [],
        transforms=_normalize_transforms(data.get("transforms")),
        filters=data.get("filters") if isinstance(data.get("filters"), dict) else {},
        output=data.get("output") if isinstance(data.get("output"), dict) else {},
    )
    errors = validate_profile(profile)
    if errors:
        formatted = "\n  - ".join(errors)
        raise ProfileError(f"Invalid profile {path}:\n  - {formatted}")
    return profile


def _validate_catalog_reference(
    dictionary_id: str,
    profile: Profile,
    set_name: str,
) -> list[str]:
    try:
        entry = get_entry(dictionary_id)
    except ComposerError as exc:
        return [str(exc)]
    errors = []
    if entry.kind not in COMPOSABLE_KINDS:
        errors.append(
            f"Set '{set_name}' cannot use catalog entry '{entry.id}' of kind '{entry.kind}'."
        )
    if entry.domain != profile.domain:
        errors.append(
            f"Set '{set_name}' uses '{entry.id}' from domain '{entry.domain}', "
            f"not '{profile.domain}'."
        )
    if not resolve_entry(entry):
        errors.append(f"Catalog set is not available: {entry.id} ({entry.path})")
    return errors


def validate_profile(profile: Profile) -> list[str]:
    errors: list[str] = []
    if not profile.id or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", profile.id):
        errors.append("'id' must use lowercase letters, numbers, underscores, or hyphens.")
    if profile.domain not in {"file_upload", "lfi"}:
        errors.append("'domain' must be 'file_upload' or 'lfi'.")
    if not profile.description:
        errors.append("'description' is required.")
    if not profile.sets_spec:
        errors.append("At least one set is required.")
    if not profile.patterns or not all(isinstance(item, str) for item in profile.patterns):
        errors.append("'patterns' must contain at least one string.")

    for name, spec in profile.sets_spec.items():
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(name)):
            errors.append(f"Invalid set name: {name}")
            continue
        if not isinstance(spec, dict):
            errors.append(f"Set '{name}' must be a mapping.")
            continue
        unsupported = sorted(set(spec) - {"inline", "file", "catalog", "catalogs", "repeat"})
        if unsupported:
            errors.append(
                f"Set '{name}' uses unsupported fields: {', '.join(unsupported)}"
            )
        choices = [key for key in ("inline", "file", "catalog", "catalogs") if key in spec]
        if len(choices) != 1:
            errors.append(
                f"Set '{name}' must define exactly one of inline, file, catalog, or catalogs."
            )
        elif "inline" in spec and (
            not isinstance(spec["inline"], list)
            or not spec["inline"]
            or not all(isinstance(value, (str, int, float)) for value in spec["inline"])
        ):
            errors.append(f"Set '{name}'.inline must be a non-empty list of scalar values.")
        elif "file" in spec:
            try:
                path = resolve_resource(str(spec["file"]))
                if not path.is_file():
                    errors.append(f"Set '{name}' file does not exist: {spec['file']}")
            except ProfileError as exc:
                errors.append(str(exc))
        elif "catalog" in spec:
            if not isinstance(spec["catalog"], str) or not spec["catalog"]:
                errors.append(f"Set '{name}'.catalog must be a dictionary ID.")
            else:
                errors.extend(_validate_catalog_reference(spec["catalog"], profile, str(name)))
        elif "catalogs" in spec:
            references = spec["catalogs"]
            if (
                not isinstance(references, list)
                or not references
                or not all(isinstance(item, str) and item for item in references)
            ):
                errors.append(f"Set '{name}'.catalogs must be a non-empty list of IDs.")
            else:
                for dictionary_id in references:
                    errors.extend(
                        _validate_catalog_reference(dictionary_id, profile, str(name))
                    )
        if "repeat" in spec:
            repeat = spec["repeat"]
            if not isinstance(repeat, dict):
                errors.append(f"Set '{name}'.repeat must be a mapping with min and max.")
            else:
                minimum = repeat.get("min", 1)
                maximum = repeat.get("max")
                if (
                    not isinstance(minimum, int)
                    or isinstance(minimum, bool)
                    or not isinstance(maximum, int)
                    or isinstance(maximum, bool)
                    or minimum <= 0
                    or maximum < minimum
                ):
                    errors.append(
                        f"Set '{name}'.repeat requires positive integer min/max with min <= max."
                    )

    known_sets = set(profile.sets_spec)
    for pattern in profile.patterns:
        placeholders = set(PLACEHOLDER.findall(pattern))
        if not placeholders:
            errors.append(f"Pattern has no placeholders: {pattern!r}")
        unknown = placeholders - known_sets
        if unknown:
            errors.append(
                f"Pattern {pattern!r} references unknown sets: {', '.join(sorted(unknown))}"
            )

    for transform in profile.transforms:
        name = transform.get("name")
        if name not in TRANSFORMS:
            errors.append(f"Unknown transform: {name!r}")
        if name == "repeat":
            minimum = transform.get("min", 1)
            maximum = transform.get("max")
            if (
                not isinstance(minimum, int)
                or isinstance(minimum, bool)
                or not isinstance(maximum, int)
                or isinstance(maximum, bool)
                or minimum <= 0
                or maximum < minimum
            ):
                errors.append("repeat transform requires positive integer min/max with min <= max.")

    filters = profile.filters
    unsupported_filters = sorted(set(filters) - {"dedupe", "max_length", "max_outputs"})
    if unsupported_filters:
        errors.append(
            f"filters uses unsupported fields: {', '.join(unsupported_filters)}"
        )
    if "dedupe" in filters and not isinstance(filters["dedupe"], bool):
        errors.append("filters.dedupe must be true or false.")
    for key in ("max_length", "max_outputs"):
        if key in filters and (
            not isinstance(filters[key], int)
            or isinstance(filters[key], bool)
            or filters[key] <= 0
        ):
            errors.append(f"filters.{key} must be a positive integer.")
    unsupported_output = sorted(set(profile.output) - {"file", "manifest"})
    if unsupported_output:
        errors.append(
            f"output uses unsupported fields: {', '.join(unsupported_output)}"
        )
    return errors


def _read_values(path: Path) -> tuple[str, ...]:
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    values = tuple(
        line.strip()
        for line in raw_lines
        if line.strip() and not line.lstrip().startswith("#")
    )
    if not values:
        raise ProfileError(f"Set has no usable values: {path}")
    return values


def _repeat_values(values: tuple[str, ...], spec: dict[str, Any]) -> tuple[str, ...]:
    repeat = spec.get("repeat")
    if not isinstance(repeat, dict):
        return values
    minimum = int(repeat.get("min", 1))
    maximum = int(repeat["max"])
    return tuple(
        value * count
        for value in values
        for count in range(minimum, maximum + 1)
    )


def load_sets(profile: Profile) -> dict[str, LoadedSet]:
    loaded: dict[str, LoadedSet] = {}
    for name, spec in profile.sets_spec.items():
        if "inline" in spec:
            values = tuple(str(value) for value in spec["inline"])
            loaded[name] = LoadedSet(
                name=name,
                values=_repeat_values(values, spec),
                source="inline",
            )
            continue
        if "file" in spec:
            relative = str(spec["file"])
            loaded[name] = LoadedSet(
                name=name,
                values=_repeat_values(_read_values(resolve_resource(relative)), spec),
                source=relative,
            )
            continue

        catalog_ids = (
            (str(spec["catalog"]),)
            if "catalog" in spec
            else tuple(str(item) for item in spec["catalogs"])
        )
        combined: list[str] = []
        for dictionary_id in catalog_ids:
            entry = get_entry(dictionary_id)
            resolved = resolve_entry(entry)
            if not resolved or resolved.startswith(("https://", "http://")):
                raise ProfileError(f"Catalog set is not locally readable: {dictionary_id}")
            combined.extend(_read_values(Path(resolved)))
        values = _repeat_values(tuple(dict.fromkeys(combined)), spec)
        loaded[name] = LoadedSet(
            name=name,
            values=values,
            source=", ".join(catalog_ids),
            catalog_ids=catalog_ids,
        )
    return loaded
