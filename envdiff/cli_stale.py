"""CLI sub-command: envdiff stale — report stale / placeholder values."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file
from envdiff.staler import check_staleness


def add_stale_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "stale",
        help="Detect stale or placeholder values in a .env file.",
    )
    p.add_argument("file", help="Path to the .env file to inspect.")
    p.add_argument(
        "--exit-zero",
        action="store_true",
        default=False,
        help="Always exit 0 even when stale values are found.",
    )
    p.set_defaults(func=_run_stale)


def _run_stale(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    result = check_staleness(env)

    print(result.summary())

    if result.is_clean or args.exit_zero:
        return 0
    return 1
