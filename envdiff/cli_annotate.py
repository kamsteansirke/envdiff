"""CLI sub-command: envdiff annotate — print an annotated .env file."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.annotator import annotate_env
from envdiff.schema import EnvSchema


def add_annotate_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "annotate",
        help="Print an .env file with inline schema/lint annotations.",
    )
    p.add_argument("env_file", help="Path to the .env file to annotate.")
    p.add_argument(
        "--schema",
        dest="schema_file",
        default=None,
        help="Optional JSON schema file (envdiff schema format).",
    )
    p.add_argument(
        "--no-lint",
        dest="no_lint",
        action="store_true",
        default=False,
        help="Skip lint annotations.",
    )
    p.add_argument(
        "--only-annotated",
        dest="only_annotated",
        action="store_true",
        default=False,
        help="Only print lines that carry an annotation.",
    )
    p.set_defaults(func=_run_annotate)


def _run_annotate(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"error: file not found: {env_path}", file=sys.stderr)
        return 2

    schema: EnvSchema | None = None
    if args.schema_file:
        schema_path = Path(args.schema_file)
        if not schema_path.exists():
            print(f"error: schema file not found: {schema_path}", file=sys.stderr)
            return 2
        raw = json.loads(schema_path.read_text(encoding="utf-8"))
        schema = EnvSchema.from_dict(raw)

    result = annotate_env(
        env_path,
        schema=schema,
        include_lint=not args.no_lint,
    )

    for line in result.lines:
        if args.only_annotated and not line.note:
            continue
        print(line.render())

    annotated_count = len(result.annotated_keys)
    if annotated_count:
        print(f"\n# {annotated_count} key(s) annotated.", file=sys.stderr)

    return 0
