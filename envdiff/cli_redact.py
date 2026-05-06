"""CLI subcommand: envdiff redact — print a redacted view of an .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file
from envdiff.redactor import RedactOptions, redact_env


def add_redact_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "redact",
        help="Print a redacted version of an .env file, masking sensitive values.",
    )
    p.add_argument("file", help="Path to the .env file to redact.")
    p.add_argument(
        "--placeholder",
        default="***REDACTED***",
        help="Replacement string for sensitive values (default: %(default)s).",
    )
    p.add_argument(
        "--extra-pattern",
        dest="extra_patterns",
        metavar="PATTERN",
        action="append",
        default=[],
        help="Additional regex pattern to treat as sensitive (repeatable).",
    )
    p.add_argument(
        "--no-defaults",
        action="store_true",
        help="Disable the built-in sensitive-key patterns.",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        help="Print a summary line after the redacted output.",
    )
    p.set_defaults(func=_run_redact)


def _run_redact(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    try:
        env = parse_env_file(path)
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not parse {path}: {exc}", file=sys.stderr)
        return 1

    from envdiff.redactor import _DEFAULT_PATTERNS  # local import to keep module clean

    patterns = [] if args.no_defaults else list(_DEFAULT_PATTERNS)
    options = RedactOptions(
        patterns=patterns,
        placeholder=args.placeholder,
        extra_patterns=args.extra_patterns,
    )
    result = redact_env(env, options=options)

    for key, value in result.redacted.items():
        print(f"{key}={value}")

    if args.summary:
        print()
        print(result.summary())

    return 0
