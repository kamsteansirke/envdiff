"""CLI sub-command: envdiff snapshot-diff  — compare two env file snapshots."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envdiff.differ import diff_snapshots
from envdiff.parser import parse_env_file


def add_diff_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *snapshot-diff* sub-command."""
    p = subparsers.add_parser(
        "snapshot-diff",
        help="Show line-level diff between two .env files (before vs after).",
    )
    p.add_argument("before", help="Path to the 'before' .env file.")
    p.add_argument("after", help="Path to the 'after' .env file.")
    p.add_argument(
        "--show-values",
        action="store_true",
        default=False,
        help="Include actual values in output (hidden by default).",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour codes.",
    )
    p.set_defaults(func=_run_diff)


def _run_diff(args: argparse.Namespace) -> int:
    """Execute the snapshot-diff command; returns an exit code."""
    try:
        before = parse_env_file(args.before)
        after = parse_env_file(args.after)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = diff_snapshots(before, after)

    if result.is_empty:
        print("No differences found.")
        return 0

    use_color = not args.no_color and sys.stdout.isatty()

    def _color(text: str, code: str) -> str:
        return f"\033[{code}m{text}\033[0m" if use_color else text

    for diff in result.all_changes:
        if args.show_values:
            line = str(diff)
        else:
            # Mask values
            if diff.status == "added":
                line = f"+ {diff.key}"
            elif diff.status == "removed":
                line = f"- {diff.key}"
            else:
                line = f"~ {diff.key} (value changed)"

        if diff.status == "added":
            print(_color(line, "32"))
        elif diff.status == "removed":
            print(_color(line, "31"))
        else:
            print(_color(line, "33"))

    return 1
