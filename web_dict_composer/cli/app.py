from __future__ import annotations

import argparse
import itertools
import json
import os
import re
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from web_dict_composer import __version__
from web_dict_composer.catalog.service import (
    COMPOSABLE_KINDS,
    CatalogEntry,
    get_entry,
    list_entries,
    resolve_entry,
    search_catalog,
)
from web_dict_composer.core.artifacts import build_artifacts
from web_dict_composer.core.engine import Estimate, estimate_profile
from web_dict_composer.core.errors import ComposerError
from web_dict_composer.core.profile import Profile, load_profile
from web_dict_composer.core.resources import ACTIVE_DOMAINS, profile_files
from web_dict_composer.sources.manager import add_source, load_sources, scan_seclists


THEME = Theme(
    {
        "brand": "bold bright_cyan",
        "accent": "bold magenta",
        "success": "bold green",
        "warning": "bold yellow",
        "danger": "bold red",
        "muted": "dim white",
        "source.local": "bold bright_cyan",
        "source.seclists": "bold green",
        "source.external": "bold magenta",
    }
)


def _console(*, stderr: bool = False) -> Console:
    disabled = "--no-color" in sys.argv or bool(os.environ.get("NO_COLOR"))
    return Console(
        theme=THEME,
        stderr=stderr,
        highlight=False,
        color_system=None if disabled else "auto",
    )


console = _console()
error_console = _console(stderr=True)


class ColorHelpFormatter(argparse.HelpFormatter):
    """Small ANSI enhancement for interactive argparse help."""

    def start_section(self, heading: str | None) -> None:
        if heading and sys.stdout.isatty() and not os.environ.get("NO_COLOR"):
            heading = f"\033[1;36m{heading}\033[0m"
        super().start_section(heading)


