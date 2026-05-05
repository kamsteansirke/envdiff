"""CLI sub-command: envdiff validate

Validates one or more .env files against a JSON schema file.

Usage:
    envdiff validate --schema schema.json .env .env.staging
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from envdiff.parser import parse_env_file
from envdiff.schema import EnvSchema, SchemaError


def add_validate_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *validate* sub-command on *subparsers*."""
    parser = subparsers.add_parser(
        "validate",
        help="Validate .env files against a JSON schema",
    )
    parser.add_argument(
        "--schema",
        required=True,
        metavar="FILE",
        help="Path to the JSON schema file",
    )
    parser.add_argument(
        "envfiles",
        nargs="+",
        metavar="ENV_FILE",
        help="One or more .env files to validate",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output",
    )
    parser.set_defaults(func=_run_validate)


def _run_validate(args: argparse.Namespace) -> int:
    """Execute the validate sub-command.  Returns an exit code."""
    try:
        schema = EnvSchema.from_json_file(Path(args.schema))
    except SchemaError as exc:
        print(f"Schema error: {exc}", file=sys.stderr)
        return 2

    use_color = not args.no_color and sys.stdout.isatty()
    all_ok = True

    for env_path_str in args.envfiles:
        env_path = Path(env_path_str)
        try:
            env = parse_env_file(env_path)
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] Could not parse {env_path}: {exc}", file=sys.stderr)
            all_ok = False
            continue

        violations = schema.validate(env)
        if violations:
            all_ok = False
            header = f"✗ {env_path}" if use_color else f"FAIL {env_path}"
            if use_color:
                header = f"\033[31m{header}\033[0m"
            print(header)
            for v in violations:
                line = f"  - {v}"
                print(line)
        else:
            header = f"✓ {env_path}" if use_color else f"OK   {env_path}"
            if use_color:
                header = f"\033[32m{header}\033[0m"
            print(header)

    return 0 if all_ok else 1
