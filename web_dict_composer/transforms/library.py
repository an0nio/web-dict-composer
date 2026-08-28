from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable
from urllib.parse import quote_from_bytes


Transform = Callable[[str, dict[str, object]], tuple[str, ...]]

FILE_UPLOAD_STORAGE_PRESETS = (
    "common_web",
    "posix",
    "windows",
    "unicode",
    "extension_rewrite",
    "collision_suffixes",
    "length_limit",
)

_PERCENT_BYTE = re.compile(rb"%([0-9A-Fa-f]{2})")
_PERCENT_ESCAPE = re.compile(r"%[0-9A-F]{2}")
_ASCII_WHITESPACE = re.compile(r"[\t\n\r\f\v ]+")
_WINDOWS_INVALID = re.compile(r'[<>:"/\\|?*]')
_WINDOWS_RESERVED = re.compile(
    r"^(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?$",
    re.IGNORECASE,
)


def _slash_to_backslash(value: str, _: dict[str, object]) -> tuple[str, ...]:
    return (value.replace("/", "\\"),)


def _repeat(value: str, options: dict[str, object]) -> tuple[str, ...]:
    minimum = int(options.get("min", 1))
    maximum = int(options["max"])
    return tuple(value * count for count in range(minimum, maximum + 1))


def _ordered_add(values: list[str], seen: set[str], value: str) -> None:
    if value and value not in seen:
        seen.add(value)
        values.append(value)


def _percent_decode_once(value: bytes) -> bytes:
    return _PERCENT_BYTE.sub(lambda match: bytes((int(match.group(1), 16),)), value)


def _decoded_bytes(value: str, depth: int) -> tuple[bytes, ...]:
    variants = [value.encode("utf-8")]
    for _ in range(depth):
        decoded = _percent_decode_once(variants[-1])
        if decoded == variants[-1]:
            break
        variants.append(decoded)
    return tuple(variants)


def _decoded_text(value: str, depth: int) -> tuple[str, ...]:
    variants: list[str] = []
    seen: set[str] = set()
    for raw in _decoded_bytes(value, depth):
        try:
            decoded = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        _ordered_add(variants, seen, decoded)
    return tuple(variants)


def _lower_percent_hex(value: str) -> str:
    return _PERCENT_ESCAPE.sub(lambda match: match.group(0).lower(), value)


def _canonical_request_path(value: bytes, target: str) -> str:
    safe = "/-._~" if target in {"relative_path", "object_key"} else "-._~"
    return quote_from_bytes(value, safe=safe)