def _parser() -> argparse.ArgumentParser:
    common = {"formatter_class": ColorHelpFormatter}
    parser = argparse.ArgumentParser(
        prog="web-dict-composer",
        description="Find and compose curated dictionaries for authorized web security testing.",
        epilog="It generates local files only: no requests, scanning, or exploitation.",
        **common,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output.")
    commands = parser.add_subparsers(dest="command", metavar="COMMAND")

    sources = commands.add_parser(
        "sources", help="Detect and register SecLists.", **common
    )
    source_commands = sources.add_subparsers(dest="sources_command", metavar="COMMAND")
    source_commands.add_parser(
        "scan", help="Find and register SecLists installations.", **common
    )
    source_commands.add_parser("list", help="List registered sources.", **common)
    add = source_commands.add_parser("add", help="Register a source directory.", **common)
    add.add_argument("name", help="Stable source name, currently seclists.")
    add.add_argument("path", help="Source root path.")

    dictionaries = commands.add_parser(
        "dicts", help="Browse the curated dictionary catalog.", **common
    )
    dict_commands = dictionaries.add_subparsers(dest="dicts_command", metavar="COMMAND")
    listing = dict_commands.add_parser("list", help="List catalog entries.", **common)
    listing.add_argument("--domain", choices=ACTIVE_DOMAINS)
    listing.add_argument("--kind")
    listing.add_argument("--tag")
    listing.add_argument("--include-references", action="store_true")
    search = dict_commands.add_parser(
        "search", help="Search the curated catalog.", **common
    )
    search.add_argument("query", nargs="+", help="Terms such as: file-upload php extensions")
    search.add_argument("--limit", type=int, default=50)
    search.add_argument("--include-references", action="store_true")
    show = dict_commands.add_parser("show", help="Show catalog metadata.", **common)
    show.add_argument("dictionary_id")
    path = dict_commands.add_parser(
        "path", help="Print the resolved path or reference URL.", **common
    )
    path.add_argument("dictionary_id")

    profiles = commands.add_parser(
        "profiles", help="Inspect, estimate, and build composition profiles.", **common
    )
    profile_commands = profiles.add_subparsers(dest="profiles_command", metavar="COMMAND")
    profile_list = profile_commands.add_parser("list", help="List built-in profiles.", **common)
    profile_list.add_argument("domain", nargs="?", choices=ACTIVE_DOMAINS)
    profile_show = profile_commands.add_parser("show", help="Show a profile.", **common)
    profile_show.add_argument("profile")
    profile_estimate = profile_commands.add_parser(
        "estimate", help="Estimate a profile before generation.", **common
    )
    profile_estimate.add_argument("profile")
    profile_estimate.add_argument("--json", action="store_true")
    profile_build = profile_commands.add_parser(
        "build", help="Generate a wordlist and compact manifest.", **common
    )
    profile_build.add_argument("profile")
    profile_build.add_argument("-o", "--output", help="Override the wordlist output path.")
    profile_build.add_argument(
        "--force",
        action="store_true",
        help="Permit a deterministic capped result when the estimate exceeds the hard limit.",
    )

    commands.add_parser(
        "wizard",
        help="Build a custom composition interactively.",
        **common,
    )
    commands.add_parser(
        "guided",
        help="Choose and customize a built-in profile interactively.",
        **common,
    )
    return parser


def _banner() -> None:
    console.print(
        Panel.fit(
            "[brand]web-dict-composer[/brand]\n"
            "[muted]Find clean sets. Compose bounded wordlists.[/muted]",
            border_style="bright_cyan",
        )
    )


def _source_style(source: str) -> str:
    if source == "local":
        return "source.local"
    if source == "seclists":
        return "source.seclists"
    return "source.external"


def _estimate_table(estimate: Estimate) -> None:
    summary = Table(show_header=False, box=None, padding=(0, 2))
    summary.add_column(style="muted")
    summary.add_column(style="white")
    summary.add_row("Profile", estimate.profile)
    summary.add_row("Domain", estimate.domain)
    summary.add_row("Raw combinations", f"{estimate.raw_combinations:,}")
    summary.add_row("Transform upper bound", f"× {estimate.transform_upper_bound:,}")
    summary.add_row("Expanded upper bound", f"{estimate.expanded_upper_bound:,}")
    summary.add_row(
        "Approx. after filters/dedupe",
        f"{estimate.estimated_after_filters_and_dedupe:,}",
    )
    summary.add_row("Hard output cap", f"{estimate.max_outputs:,}")
    console.print(Panel(summary, title="[brand]Build estimate[/brand]", border_style="cyan"))

    sets = Table(title="Sets", header_style="bold bright_cyan", box=None)
    sets.add_column("Name")
    sets.add_column("Entries", justify="right", style="magenta")
    for name, count in estimate.set_counts.items():
        sets.add_row(name, f"{count:,}")
    console.print(sets)

    patterns = Table(title="Patterns", header_style="bold bright_cyan", box=None)
    patterns.add_column("Template")
    patterns.add_column("Combinations", justify="right", style="magenta")
    for item in estimate.patterns:
        patterns.add_row(item.pattern, f"{item.combinations:,}")
    console.print(patterns)


def _sources_command(args: argparse.Namespace) -> int:
    if args.sources_command == "scan":
        found = scan_seclists(persist=True)
        if not found:
            console.print("[warning]No SecLists installation found.[/warning]")
            console.print("Register one with: web-dict-composer sources add seclists PATH")
            return 1
        for source in found:
            console.print(f"[success]Found[/success] [source.seclists]{source.path}[/]")
        return 0
    if args.sources_command == "list":
        sources = load_sources()
        table = Table(header_style="bold bright_cyan", title="Dictionary sources")
        table.add_column("Name")
        table.add_column("Path")
        table.add_column("Status")
        for source in sources:
            available = source.resolved_path.is_dir()
            table.add_row(
                source.name,
                source.path,
                Text("available", style="success")
                if available
                else Text("missing", style="danger"),
            )
        console.print(table)
        if not sources:
            console.print("[muted]No sources registered. Run `sources scan` or `sources add`.[/]")
        return 0
    if args.sources_command == "add":
        source = add_source(args.name, args.path)
        console.print(f"[success]Registered[/success] {source.name} → {source.path}")
        return 0
    raise ComposerError("Choose a sources command. Run `web-dict-composer sources --help`.")


def _catalog_table(entries: list[CatalogEntry], *, search: bool = False) -> Table:
    if search and console.width < 100:
        table = Table(
            header_style="bold bright_cyan",
            title="Dictionary search results",
            show_lines=True,
        )
        table.add_column("ID", style="cyan", overflow="fold", ratio=2)
        table.add_column("Details", ratio=3, overflow="fold")
        for entry in entries:
            details = Text()
            details.append("Kind: ", style="muted")
            details.append(entry.kind)
            details.append("\nSource: ", style="muted")
            details.append(entry.source, style=_source_style(entry.source))
            details.append("\nPath: ", style="muted")
            details.append(entry.path.replace("/", "/\n"))
            details.append("\nTags: ", style="muted")
            details.append(", ".join(entry.tags))
            details.append("\nDescription: ", style="muted")
            details.append(entry.description)
            if not resolve_entry(entry) and entry.source != "local":
                details.append("\nSource not available locally.", style="warning")
            table.add_row(entry.id, details)
        return table

    table = Table(
        header_style="bold bright_cyan",
        title="Dictionary search results" if search else "Dictionary catalog",
        show_lines=search,
    )
    table.add_column("ID", style="cyan", overflow="fold")
    if not search:
        table.add_column("Domain", style="magenta", no_wrap=True)
    table.add_column("Kind", no_wrap=True)
    table.add_column("Source", no_wrap=True)
    table.add_column("Path", style="white", overflow="fold")
    if search:
        table.add_column("Tags", overflow="fold")
        table.add_column("Description")

    for entry in entries:
        row = [
            entry.id,
            *([] if search else [entry.domain]),
            entry.kind,
            Text(entry.source, style=_source_style(entry.source)),
            entry.path,
        ]
        if search:
            row.append(", ".join(entry.tags))
            description = Text(entry.description)
            if not resolve_entry(entry) and entry.source != "local":
                description.append("\nSource not available locally.", style="warning")
            row.append(description)
        table.add_row(*row)
    return table


def _dicts_command(args: argparse.Namespace) -> int:
    if args.dicts_command == "list":
        entries = list_entries(
            domain=args.domain,
            kind=args.kind,
            tag=args.tag,
            include_references=args.include_references,
        )
        console.print(_catalog_table(entries))
        if not entries:
            console.print("[warning]No catalog entries matched those filters.[/warning]")
            return 1
        return 0
    if args.dicts_command == "search":
        entries = search_catalog(
            " ".join(args.query),
            limit=args.limit,
            include_references=args.include_references,
        )
        if not entries:
            console.print("[warning]No dictionaries matched.[/warning]")
            return 1
        console.print(_catalog_table(entries, search=True))
        return 0
    if args.dicts_command == "show":
        entry = get_entry(args.dictionary_id)
        resolved = resolve_entry(entry)
        body = Table(show_header=False, box=None, padding=(0, 2))
        for label, value in (
            ("ID", entry.id),
            ("Name", entry.name),
            ("Domain", entry.domain),
            ("Kind", entry.kind),
            ("Source", entry.source),
            ("Path", entry.path),
            ("Resolved", resolved or "not available locally"),
            ("Tags", ", ".join(entry.tags)),
            ("Description", entry.description),
        ):
            body.add_row(Text(label, style="muted"), str(value))
        console.print(Panel(body, title="[brand]Dictionary[/brand]", border_style="cyan"))
        return 0
    if args.dicts_command == "path":
        entry = get_entry(args.dictionary_id)
        resolved = resolve_entry(entry)
        if not resolved:
            raise ComposerError(
                f"'{entry.id}' is cataloged as [{entry.source}] {entry.path}, but that source "
                "is not available locally. Run `sources scan` or `sources add`."
            )
        console.print(resolved, markup=False)
        return 0
    raise ComposerError("Choose a dicts command. Run `web-dict-composer dicts --help`.")


def _profile_rows(domain: str | None = None) -> list[Profile]:
    return [load_profile(path) for path in profile_files(domain)]


def _set_source(spec: dict[str, object]) -> str:
    if "catalog" in spec:
        return str(spec["catalog"])
    if "catalogs" in spec:
        return ", ".join(str(item) for item in spec["catalogs"])
    if "file" in spec:
        return str(spec["file"])
    return "inline"


SET_TAG_HINTS = {
    "base": {"filenames", "bases"},
    "dangerous": {"dangerous", "extensions", "handlers"},
    "allowed": {"allowlist", "extensions"},
    "sep": {"separators"},
    "separator": {"separators"},
    "traversal": {"steps"},
    "step": {"steps"},
    "target": {"targets"},
    "wrapper": {"wrappers"},
    "extension": {"limited-upload", "extensions"},
    "suffix": {"suffixes"},
}


def _replacement_candidates(profile: Profile, set_name: str) -> list[CatalogEntry]:
    spec = profile.sets_spec[set_name]
    current_ids: set[str] = set()
    if "catalog" in spec:
        current_ids.add(str(spec["catalog"]))
    elif "catalogs" in spec:
        current_ids.update(str(item) for item in spec["catalogs"])
    primary_hints = set(SET_TAG_HINTS.get(set_name.casefold(), set()))
    hints = set(primary_hints)
    for dictionary_id in current_ids:
        hints.update(tag.casefold() for tag in get_entry(dictionary_id).tags)
    hints -= {"atoms", "file-upload", "lfi"}
    match_hints = primary_hints or hints
    required_overlap = min(2, len(primary_hints)) or 2

    candidates = []
    for entry in list_entries(domain=profile.domain):
        overlap = match_hints.intersection(tag.casefold() for tag in entry.tags)
        if (
            entry.id not in current_ids
            and entry.kind in COMPOSABLE_KINDS
            and len(overlap) >= required_overlap
        ):
            candidates.append(entry)
    return candidates


def _replaceable_sets(profile: Profile) -> list[str]:
    return [
        name
        for name in profile.sets_spec
        if _replacement_candidates(profile, name)
    ]


def _profiles_command(args: argparse.Namespace) -> int:
    if args.profiles_command == "list":
        profiles = _profile_rows(args.domain)
        table = Table(header_style="bold bright_cyan", title="Composition profiles")
        table.add_column("Profile", style="cyan")
        table.add_column("Domain", style="magenta")
        table.add_column("Description")
        for profile in profiles:
            table.add_row(profile.id, profile.domain, profile.description)
        console.print(table)
        return 0 if profiles else 1
    if args.profiles_command == "show":
        profile = load_profile(args.profile)
        body = Table(show_header=False, box=None, padding=(0, 2))
        body.add_row("ID", profile.id)
        body.add_row("Domain", profile.domain)
        body.add_row("Description", profile.description)
        body.add_row("File", str(profile.path))
        for name, spec in profile.sets_spec.items():
            body.add_row(f"Set: {name}", _set_source(spec))
        console.print(Panel(body, title="[brand]Profile[/brand]", border_style="cyan"))
        _estimate_table(estimate_profile(profile))
        return 0
    if args.profiles_command == "estimate":
        estimate = estimate_profile(load_profile(args.profile))
        if args.json:
            console.print(json.dumps(estimate.to_dict(), indent=2), markup=False)
        else:
            _estimate_table(estimate)
        return 0
    if args.profiles_command == "build":
        return _build(load_profile(args.profile), args.output, args.force)
    raise ComposerError("Choose a profiles command. Run `web-dict-composer profiles --help`.")


def _build(profile: Profile, output: str | None, force: bool) -> int:
    estimate = estimate_profile(profile)
    _estimate_table(estimate)
    with console.status("[brand]Composing deterministic output…[/brand]"):
        artifacts = build_artifacts(profile, output_override=output, force=force)
    status = "[warning]TRUNCATED[/warning]" if artifacts.truncated else "[success]complete[/]"
    console.print(f"\nBuild {status}: [accent]{artifacts.lines:,} lines[/accent]")
    console.print(f"  [muted]Wordlist[/muted]  {artifacts.wordlist}")
    console.print(f"  [muted]Manifest[/muted]  {artifacts.manifest}")
    return 0


def _choose_catalog_set(profile: Profile) -> None:
    replaceable = _replaceable_sets(profile)
    while replaceable and Confirm.ask("Change one of the catalog sets?", default=False):
        for number, name in enumerate(replaceable, 1):
            source = _set_source(profile.sets_spec[name])
            console.print(f"  [accent]{number}[/accent]  {name}: {source}")
        selected = replaceable[
            IntPrompt.ask(
                "Set to replace",
                choices=[str(number) for number in range(1, len(replaceable) + 1)],
            )
            - 1
        ]
        compatible = _replacement_candidates(profile, selected)
        for number, entry in enumerate(compatible, 1):
            console.print(
                f"  [brand]{number}[/brand]  {entry.id} [muted]— {entry.description}[/muted]"
            )
        choice = IntPrompt.ask(
            "Replacement",
            choices=[str(number) for number in range(1, len(compatible) + 1)],
        )
        old_spec = profile.sets_spec[selected]
        new_spec: dict[str, object] = {"catalog": compatible[choice - 1].id}
        if "repeat" in old_spec:
            new_spec["repeat"] = old_spec["repeat"]
        profile.sets_spec[selected] = new_spec
        replaceable = _replaceable_sets(profile)


def _composable_entries(domain: str | None = None) -> list[CatalogEntry]:
    entries = list_entries(domain=domain)
    return [
        entry
        for entry in entries
        if entry.kind in COMPOSABLE_KINDS
        and not entry.path.startswith(("https://", "http://"))
        and resolve_entry(entry)
    ]


def _filter_composable_entries(
    entries: list[CatalogEntry], terms: list[str]
) -> list[CatalogEntry]:
    normalized = [term.casefold() for term in terms if term.strip()]
    if not normalized:
        return entries
    matches = []
    for entry in entries:
        searchable = " ".join(
            (
                entry.id,
                entry.name,
                entry.domain,
                entry.kind,
                entry.path,
                entry.description,
                *entry.tags,
            )
        ).casefold()
        if all(term in searchable for term in normalized):
            matches.append(entry)
    return matches


def _remaining_tags(entry: CatalogEntry, terms: list[str]) -> tuple[str, ...]:
    active = {term.casefold() for term in terms}
    return tuple(tag for tag in entry.tags if tag.casefold() not in active)


def _tag_counts(
    entries: list[CatalogEntry], terms: list[str] | None = None
) -> list[tuple[str, int]]:
    active = {term.casefold() for term in (terms or [])}
    counts: dict[str, int] = {}
    for entry in entries:
        for tag in entry.tags:
            if tag.casefold() not in active:
                counts[tag] = counts.get(tag, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def _print_tag_summary(entries: list[CatalogEntry], terms: list[str] | None = None) -> None:
    tags = _tag_counts(entries, terms)
    line = Text("Available tags: ", style="muted")
    for index, (tag, count) in enumerate(tags):
        if index:
            line.append(", ", style="muted")
        line.append(tag, style="accent")
        line.append(f" ({count})", style="muted")
    console.print(line)


def _wizard_dictionary_table(
    entries: list[CatalogEntry], terms: list[str], *, show_domain: bool
) -> Table:
    table = Table(
        title=f"Matching dictionaries ({len(entries)})",
        header_style="bold bright_cyan",
        show_lines=True,
    )
    table.add_column("#", justify="right", style="accent", no_wrap=True)
    table.add_column("ID", style="cyan", overflow="fold")
    if show_domain:
        table.add_column("Domain", style="magenta", no_wrap=True)
    table.add_column("Description", overflow="fold")
    table.add_column("Remaining tags", overflow="fold")
    for number, entry in enumerate(entries, 1):
        row = [str(number), entry.id]
        if show_domain:
            row.append(entry.domain)
        row.extend((entry.description, ", ".join(_remaining_tags(entry, terms)) or "—"))
        table.add_row(*row)
    return table


def _custom_dictionary_values() -> list[str]:
    console.print(
        "Enter one value per line. You can paste several lines; type "
        "[accent]:done[/accent] on its own line when finished."
    )
    values: list[str] = []
    while True:
        try:
            value = console.input("[accent]> [/accent]").strip()
        except EOFError as exc:
            raise ComposerError("Input ended before the custom dictionary was finished.") from exc
        if value.casefold() == ":done":
            if values:
                return list(dict.fromkeys(values))
            console.print("[warning]Add at least one value before finishing.[/warning]")
            continue
        if value:
            values.append(value)


def _select_wizard_dictionary(
    number: int, total: int, domain: str | None
) -> tuple[CatalogEntry | None, list[str] | None]:
    pool = _composable_entries(domain)
    if not pool:
        raise ComposerError("No locally available composable dictionaries were found.")

    filters: list[str] = []
    visible: list[CatalogEntry] = []
    console.print(f"\n[brand]Dictionary {number} of {total}[/brand]")
    if domain:
        console.print(f"[muted]Composition domain: {domain}[/muted]")
    _print_tag_summary(pool)
    console.print(
        "Type tags to narrow the results, a known ID/name to select it, or a command: "
        "[accent]:custom[/accent], [accent]:all[/accent], [accent]:reset[/accent], "
        "[accent]:tags[/accent]."
    )

    while True:
        raw = Prompt.ask("Tag, dictionary, or result number").strip()
        command = raw.casefold()
        if command == ":custom":
            return None, _custom_dictionary_values()
        if command == ":reset":
            filters.clear()
            visible = []
            _print_tag_summary(pool)
            continue
        if command == ":all":
            filters.clear()
            visible = pool
            console.print(
                _wizard_dictionary_table(visible, filters, show_domain=domain is None)
            )
            continue
        if command == ":tags":
            _print_tag_summary(visible or pool, filters)
            continue

        exact = [
            entry
            for entry in pool
            if command in {entry.id.casefold(), entry.name.casefold()}
        ]
        if len(exact) == 1:
            return exact[0], None

        if raw.isdigit() and visible:
            selected = int(raw)
            if 1 <= selected <= len(visible):
                return visible[selected - 1], None
            console.print("[warning]That result number is outside the displayed range.[/warning]")
            continue

        new_terms = re.findall(r"[a-z0-9]+(?:[-_][a-z0-9]+)*", command)
        if not new_terms:
            console.print("[warning]Enter a tag, name, ID, or command.[/warning]")
            continue
        proposed = filters + [term for term in new_terms if term not in filters]
        matches = _filter_composable_entries(pool, proposed)
        if not matches:
            console.print(
                "[warning]No dictionaries match those filters; the previous selection "
                "was kept.[/warning]"
            )
            continue
        filters = proposed
        visible = matches
        console.print(f"[muted]Active filters: {' + '.join(filters)}[/muted]")
        console.print(_wizard_dictionary_table(visible, filters, show_domain=domain is None))


def _suggest_alias(entry: CatalogEntry | None, number: int, used: set[str]) -> str:
    if entry:
        tags = {tag.casefold() for tag in entry.tags}
        suggestions = (
            ("bases", "base"),
            ("dangerous", "dangerous"),
            ("allowlist", "allowed"),
            ("separators", "sep"),
            ("steps", "traversal"),
            ("targets", "target"),
            ("wrappers", "wrapper"),
            ("suffixes", "suffix"),
        )
        for tag, alias in suggestions:
            if tag in tags and alias not in used:
                return alias
    return f"set{number}"


def _prompt_alias(entry: CatalogEntry | None, number: int, used: set[str]) -> str:
    default = _suggest_alias(entry, number, used)
    while True:
        alias = Prompt.ask(
            "Short placeholder name used in patterns",
            default=default,
        ).strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", alias):
            console.print(
                "[warning]Use letters, numbers, and underscores, starting with a letter "
                "or underscore.[/warning]"
            )
        elif alias in used:
            console.print("[warning]That placeholder name is already in use.[/warning]")
        else:
            return alias


def _pattern_options(aliases: list[str], include_subsets: bool = False) -> list[str]:
    if include_subsets and len(aliases) > 1:
        lengths = range(len(aliases), 1, -1)
    else:
        lengths = (len(aliases),)
    return [
        "".join(f"{{{alias}}}" for alias in ordering)
        for length in lengths
        for ordering in itertools.permutations(aliases, length)
    ]


def _parse_number_selection(value: str, maximum: int) -> list[int]:
    if value.strip().casefold() == "all":
        return list(range(maximum))
    selected: list[int] = []
    for item in value.split(","):
        token = item.strip()
        if not token:
            raise ValueError("Use numbers separated by commas, ranges such as 2-5, or 'all'.")
        if "-" in token:
            bounds = token.split("-", 1)
            if len(bounds) != 2 or not all(bound.strip().isdigit() for bound in bounds):
                raise ValueError(f"Invalid range: {token}")
            start, end = (int(bound.strip()) for bound in bounds)
            if start > end:
                raise ValueError(f"Range must be ascending: {token}")
            numbers = range(start, end + 1)
        elif token.isdigit():
            numbers = (int(token),)
        else:
            raise ValueError(f"Invalid selection: {token}")
        for number in numbers:
            if not 1 <= number <= maximum:
                raise ValueError(f"Pattern number {number} is outside 1-{maximum}.")
            index = number - 1
            if index not in selected:
                selected.append(index)
    if not selected:
        raise ValueError("Select at least one pattern.")
    return selected


def _select_patterns(aliases: list[str]) -> list[str]:
    include_subsets = len(aliases) > 1 and Confirm.ask(
        "Also offer shorter patterns that still combine at least two dictionaries?",
        default=False,
    )
    patterns = _pattern_options(aliases, include_subsets)
    table = Table(title="Available composition patterns", header_style="bold bright_cyan")
    table.add_column("#", justify="right", style="accent")
    table.add_column("Pattern", style="cyan")
    table.add_column("Uses", justify="right", style="muted")
    for number, pattern in enumerate(patterns, 1):
        table.add_row(str(number), pattern, str(pattern.count("{")))
    console.print(table)
    console.print(
        "[muted]Choose comma-separated numbers, ranges such as 1-3, or all.[/muted]"
    )
    while True:
        raw = Prompt.ask("Patterns to generate", default="all")
        try:
            return [patterns[index] for index in _parse_number_selection(raw, len(patterns))]
        except ValueError as exc:
            console.print(f"[warning]{exc}[/warning]")


def _wizard() -> int:
    if not console.is_terminal:
        raise ComposerError(
            "The wizard needs an interactive terminal. Use `profiles build` in scripts."
        )
    _banner()
    console.print(
        "[muted]Build a custom composition from catalog dictionaries or pasted values. "
        "Up to four inputs keeps every ordering easy to review.[/muted]\n"
    )
    count = IntPrompt.ask(
        "How many dictionaries do you want to combine?",
        choices=["1", "2", "3", "4"],
        default=3,
    )

    domain: str | None = None
    used_aliases: set[str] = set()
    sets_spec: dict[str, dict[str, object]] = {}
    selected_rows: list[tuple[str, str, str]] = []
    for number in range(1, count + 1):
        entry, custom_values = _select_wizard_dictionary(number, count, domain)
        if entry and domain is None:
            domain = entry.domain
            console.print(f"[success]Composition domain set to {domain}.[/success]")
        alias = _prompt_alias(entry, number, used_aliases)
        used_aliases.add(alias)
        if entry:
            sets_spec[alias] = {"catalog": entry.id}
            selected_rows.append((alias, entry.id, entry.description))
        else:
            values = custom_values or []
            sets_spec[alias] = {"inline": values}
            selected_rows.append((alias, "custom", f"{len(values)} inline values"))

    if domain is None:
        domains = list(ACTIVE_DOMAINS)
        for number, candidate in enumerate(domains, 1):
            console.print(f"  [brand]{number}[/brand]  {candidate}")
        domain = domains[
            IntPrompt.ask(
                "Choose a domain for this custom composition",
                choices=[str(number) for number in range(1, len(domains) + 1)],
            )
            - 1
        ]

    selected_table = Table(title="Selected dictionaries", header_style="bold bright_cyan")
    selected_table.add_column("Placeholder", style="accent")
    selected_table.add_column("Dictionary", style="cyan")
    selected_table.add_column("Description")
    for row in selected_rows:
        selected_table.add_row(*row)
    console.print(selected_table)

    aliases = list(sets_spec)
    patterns = _select_patterns(aliases)
    while True:
        max_outputs = IntPrompt.ask("Maximum output lines", default=50_000)
        if max_outputs > 0:
            break
        console.print("[warning]The maximum must be a positive number.[/warning]")
    profile_id = "wizard_" + "_".join(alias.casefold() for alias in aliases)
    profile = Profile(
        path=Path("<interactive-wizard>"),
        id=profile_id,
        domain=domain,
        description="Interactive composition created by the wizard.",
        sets_spec=sets_spec,
        patterns=patterns,
        filters={"dedupe": True, "max_length": 240, "max_outputs": max_outputs},
        output={"file": f"output/{profile_id}.txt"},
    )

    estimate = estimate_profile(profile)
    _estimate_table(estimate)
    if not Confirm.ask("Generate the wordlist and manifest?", default=True):
        console.print("[muted]Nothing was written.[/muted]")
        return 0
    output = Prompt.ask("Output file", default=str(profile.output["file"]))
    force = False
    if estimate.expanded_upper_bound > estimate.max_outputs:
        force = Confirm.ask(
            "The estimate exceeds the hard cap. Generate a capped, marked result?",
            default=False,
        )
        if not force:
            console.print("[muted]Nothing was written.[/muted]")
            return 0
    return _build(profile, output, force)


def _guided() -> int:
    if not console.is_terminal:
        raise ComposerError(
            "Guided selection needs an interactive terminal. Use `profiles list` and "
            "`profiles build`."
        )
    _banner()
    console.print(
        "[muted]Guided selection writes only a wordlist and compact manifest.[/muted]\n"
    )
    domains = list(ACTIVE_DOMAINS)
    for number, domain in enumerate(domains, 1):
        console.print(f"  [brand]{number}[/brand]  {domain.replace('_', ' ').title()}")
    domain = domains[IntPrompt.ask("Choose a domain", choices=["1", "2"]) - 1]

    profiles = _profile_rows(domain)
    console.print()
    for number, profile in enumerate(profiles, 1):
        console.print(
            f"  [accent]{number}[/accent]  {profile.id} "
            f"[muted]— {profile.description}[/muted]"
        )
    choice = IntPrompt.ask(
        "Choose a profile",
        choices=[str(number) for number in range(1, len(profiles) + 1)],
    )
    profile = profiles[choice - 1]

    console.print("\n[brand]Profile sets[/brand]")
    for name, spec in profile.sets_spec.items():
        console.print(f"  [success]•[/success] {name}: [muted]{_set_source(spec)}[/muted]")
    _choose_catalog_set(profile)

    estimate = estimate_profile(profile)
    _estimate_table(estimate)
    if not Confirm.ask("Generate the wordlist and manifest?", default=True):
        console.print("[muted]Nothing was written.[/muted]")
        return 0
    default_output = str(profile.output.get("file", f"output/{profile.id}.txt"))
    output = Prompt.ask("Output file", default=default_output)
    force = False
    if estimate.expanded_upper_bound > estimate.max_outputs:
        force = Confirm.ask(
            "The estimate exceeds the hard cap. Generate a capped, marked result?",
            default=False,
        )
        if not force:
            console.print("[muted]Nothing was written.[/muted]")
            return 0
    return _build(profile, output, force)


def run(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if not args.command:
        _banner()
        parser.print_help()
        return 0
    try:
        if args.command == "sources":
            return _sources_command(args)
        if args.command == "dicts":
            return _dicts_command(args)
        if args.command == "profiles":
            return _profiles_command(args)
        if args.command == "wizard":
            return _wizard()
        if args.command == "guided":
            return _guided()
        raise ComposerError(f"Unknown command: {args.command}")
    except ComposerError as exc:
        error_console.print(f"[danger]Error:[/danger] {exc}")
        return 2
    except KeyboardInterrupt:
        error_console.print("\n[warning]Cancelled.[/warning]")
        return 130


def main() -> None:
    raise SystemExit(run())
