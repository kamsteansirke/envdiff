"""CLI sub-command: envdiff sanitize — detect unsafe values in a .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file
from envdiff.sanitizer import sanitize_env


def add_sanitize_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "sanitize",
        help="Detect (and optionally report fixes for) unsafe values in a .env file.",
    )
    p.add_argument("file", help="Path to the .env file to sanitize.")
    p.add_argument(
        "--no-trailing-ws",
        dest="fix_trailing_ws",
        action="store_false",
        default=True,
        help="Disable trailing-whitespace checks.",
    )
    p.add_argument(
        "--no-control-chars",
        dest="fix_control",
        action="store_false",
        default=True,
        help="Disable control-character checks.",
    )
    p.add_argument(
        "--no-null-bytes",
        dest="strip_null",
        action="store_false",
        default=True,
        help="Disable null-byte checks.",
    )
    p.set_defaults(func=_run_sanitize)


def _run_sanitize(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    result = sanitize_env(
        env,
        fix_trailing_whitespace=args.fix_trailing_ws,
        fix_control_chars=args.fix_control,
        strip_null_bytes=args.strip_null,
    )

    print(result.summary())

    if not result.is_clean:
        print()
        print("Suggested fixes:")
        for key, clean_value in result.sanitized.items():
            if clean_value != env[key]:
                print(f"  {key}={clean_value!r}")
        return 1

    return 0
