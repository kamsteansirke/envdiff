"""CLI sub-command: envdiff dedup — find duplicate keys in .env files."""
from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from envdiff.deduplicator import find_duplicates


def add_dedup_subparser(subparsers) -> None:  # type: ignore[type-arg]
    p: ArgumentParser = subparsers.add_parser(
        "dedup",
        help="detect duplicate keys within one or more .env files",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help=".env file(s) to check",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="exit with code 1 if any duplicates are found",
    )
    p.set_defaults(func=_run_dedup)


def _run_dedup(args: Namespace) -> int:
    found_any = False
    for raw in args.files:
        path = Path(raw)
        if not path.exists():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 2
        result = find_duplicates(path)
        print(result.summary())
        if result.has_duplicates:
            found_any = True

    if args.strict and found_any:
        return 1
    return 0
