"""CLI sub-command: envdiff audit — validate .env files against a schema."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from envdiff.auditor import audit_many
from envdiff.schema import EnvSchema


def add_audit_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "audit",
        help="Audit .env files against a schema for compliance.",
    )
    p.add_argument(
        "schema",
        help="Path to a JSON schema file (envdiff schema format).",
    )
    p.add_argument(
        "envfiles",
        nargs="+",
        help="One or more .env files to audit.",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Fail on keys not declared in the schema (undeclared keys).",
    )
    p.add_argument(
        "--json",
        dest="output_json",
        action="store_true",
        default=False,
        help="Emit results as JSON instead of human-readable text.",
    )
    p.set_defaults(func=_run_audit)


def _run_audit(args: argparse.Namespace) -> int:
    schema_path = Path(args.schema)
    if not schema_path.exists():
        print(f"error: schema file not found: {schema_path}", file=sys.stderr)
        return 2

    with schema_path.open() as fh:
        raw = json.load(fh)

    schema = EnvSchema.from_dict(raw)
    results = audit_many(
        args.envfiles,
        schema,
        allow_undeclared=not args.strict,
    )

    if args.output_json:
        payload = [
            {
                "file": r.env_file,
                "passed": r.passed,
                "violations": [
                    {"key": v.key, "kind": v.kind, "message": v.message}
                    for v in r.violations
                ],
            }
            for r in results
        ]
        print(json.dumps(payload, indent=2))
    else:
        for r in results:
            print(r.summary())

    all_passed = all(r.passed for r in results)
    return 0 if all_passed else 1
