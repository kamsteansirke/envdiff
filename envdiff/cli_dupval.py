"""CLI sub-command: envdiff dupval — find keys that share the same value."""
from __future__ import annotations

import argparse
import sys
from typing import List

from envdiff.duplicator import find_duplicate_values


def add_dupval_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "dupval",
        help="Detect keys that share the same value within a .env file.",
    )
    p.add_argument("files", nargs="+", metavar="FILE", help=".env file(s) to scan")
    p.add_argument(
        "--include-empty",
        action="store_true",
        default=False,
        help="Also flag keys that share an empty value (default: skip empty)",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress output; use exit code only",
    )
    p.set_defaults(func=_run_dupval)


def _run_dupval(args: argparse.Namespace) -> int:
    files: List[str] = args.files
    ignore_empty: bool = not args.include_empty
    quiet: bool = args.quiet

    found_any = False
    for path in files:
        result = find_duplicate_values(path, ignore_empty=ignore_empty)
        if not quiet:
            print(result.summary())
        if result.has_duplicates:
            found_any = True

    return 1 if found_any else 0


def main(argv: List[str] | None = None) -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="envdiff")
    sub = parser.add_subparsers(dest="command")
    add_dupval_subparser(sub)
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    sys.exit(args.func(args))
