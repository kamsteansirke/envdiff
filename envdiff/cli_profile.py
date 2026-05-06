"""CLI sub-command: envdiff profile — display a profile of one or more .env files."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from envdiff.profiler import profile_env
from envdiff.parser import EnvParseError


def add_profile_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "profile",
        help="Display a statistical profile of one or more .env files.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help=".env file(s) to profile.",
    )
    p.add_argument(
        "--show-keys",
        action="store_true",
        default=False,
        help="List the individual keys in each category.",
    )
    p.set_defaults(func=_run_profile)


def _run_profile(args: argparse.Namespace) -> int:
    exit_code = 0
    for raw in args.files:
        path = Path(raw)
        try:
            result = profile_env(path)
        except (EnvParseError, OSError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue

        print(result.summary())

        if args.show_keys:
            categories = [
                ("Empty values", result.empty_values),
                ("Secret keys", result.secret_keys),
                ("URL values", result.url_values),
                ("Int values", result.int_values),
                ("Bool values", result.bool_values),
                ("Other values", result.other_values),
            ]
            for label, keys in categories:
                if keys:
                    print(f"  [{label}]")
                    for k in keys:
                        print(f"    - {k}")

        print()

    return exit_code
