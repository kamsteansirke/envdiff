"""CLI sub-command: normalize — apply normalization rules to a .env file."""
from __future__ import annotations

import argparse
import sys

from envdiff.normalizer import CasePolicy, NormalizeOptions, normalize_env, render_normalized


def add_normalize_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "normalize",
        help="Normalize a .env file (sort keys, enforce casing, strip empty values).",
    )
    p.add_argument("file", help="Path to the .env file to normalize.")
    p.add_argument(
        "--case",
        choices=[c.value for c in CasePolicy],
        default=CasePolicy.PRESERVE.value,
        help="Key casing policy (default: preserve).",
    )
    p.add_argument(
        "--no-sort",
        action="store_true",
        default=False,
        help="Disable alphabetical key sorting.",
    )
    p.add_argument(
        "--strip-empty",
        action="store_true",
        default=False,
        help="Remove keys with empty values.",
    )
    p.add_argument(
        "--write",
        action="store_true",
        default=False,
        help="Write normalized output back to the file in-place.",
    )
    p.add_argument(
        "--check",
        action="store_true",
        default=False,
        help="Exit with code 1 if the file is not already normalized.",
    )
    p.set_defaults(func=_run_normalize)


def _run_normalize(args: argparse.Namespace) -> int:
    options = NormalizeOptions(
        sort_keys=not args.no_sort,
        case_policy=CasePolicy(args.case),
        strip_empty_values=args.strip_empty,
    )

    result = normalize_env(args.file, options)
    rendered = render_normalized(result)

    if args.check:
        if not result.is_clean:
            print(result.summary())
            return 1
        print("File is already normalized.")
        return 0

    if args.write:
        with open(args.file, "w", encoding="utf-8") as fh:
            fh.write(rendered)
        print(f"Wrote normalized output to {args.file}")
        if not result.is_clean:
            print(result.summary())
    else:
        sys.stdout.write(rendered)

    return 0
