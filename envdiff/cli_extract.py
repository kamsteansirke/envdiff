"""CLI sub-command: extract — pull a subset of keys from an env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.extractor import extract_env


def add_extract_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "extract",
        help="Extract a subset of keys from an env file",
    )
    p.add_argument("file", type=Path, help="Source .env file")
    p.add_argument(
        "-k", "--key",
        dest="keys",
        metavar="KEY",
        action="append",
        default=[],
        help="Explicit key to extract (repeatable)",
    )
    p.add_argument(
        "-p", "--pattern",
        dest="patterns",
        metavar="REGEX",
        action="append",
        default=[],
        help="Regex pattern for keys to extract (repeatable)",
    )
    p.add_argument(
        "--invert",
        action="store_true",
        default=False,
        help="Invert selection (exclude matched keys instead)",
    )
    p.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Write result to file instead of stdout",
    )
    p.set_defaults(func=_run_extract)


def _run_extract(args: argparse.Namespace) -> int:
    result = extract_env(
        args.file,
        keys=args.keys or None,
        patterns=args.patterns or None,
        invert=args.invert,
    )

    rendered = result.render()
    if args.output:
        args.output.write_text(rendered)
        print(result.summary())
    else:
        sys.stdout.write(rendered)

    return 0
