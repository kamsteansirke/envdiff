"""CLI sub-command: envdiff overlap — show key-overlap across env files."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from envdiff.comparator_overlap import analyze_overlap


def add_overlap_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "overlap",
        help="Analyse key overlap across multiple .env files.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Two or more .env files to compare.",
    )
    p.add_argument(
        "--unique",
        action="store_true",
        default=False,
        help="List keys that appear in only one file.",
    )
    p.add_argument(
        "--universal",
        action="store_true",
        default=False,
        help="List keys that appear in every file.",
    )
    p.add_argument(
        "--no-color",
        dest="no_color",
        action="store_true",
        default=False,
    )
    p.set_defaults(func=_run_overlap)


def _color(text: str, code: str, disabled: bool) -> str:
    if disabled:
        return text
    return f"\033[{code}m{text}\033[0m"


def _run_overlap(args: argparse.Namespace) -> int:
    paths: List[Path] = [Path(f) for f in args.files]

    for p in paths:
        if not p.exists():
            print(f"error: file not found: {p}", file=sys.stderr)
            return 2

    result = analyze_overlap(*paths)
    nc = getattr(args, "no_color", False)

    print(result.summary())
    print()

    show_unique = getattr(args, "unique", False)
    show_universal = getattr(args, "universal", False)

    if show_universal:
        keys = result.universal_keys()
        header = _color("Universal keys:", "1;32", nc)
        print(header)
        for k in keys:
            print(f"  {k}")
        print()

    if show_unique:
        keys = result.unique_keys()
        header = _color("Unique-to-one keys:", "1;33", nc)
        print(header)
        for k in keys:
            entry = result.entry_for(k)
            source = next(iter(entry.present_in)) if entry else "?"
            print(f"  {k}  ({source})")
        print()

    if not show_unique and not show_universal:
        for k in result.all_keys():
            entry = result.entry_for(k)
            coverage = entry.coverage(len(result.env_names)) if entry else 0.0
            bar = f"{coverage * 100:.0f}%"
            print(f"  {k:<40} {bar}")

    return 1 if not result.is_fully_overlapping() else 0