def _remove_dot_segments_without_parent_resolution(value: str) -> str:
    normalized = value
    while "/./" in normalized:
        normalized = normalized.replace("/./", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized.endswith("/."):
        normalized = normalized[:-2] + "/"
    return normalized


def _request_path_variants(value: str, target: str, depth: int) -> tuple[str, ...]:
    variants: list[str] = []
    seen: set[str] = set()

    unsafe = any(
        _is_ascii_control(character) or character.isspace() or ord(character) > 0x7E
        for character in value
    )
    unsafe = unsafe or any(character in value for character in "?#")
    if target == "segment":
        unsafe = unsafe or "/" in value or "\\" in value
    if not unsafe:
        _ordered_add(variants, seen, value)

    pathish_values = [value]
    if target in {"relative_path", "object_key"}:
        pathish_values.extend(
            (
                value.replace("\\", "/"),
                _remove_dot_segments_without_parent_resolution(value.replace("\\", "/")),
            )
        )

    for pathish in dict.fromkeys(pathish_values):
        for raw in _decoded_bytes(pathish, depth):
            quoted = _canonical_request_path(raw, target)
            _ordered_add(variants, seen, quoted)
            _ordered_add(variants, seen, _lower_percent_hex(quoted))
    return tuple(variants)


def _is_ascii_control(character: str) -> bool:
    codepoint = ord(character)
    return codepoint < 0x20 or codepoint == 0x7F


def _remove_controls(value: str) -> str:
    return "".join(character for character in value if not _is_ascii_control(character))


def _replace_controls(value: str, replacement: str) -> str:
    return "".join(
        replacement if _is_ascii_control(character) else character for character in value
    )


def _truncate_at_control(value: str) -> str:
    positions = [index for index, character in enumerate(value) if _is_ascii_control(character)]
    return value if not positions else value[: min(positions)]


def _basename(value: str, separators: str) -> str:
    positions = [value.rfind(separator) for separator in separators]
    return value[max(positions) + 1 :]


def _replace_non_filename_characters(value: str, replacement: str) -> str:
    return "".join(
        character if character.isalnum() or character in ".-_" else replacement
        for character in value
    )


def _path_prefix_and_segment(value: str) -> tuple[str, str]:
    position = max(value.rfind("/"), value.rfind("\\"))
    return value[: position + 1], value[position + 1 :]


def _lowercase_extension(value: str) -> str:
    prefix, segment = _path_prefix_and_segment(value)
    if "." not in segment[1:]:
        return value
    stem, extension = segment.rsplit(".", 1)
    return f"{prefix}{stem}.{extension.lower()}"


def _ascii_transliteration(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(character for character in decomposed if not unicodedata.combining(character))


def _common_web_hypotheses(value: str) -> tuple[str, ...]:
    no_controls = _remove_controls(value)
    return (
        _basename(value, "/\\"),
        no_controls,
        _replace_controls(value, "_"),
        _truncate_at_control(value),
        value.strip(" .\t\n\r\f\v\x00"),
        _ASCII_WHITESPACE.sub("-", no_controls),
        _ASCII_WHITESPACE.sub("_", no_controls),
        _ASCII_WHITESPACE.sub("", no_controls),
        value.replace("+", "-"),
        _replace_non_filename_characters(no_controls, ""),
        _replace_non_filename_characters(no_controls, "_"),
        re.sub(r"\.{2,}", ".", no_controls),
        re.sub(r"[-_]{2,}", "_", no_controls),
        no_controls.strip("._- "),
        value.replace("\\", ""),
        value.replace("\\", "/"),
        value.lower(),
        _lowercase_extension(value),
    )


def _posix_hypotheses(value: str) -> tuple[str, ...]:
    return (
        _basename(value, "/"),
        value.replace("/", ""),
        value.replace("/", "_"),
        value.replace("\x00", ""),
    )


def _windows_reserved_variants(value: str) -> tuple[str, ...]:
    prefix, segment = _path_prefix_and_segment(value)
    if not _WINDOWS_RESERVED.fullmatch(segment.rstrip(" .")):
        return ()
    return (f"{prefix}_{segment}", f"{prefix}{segment}_")


def _windows_hypotheses(value: str) -> tuple[str, ...]:
    basename = _basename(value, "/\\")
    no_controls = _remove_controls(value)
    invalid_removed = _WINDOWS_INVALID.sub("", no_controls)
    invalid_replaced = _WINDOWS_INVALID.sub("_", no_controls)
    variants = [
        basename,
        invalid_removed,
        invalid_replaced,
        no_controls.rstrip(" ."),
        no_controls.strip(" ."),
        no_controls.lower(),
    ]
    variants.extend(_windows_reserved_variants(no_controls))
    return tuple(variants)


def _unicode_hypotheses(value: str) -> tuple[str, ...]:
    return (
        unicodedata.normalize("NFC", value),
        unicodedata.normalize("NFD", value),
        unicodedata.normalize("NFKC", value),
        unicodedata.normalize("NFKD", value),
        _ascii_transliteration(value),
    )


def _stem_and_extension(segment: str) -> tuple[str, str]:
    if "." not in segment[1:]:
        return segment, ""
    stem, suffix = segment.rsplit(".", 1)
    return stem, f".{suffix}"


def _extension_hypotheses(value: str, extensions: tuple[str, ...]) -> tuple[str, ...]:
    prefix, segment = _path_prefix_and_segment(value)
    stem, _ = _stem_and_extension(segment)
    variants = []
    for extension in extensions:
        suffix = "." + extension.lstrip(".")
        variants.extend((f"{prefix}{stem}{suffix}", f"{prefix}{segment}{suffix}"))
    return tuple(variants)


def _collision_hypotheses(value: str, number: int) -> tuple[str, ...]:
    prefix, segment = _path_prefix_and_segment(value)
    stem, extension = _stem_and_extension(segment)
    return tuple(
        f"{prefix}{stem}{suffix}{extension}"
        for suffix in (f"-{number}", f"_{number}", f"({number})")
    )


def _truncate_utf8(value: str, maximum: int) -> str:
    while value and len(value.encode("utf-8")) > maximum:
        value = value[:-1]
    return value


def _length_hypothesis(value: str, maximum: int) -> str:
    prefix, segment = _path_prefix_and_segment(value)
    stem, extension = _stem_and_extension(segment)
    extension_bytes = len(extension.encode("utf-8"))
    if extension_bytes >= maximum:
        return prefix + _truncate_utf8(segment, maximum)
    return prefix + _truncate_utf8(stem, maximum - extension_bytes) + extension


def _storage_hypotheses(value: str, options: dict[str, object]) -> tuple[str, ...]:
    depth = int(options.get("decode_depth", 2))
    variant_limit = int(options.get("max_variants_per_input", 512))
    presets = {str(item) for item in options.get("presets", [])}
    seeds = tuple(dict.fromkeys(_decoded_text(value, depth)))
    families: list[list[str]] = [list(seeds)]

    builders: list[Callable[[str], tuple[str, ...]]] = []
    if "common_web" in presets:
        builders.append(_common_web_hypotheses)
    if "posix" in presets:
        builders.append(_posix_hypotheses)
    if "windows" in presets:
        builders.append(_windows_hypotheses)
    if "unicode" in presets:
        builders.append(_unicode_hypotheses)
    for builder in builders:
        family: list[str] = []
        family_seen: set[str] = set()
        for seed in seeds:
            if len(family) >= variant_limit:
                break
            for candidate in builder(seed):
                _ordered_add(family, family_seen, candidate)
                if len(family) >= variant_limit:
                    break
        families.append(family)

    branch_inputs = tuple(dict.fromkeys(candidate for family in families for candidate in family))
    extension_candidates: list[str] = []
    if "extension_rewrite" in presets:
        extension_seen: set[str] = set()
        extensions = tuple(str(item) for item in options.get("forced_extensions", []))
        for seed in branch_inputs:
            if len(extension_candidates) >= variant_limit:
                break
            for candidate in _extension_hypotheses(seed, extensions):
                _ordered_add(extension_candidates, extension_seen, candidate)
                if len(extension_candidates) >= variant_limit:
                    break
        families.append(extension_candidates)

    collision_candidates: list[str] = []
    if "collision_suffixes" in presets:
        collision_seen: set[str] = set()
        collision_limit = int(options.get("collision_suffix_limit", 3))
        collision_inputs = tuple(dict.fromkeys((*extension_candidates, *branch_inputs)))
        for number in range(1, collision_limit + 1):
            for seed in collision_inputs:
                for candidate in _collision_hypotheses(seed, number):
                    _ordered_add(collision_candidates, collision_seen, candidate)
                    if len(collision_candidates) >= variant_limit:
                        break
                if len(collision_candidates) >= variant_limit:
                    break
            if len(collision_candidates) >= variant_limit:
                break
        families.append(collision_candidates)

    if "length_limit" in presets:
        length_candidates: list[str] = []
        length_seen: set[str] = set()
        maximum = int(options.get("filename_max_bytes", 255))
        length_inputs = tuple(
            dict.fromkeys((*collision_candidates, *extension_candidates, *branch_inputs))
        )
        for seed in length_inputs:
            _ordered_add(length_candidates, length_seen, _length_hypothesis(seed, maximum))
            if len(length_candidates) >= variant_limit:
                break
        families.append(length_candidates)

    variants: list[str] = []
    seen: set[str] = set()
    positions = [0] * len(families)
    while len(variants) < variant_limit:
        progressed = False
        for index, family in enumerate(families):
            while positions[index] < len(family):
                candidate = family[positions[index]]
                positions[index] += 1
                if candidate in seen or not candidate:
                    continue
                _ordered_add(variants, seen, candidate)
                progressed = True
                break
            if len(variants) >= variant_limit:
                break
        if not progressed:
            break
    return tuple(variants)


def _file_upload_request_path_variants(
    value: str, options: dict[str, object]
) -> tuple[str, ...]:
    source = str(options.get("source", "stored"))
    target = str(options.get("target", "segment"))
    depth = int(options.get("decode_depth", 2))
    limit = int(options.get("max_variants_per_input", 512))
    storage_values = _storage_hypotheses(value, options) if source == "accepted" else (value,)

    variants: list[str] = []
    seen: set[str] = set()
    for storage_value in storage_values:
        for candidate in _request_path_variants(storage_value, target, depth):
            _ordered_add(variants, seen, candidate)
            if len(variants) >= limit:
                return tuple(variants)
    return tuple(variants)


TRANSFORMS: dict[str, Transform] = {
    "slash_to_backslash": _slash_to_backslash,
    "repeat": _repeat,
    "file_upload_request_path_variants": _file_upload_request_path_variants,
}


def validate_transform_spec(spec: dict[str, object]) -> list[str]:
    name = spec.get("name")
    if name not in TRANSFORMS:
        return [f"Unknown transform: {name!r}"]
    if name == "repeat":
        minimum = spec.get("min", 1)
        maximum = spec.get("max")
        if (
            not isinstance(minimum, int)
            or isinstance(minimum, bool)
            or not isinstance(maximum, int)
            or isinstance(maximum, bool)
            or minimum <= 0
            or maximum < minimum
        ):
            return ["repeat transform requires positive integer min/max with min <= max."]
        return []
    if name != "file_upload_request_path_variants":
        return []

    errors: list[str] = []
    allowed = {
        "name",
        "include_original",
        "guided",
        "source",
        "target",
        "decode_depth",
        "presets",
        "forced_extensions",
        "collision_suffix_limit",
        "filename_max_bytes",
        "max_variants_per_input",
    }
    unsupported = sorted(set(spec) - allowed)
    if unsupported:
        errors.append(
            "file_upload_request_path_variants uses unsupported options: "
            + ", ".join(unsupported)
        )
    if spec.get("source", "stored") not in {"stored", "accepted"}:
        errors.append("file_upload_request_path_variants.source must be stored or accepted.")
    if spec.get("target", "segment") not in {"segment", "relative_path", "object_key"}:
        errors.append(
            "file_upload_request_path_variants.target must be segment, relative_path, "
            "or object_key."
        )
    for key, default, upper in (
        ("decode_depth", 2, 4),
        ("collision_suffix_limit", 3, 100),
        ("filename_max_bytes", 255, 4096),
        ("max_variants_per_input", 512, 5000),
    ):
        value = spec.get(key, default)
        minimum = 0 if key == "decode_depth" else 1
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < minimum
            or value > upper
        ):
            errors.append(f"file_upload_request_path_variants.{key} is outside its valid range.")
    presets = spec.get("presets", [])
    if not isinstance(presets, list) or not all(isinstance(item, str) for item in presets):
        errors.append("file_upload_request_path_variants.presets must be a list of names.")
        selected_presets: set[str] = set()
    else:
        selected_presets = set(presets)
        unknown = sorted(selected_presets - set(FILE_UPLOAD_STORAGE_PRESETS))
        if unknown:
            errors.append("Unknown file upload storage presets: " + ", ".join(unknown))
        if len(presets) != len(selected_presets):
            errors.append("file_upload_request_path_variants.presets must not contain duplicates.")
    extensions = spec.get("forced_extensions", [])
    if not isinstance(extensions, list) or not all(
        isinstance(item, str)
        and item.lstrip(".")
        and not any(separator in item for separator in "/\\")
        for item in extensions
    ):
        errors.append(
            "file_upload_request_path_variants.forced_extensions must be extension names."
        )
    if "extension_rewrite" in selected_presets and not extensions:
        errors.append("extension_rewrite requires at least one forced_extensions value.")
    for key in ("guided", "include_original"):
        if key in spec and not isinstance(spec[key], bool):
            errors.append(f"file_upload_request_path_variants.{key} must be true or false.")
    if spec.get("include_original") is True:
        errors.append(
            "file_upload_request_path_variants generates safe original candidates itself; "
            "include_original must be false."
        )
    return errors


def apply_transforms(value: str, specs: list[dict[str, object]]) -> tuple[str, ...]:
    values = (value,)
    for spec in specs:
        transform = TRANSFORMS[str(spec["name"])]
        transformed: list[str] = []
        include_original = bool(spec.get("include_original", False))
        for current in values:
            if include_original:
                transformed.append(current)
            transformed.extend(transform(current, spec))
        values = tuple(dict.fromkeys(transformed))
    return values


def transform_upper_bound(specs: list[dict[str, object]]) -> int:
    multiplier = 1
    for spec in specs:
        if spec.get("name") == "repeat":
            variants = int(spec["max"]) - int(spec.get("min", 1)) + 1
        elif spec.get("name") == "file_upload_request_path_variants":
            variants = int(spec.get("max_variants_per_input", 512))
        else:
            variants = 1
        if spec.get("include_original", False):
            variants += 1
        multiplier *= variants
    return multiplier
