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


def _process_file(path: Path) -> tuple[bool, int]:
    """Process a single file for duplicates.

    Returns a tuple of (has_duplicates, exit_code) where exit_code is non-zero
    on error (e.g. file not found or unreadable).
    """
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return False, 2
    try:
        result = find_duplicates(path)
    except OSError as exc:
        print(f"error: could not read {path}: {exc}", file=sys.stderr)
        return False, 2
    print(result.summary())
    return result.has_duplicates, 0


def _run_dedup(args: Namespace) -> int:
    """Entry point for the 'dedup' sub-command."""
    found_any = False
    for raw in args.files:
        has_duplicates, error_code = _process_file(Path(raw))
        if error_code:
            return error_code
        if has_duplicates:
            found_any = True

    if args.strict and found_any:
        return 1
    return 0
