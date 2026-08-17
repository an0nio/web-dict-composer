from __future__ import annotations

import itertools
import math
from dataclasses import asdict, dataclass
from typing import Iterator

from web_dict_composer.core.errors import SafetyLimitError
from web_dict_composer.core.profile import PLACEHOLDER, LoadedSet, Profile, load_sets
from web_dict_composer.transforms.library import apply_transforms, transform_upper_bound


@dataclass(frozen=True)
class PatternEstimate:
    pattern: str
    combinations: int


@dataclass(frozen=True)
class Estimate:
    profile: str
    domain: str
    set_counts: dict[str, int]
    patterns: tuple[PatternEstimate, ...]
    raw_combinations: int
    transform_upper_bound: int
    expanded_upper_bound: int
    estimated_after_filters_and_dedupe: int
    max_outputs: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class Composition:
    values: list[str]
    accepted_before_dedupe: int
    duplicates_removed: int
    truncated: bool
    sets: dict[str, LoadedSet]
    estimate: Estimate


def _placeholder_names(pattern: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(PLACEHOLDER.findall(pattern)))


def _pattern_combinations(pattern: str, sets: dict[str, LoadedSet]) -> int:
    names = _placeholder_names(pattern)
    return math.prod(sets[name].count for name in names)


def _iter_pattern(pattern: str, sets: dict[str, LoadedSet]) -> Iterator[str]:
    names = _placeholder_names(pattern)
    value_lists = [sets[name].values for name in names]
    for combination in itertools.product(*value_lists):
        yield pattern.format_map(dict(zip(names, combination)))


def _passes_length(value: str, profile: Profile) -> bool:
    maximum = profile.filters.get("max_length")
    return maximum is None or len(value) <= int(maximum)


def estimate_profile(profile: Profile, sample_limit: int = 2_000) -> Estimate:
    sets = load_sets(profile)
    pattern_estimates = tuple(
        PatternEstimate(pattern=pattern, combinations=_pattern_combinations(pattern, sets))
        for pattern in profile.patterns
    )
    raw = sum(item.combinations for item in pattern_estimates)
    multiplier = transform_upper_bound(profile.transforms)
    expanded = raw * multiplier

    sampled_base = 0
    sampled_expanded = 0
    sampled_accepted = 0
    unique: set[str] = set()
    for pattern in profile.patterns:
        for candidate in _iter_pattern(pattern, sets):
            if sampled_base >= sample_limit:
                break
            sampled_base += 1
            variants = apply_transforms(candidate, profile.transforms)
            sampled_expanded += len(variants)
            for value in variants:
                if _passes_length(value, profile):
                    sampled_accepted += 1
                    unique.add(value)
        if sampled_base >= sample_limit:
            break

    if sampled_expanded == 0:
        approximate = 0
    else:
        accepted = len(unique) if profile.filters.get("dedupe", True) else sampled_accepted
        approximate = round(expanded * (accepted / sampled_expanded))
        if sampled_base >= raw:
            approximate = accepted

    maximum = int(profile.filters.get("max_outputs", 50_000))
    return Estimate(
        profile=profile.id,
        domain=profile.domain,
        set_counts={name: item.count for name, item in sets.items()},
        patterns=pattern_estimates,
        raw_combinations=raw,
        transform_upper_bound=multiplier,
        expanded_upper_bound=expanded,
        estimated_after_filters_and_dedupe=approximate,
        max_outputs=maximum,
    )


def compose(profile: Profile, *, force: bool = False) -> Composition:
    sets = load_sets(profile)
    estimate = estimate_profile(profile)
    maximum = estimate.max_outputs
    if estimate.expanded_upper_bound > maximum and not force:
        raise SafetyLimitError(
            f"Estimated upper bound ({estimate.expanded_upper_bound:,}) exceeds "
            f"filters.max_outputs ({maximum:,}). Refine the profile or pass --force "
            "to generate a clearly marked, capped result."
        )

    dedupe = bool(profile.filters.get("dedupe", True))
    seen: set[str] = set()
    values: list[str] = []
    transformed = accepted = duplicates = 0
    truncated = False

    for pattern in profile.patterns:
        for candidate in _iter_pattern(pattern, sets):
            for value in apply_transforms(candidate, profile.transforms):
                transformed += 1
                if not _passes_length(value, profile):
                    continue
                accepted += 1
                if dedupe and value in seen:
                    duplicates += 1
                    continue
                seen.add(value)
                values.append(value)
                if len(values) >= maximum:
                    truncated = transformed < estimate.expanded_upper_bound
                    break
            if len(values) >= maximum:
                break
        if len(values) >= maximum:
            break

    return Composition(
        values=values,
        accepted_before_dedupe=accepted,
        duplicates_removed=duplicates,
        truncated=truncated,
        sets=sets,
        estimate=estimate,
    )
