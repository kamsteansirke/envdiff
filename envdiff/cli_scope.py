"""CLI sub-command: ``envdiff scope`` — show deployment-scope analysis."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file
from envdiff.scoper import scope_env


def add_scope_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "scope",
        help="Classify keys by deployment-environment scope prefix.",
    )
    p.add_argument("file", help="Path to the .env file to analyse.")
    p.add_argument(
        "--by-scope",
        action="store_true",
        default=False,
        help="Group output by scope instead of listing all keys.",
    )
    p.add_argument(
        "--scoped-only",
        action="store_true",
        default=False,
        help="Only show keys that have a recognised scope prefix.",
    )
    p.set_defaults(func=_run_scope)


def _run_scope(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    result = scope_env(env)

    print(result.summary())
    print()

    if args.by_scope:
        for scope, keys in result.by_scope().items():
            print(f"[{scope}]")
            for k in keys:
                print(f"  {k}")
    else:
        entries = result.entries
        if args.scoped_only:
            entries = [e for e in entries if e.scope is not None]
        for entry in sorted(entries, key=lambda e: e.key):
            print(str(entry))

    return 1 if result.scoped_keys() else 0
