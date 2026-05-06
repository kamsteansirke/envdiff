"""CLI subcommand: envdiff group — show key groupings for one or more env files."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.grouper import group_env
from envdiff.parser import parse_env_file


def add_group_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "group",
        help="Group env keys by prefix and display the result.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="One or more .env files to analyse.",
    )
    p.add_argument(
        "--separator",
        default="_",
        metavar="SEP",
        help="Key separator character (default: '_').",
    )
    p.add_argument(
        "--min-group-size",
        type=int,
        default=2,
        metavar="N",
        help="Minimum keys to form a named group (default: 2).",
    )
    p.set_defaults(func=_run_group)


def _run_group(args: argparse.Namespace) -> int:
    exit_code = 0

    for raw_path in args.files:
        path = Path(raw_path)
        if not path.exists():
            print(f"error: file not found: {path}", file=sys.stderr)
            exit_code = 1
            continue

        try:
            env = parse_env_file(path)
        except Exception as exc:  # noqa: BLE001
            print(f"error: could not parse {path}: {exc}", file=sys.stderr)
            exit_code = 1
            continue

        result = group_env(
            env,
            separator=args.separator,
            min_group_size=args.min_group_size,
        )

        print(f"=== {path} ===")
        print(result.summary())
        print()

    return exit_code
