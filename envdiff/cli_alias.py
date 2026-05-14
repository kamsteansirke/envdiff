"""cli_alias.py – CLI sub-command: envdiff alias

Prints keys that share identical values (potential legacy aliases).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.aliaser import find_aliases
from envdiff.parser import parse_env_file


def add_alias_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "alias",
        help="Detect keys that share the same value (possible aliases).",
    )
    p.add_argument("file", help="Path to the .env file to inspect.")
    p.add_argument(
        "--include-empty",
        action="store_true",
        default=False,
        help="Include keys whose value is an empty string.",
    )
    p.add_argument(
        "--min-group",
        type=int,
        default=2,
        metavar="N",
        help="Minimum number of keys to form an alias group (default: 2).",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output.",
    )
    p.set_defaults(func=_run_alias)


def _color(text: str, code: str, *, enabled: bool) -> str:
    if not enabled:
        return text
    return f"\033[{code}m{text}\033[0m"


def _run_alias(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    result = find_aliases(
        env,
        ignore_empty=not args.include_empty,
        min_group_size=args.min_group,
    )

    color = not args.no_color
    print(result.summary())

    if result.has_aliases:
        for group in result.groups:
            keys_fmt = ", ".join(group.keys)
            label = _color("ALIAS", "33", enabled=color)
            print(f"  {label}  {keys_fmt}")
        return 1

    return 0
