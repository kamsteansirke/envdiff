"""cli_trim.py – CLI sub-command: envdiff trim"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.trimmer import trim_env, apply_trim


def add_trim_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "trim",
        help="Detect and optionally fix leading/trailing whitespace in .env values",
    )
    p.add_argument("files", nargs="+", metavar="FILE", help=".env file(s) to inspect")
    p.add_argument(
        "--fix",
        action="store_true",
        default=False,
        help="Rewrite files in-place, removing surrounding whitespace from values",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress output; use exit code only",
    )
    p.set_defaults(func=_run_trim)


def _run_trim(args: argparse.Namespace) -> int:
    any_issues = False

    for file_arg in args.files:
        path = Path(file_arg)
        if not path.exists():
            print(f"error: {path} does not exist", file=sys.stderr)
            return 2

        result = trim_env(path)

        if not result.is_clean:
            any_issues = True

        if not args.quiet:
            print(result.summary())

        if args.fix and not result.is_clean:
            changed = apply_trim(path, result)
            if not args.quiet:
                print(f"  fixed {len(changed)} line(s) in {path}")

    if any_issues and not args.fix:
        return 1
    return 0
