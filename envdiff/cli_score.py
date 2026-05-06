"""CLI sub-command: envdiff score — print a health score for a .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.comparator import compare_envs
from envdiff.linter import lint_env
from envdiff.auditor import audit_env, AuditResult
from envdiff.schema import EnvSchema
from envdiff.scorer import score_env


def add_score_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "score",
        help="Compute a health score (0-100) for a target .env file.",
    )
    p.add_argument("base", help="Base .env file (reference)")
    p.add_argument("target", help="Target .env file to score")
    p.add_argument(
        "--schema",
        metavar="FILE",
        help="Optional JSON/YAML schema file for audit checks",
    )
    p.add_argument(
        "--no-lint",
        action="store_true",
        default=False,
        help="Skip lint checks",
    )
    p.add_argument(
        "--fail-under",
        type=int,
        default=0,
        metavar="N",
        help="Exit with code 2 if score is below N (default: 0 = never fail)",
    )
    p.set_defaults(func=_run_score)


def _run_score(args: argparse.Namespace) -> int:
    base_path = Path(args.base)
    target_path = Path(args.target)

    try:
        base_env = parse_env_file(base_path)
        target_env = parse_env_file(target_path)
    except EnvParseError as exc:
        print(f"Parse error: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"File not found: {exc}", file=sys.stderr)
        return 1

    diff = compare_envs(base_env, target_env, base_name=args.base, target_name=args.target)

    lint_result = None
    if not args.no_lint:
        lint_result = lint_env(target_env)

    audit_result: Optional[AuditResult] = None
    if args.schema:
        try:
            import json
            schema_data = json.loads(Path(args.schema).read_text())
            schema = EnvSchema.from_dict(schema_data)
            audit_result = audit_env(target_env, schema)
        except Exception as exc:  # noqa: BLE001
            print(f"Schema error: {exc}", file=sys.stderr)
            return 1

    health = score_env(diff=diff, lint=lint_result, audit=audit_result)

    print(str(health))
    if health.notes:
        for note in health.notes:
            print(f"  - {note}")

    if args.fail_under and health.score < args.fail_under:
        return 2
    return 0
