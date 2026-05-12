"""CLI sub-command: envdiff diff-summary  — pretty-print a SnapshotDiff."""
from __future__ import annotations

import argparse
import sys

from envdiff.snapshotter import EnvSnapshot
from envdiff.differ import SnapshotDiff
from envdiff.differ_summary import summarise_diff


def add_differ_summary_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "diff-summary",
        help="Compare two snapshot files and print a human-readable summary.",
    )
    p.add_argument("before", help="Path to the 'before' snapshot JSON file.")
    p.add_argument("after", help="Path to the 'after' snapshot JSON file.")
    p.add_argument(
        "--show-values",
        action="store_true",
        default=False,
        help="Include old/new values in the output.",
    )
    p.set_defaults(func=_run_differ_summary)


def _run_differ_summary(args: argparse.Namespace) -> int:
    try:
        before = EnvSnapshot.load(args.before)
        after = EnvSnapshot.load(args.after)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    diff = SnapshotDiff(before=before, after=after)
    report = summarise_diff(diff, show_values=args.show_values)
    print(report.render(show_values=args.show_values))
    return 1 if not report.is_empty else 0
