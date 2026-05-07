"""CLI subcommand: envdiff patch — apply key updates to a .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.patcher import patch_env


def add_patch_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "patch",
        help="Apply key=value updates to a .env file.",
    )
    p.add_argument("env_file", type=Path, help="Target .env file to patch.")
    p.add_argument(
        "assignments",
        nargs="*",
        metavar="KEY=VALUE",
        help="Key=value pairs to set.",
    )
    p.add_argument(
        "--remove",
        nargs="*",
        metavar="KEY",
        default=[],
        help="Keys to remove from the file.",
    )
    p.add_argument(
        "--no-add",
        action="store_true",
        help="Do not append keys that are missing from the file.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing.",
    )
    p.set_defaults(func=_run_patch)


def _run_patch(args: argparse.Namespace) -> int:
    updates: dict[str, str] = {}
    for assignment in args.assignments:
        if "=" not in assignment:
            print(f"ERROR: invalid assignment '{assignment}' (expected KEY=VALUE)", file=sys.stderr)
            return 2
        key, _, value = assignment.partition("=")
        updates[key.strip()] = value

    if not updates and not args.remove:
        print("Nothing to do.", file=sys.stderr)
        return 0

    result = patch_env(
        args.env_file,
        updates,
        remove_keys=args.remove,
        add_missing=not args.no_add,
        dry_run=args.dry_run,
    )

    prefix = "[dry-run] " if args.dry_run else ""
    print(f"{prefix}{result.summary()}")
    return 0
