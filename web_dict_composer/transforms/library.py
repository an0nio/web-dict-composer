from __future__ import annotations

from collections.abc import Callable


Transform = Callable[[str, dict[str, object]], tuple[str, ...]]


def _slash_to_backslash(value: str, _: dict[str, object]) -> tuple[str, ...]:
    return (value.replace("/", "\\"),)


def _repeat(value: str, options: dict[str, object]) -> tuple[str, ...]:
    minimum = int(options.get("min", 1))
    maximum = int(options["max"])
    return tuple(value * count for count in range(minimum, maximum + 1))


TRANSFORMS: dict[str, Transform] = {
    "slash_to_backslash": _slash_to_backslash,
    "repeat": _repeat,
}


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
        else:
            variants = 1
        if spec.get("include_original", False):
            variants += 1
        multiplier *= variants
    return multiplier
