"""CLI sub-command: envdiff prune — report or remove obsolete keys."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.parser import parse_env_file
from envdiff.pruner import prune_env


def add_prune_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "prune",
        help="Identify keys in a .env file that are absent from a reference key list.",
    )
    p.add_argument("env_file", help="Path to the .env file to inspect.")
    p.add_argument(
        "--reference",
        metavar="FILE",
        required=True,
        help="Path to a reference .env file whose keys define the allowed set.",
    )
    p.add_argument(
        "--reason",
        default=None,
        metavar="TEXT",
        help="Custom reason string attached to each flagged key.",
    )
    p.add_argument(
        "--json",
        dest="output_json",
        action="store_true",
        default=False,
        help="Emit results as JSON instead of plain text.",
    )
    p.add_argument(
        "--write",
        action="store_true",
        default=False,
        help="Rewrite env_file in-place with obsolete keys removed.",
    )
    p.set_defaults(func=_run_prune)


def _run_prune(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    ref_path = Path(args.reference)

    env = parse_env_file(env_path)
    ref = parse_env_file(ref_path)

    result = prune_env(
        env,
        reference=ref.keys(),
        source=env_path.name,
        extra_reason=args.reason,
    )

    if args.output_json:
        data = {
            "source": result.source,
            "is_clean": result.is_clean(),
            "kept": result.kept,
            "obsolete": [
                {"key": i.key, "reason": i.reason} for i in result.issues
            ],
        }
        print(json.dumps(data, indent=2))
    else:
        print(result.summary())
        for issue in result.issues:
            print(f"  - {issue}")

    if args.write and not result.is_clean():
        pruned = result.pruned_env()
        lines = [f"{k}={v}\n" for k, v in pruned.items()]
        env_path.write_text("".join(lines))
        removed = len(result.issues)
        print(f"Rewrote {env_path.name}: {removed} key(s) removed.", file=sys.stderr)

    return 0 if result.is_clean() else 1
