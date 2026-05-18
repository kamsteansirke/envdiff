"""CLI subcommand: envdiff timeline — show how an env file changed over snapshots."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.snapshotter import EnvSnapshot
from envdiff.comparator_timeline import build_timeline


def add_timeline_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "timeline",
        help="Show key changes across an ordered list of snapshot files.",
    )
    p.add_argument(
        "snapshots",
        nargs="+",
        metavar="SNAPSHOT",
        help="Two or more snapshot JSON files in chronological order.",
    )
    p.add_argument(
        "--labels",
        nargs="+",
        metavar="LABEL",
        default=None,
        help="Optional labels for each snapshot (must match count).",
    )
    p.add_argument(
        "--show-values",
        action="store_true",
        default=False,
        help="Display before/after values for changed keys.",
    )
    p.set_defaults(func=_run_timeline)


def _run_timeline(args: argparse.Namespace) -> int:
    paths = [Path(p) for p in args.snapshots]

    if len(paths) < 2:
        print("error: at least two snapshots are required.", file=sys.stderr)
        return 2

    labels = args.labels
    if labels is not None and len(labels) != len(paths):
        print(
            f"error: --labels count ({len(labels)}) must match snapshot count ({len(paths)}).",
            file=sys.stderr,
        )
        return 2

    snaps: list[EnvSnapshot] = []
    for path in paths:
        try:
            snaps.append(EnvSnapshot.load(path))
        except Exception as exc:  # noqa: BLE001
            print(f"error loading {path}: {exc}", file=sys.stderr)
            return 2

    result = build_timeline(snaps, labels=labels)

    if result.is_empty():
        print("No changes detected across timeline.")
        return 0

    print(result.summary())

    if args.show_values:
        print()
        for event in result.events:
            if event.kind == "changed":
                print(f"  {event.key}: {event.before!r} -> {event.after!r}")
            elif event.kind == "added":
                print(f"  {event.key}: (new) {event.after!r}")
            else:
                print(f"  {event.key}: {event.before!r} -> (removed)")

    return 1
