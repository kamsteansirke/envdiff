"""CLI sub-command: envdiff template — generate a .env.example file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.templater import build_template


def add_template_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "template",
        help="Generate a .env.example template from one or more .env files.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help=".env files to read keys from.",
    )
    p.add_argument(
        "--output",
        "-o",
        metavar="PATH",
        default=None,
        help="Write template to this file (default: print to stdout).",
    )
    p.add_argument(
        "--placeholder",
        default="",
        metavar="VALUE",
        help="Value to use for every key (default: empty string).",
    )
    p.add_argument(
        "--no-sort",
        dest="sort_keys",
        action="store_false",
        default=True,
        help="Preserve key order instead of sorting alphabetically.",
    )
    p.set_defaults(func=_run_template)


def _run_template(args: argparse.Namespace) -> int:
    paths = [Path(f) for f in args.files]

    missing = [p for p in paths if not p.exists()]
    if missing:
        for m in missing:
            print(f"error: file not found: {m}", file=sys.stderr)
        return 1

    result = build_template(
        paths,
        placeholder=args.placeholder,
        sort_keys=args.sort_keys,
    )

    if args.output:
        out = Path(args.output)
        result.write(out)
        print(f"Template written to {out} ({len(result.keys)} keys).")
    else:
        print(result.render())

    return 0
