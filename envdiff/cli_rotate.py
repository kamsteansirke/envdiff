"""CLI subcommand: envdiff rotate — detect rotated/changed keys between two env files."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file
from envdiff.rotator import rotate_env


def add_rotate_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "rotate",
        help="Detect rotated or changed keys between two env files.",
    )
    p.add_argument("before", help="Path to the older/baseline .env file.")
    p.add_argument("after", help="Path to the newer .env file.")
    p.add_argument(
        "--sensitive-only",
        action="store_true",
        default=False,
        help="Only report changes to sensitive-looking keys.",
    )
    p.add_argument(
        "--show-values",
        action="store_true",
        default=False,
        help="Show old and new values in output.",
    )
    p.set_defaults(func=_run_rotate)


def _run_rotate(args: argparse.Namespace) -> int:
    before_path = Path(args.before)
    after_path = Path(args.after)

    if not before_path.exists():
        print(f"error: file not found: {before_path}", file=sys.stderr)
        return 2
    if not after_path.exists():
        print(f"error: file not found: {after_path}", file=sys.stderr)
        return 2

    before_env = parse_env_file(before_path)
    after_env = parse_env_file(after_path)

    result = rotate_env(before_env, after_env, sensitive_only=args.sensitive_only)

    print(f"Rotation summary: {result.summary()}")

    if result.candidates:
        print("\nRotated keys:")
        for c in result.candidates:
            if args.show_values:
                print(f"  {c.key}  [{c.reason}]  '{c.old_value}' -> '{c.new_value}'")
            else:
                print(f"  {c.key}  [{c.reason}]")

    if result.added_keys:
        print("\nAdded keys:")
        for k in result.added_keys:
            print(f"  + {k}")

    if result.removed_keys:
        print("\nRemoved keys:")
        for k in result.removed_keys:
            print(f"  - {k}")

    return 1 if result.total_changes > 0 else 0
