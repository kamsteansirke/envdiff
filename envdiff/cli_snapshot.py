"""CLI subcommands: snapshot capture / diff."""
from __future__ import annotations

import sys
from pathlib import Path

from envdiff.snapshotter import (
    capture_snapshot,
    diff_snapshots,
    load_snapshot,
    save_snapshot,
)


def add_snapshot_subparser(subparsers) -> None:  # noqa: ANN001
    p = subparsers.add_parser("snapshot", help="Capture or diff .env snapshots")
    sub = p.add_subparsers(dest="snapshot_cmd", required=True)

    cap = sub.add_parser("capture", help="Capture a snapshot of an env file")
    cap.add_argument("env_file", help="Path to .env file")
    cap.add_argument("output", help="Path to write snapshot JSON")
    cap.add_argument("--ignore-values", action="store_true", default=False)

    dif = sub.add_parser("diff", help="Diff two snapshots")
    dif.add_argument("old", help="Path to old snapshot JSON")
    dif.add_argument("new", help="Path to new snapshot JSON")

    p.set_defaults(func=_run_snapshot)


def _run_snapshot(args) -> int:  # noqa: ANN001
    if args.snapshot_cmd == "capture":
        return _run_capture(args)
    if args.snapshot_cmd == "diff":
        return _run_diff(args)
    return 1


def _run_capture(args) -> int:  # noqa: ANN001
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"error: file not found: {env_path}", file=sys.stderr)
        return 1
    snap = capture_snapshot(env_path, ignore_values=args.ignore_values)
    save_snapshot(snap, Path(args.output))
    print(f"Snapshot saved to {args.output} ({len(snap.entries)} keys)")
    return 0


def _run_diff(args) -> int:  # noqa: ANN001
    try:
        old = load_snapshot(Path(args.old))
        new = load_snapshot(Path(args.new))
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    changes = diff_snapshots(old, new)
    if not changes:
        print("No changes between snapshots.")
        return 0

    labels = {"added": "+", "removed": "-", "changed": "~"}
    for key, change in sorted(changes.items()):
        print(f"  {labels.get(change, '?')} {key}  [{change}]")
    return 1
