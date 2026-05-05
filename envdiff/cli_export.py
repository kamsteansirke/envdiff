"""CLI sub-command: envdiff export — dump diff results to a file or stdout."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

from envdiff.comparator import compare_envs
from envdiff.exporter import ExportOptions, export_many
from envdiff.multi_comparator import compare_many
from envdiff.parser import parse_env_file


def add_export_subparser(subparsers) -> None:  # type: ignore[type-arg]
    """Register the 'export' sub-command onto an existing subparsers action."""
    p = subparsers.add_parser(
        "export",
        help="Export diff results to JSON, CSV, or Markdown",
    )
    p.add_argument("base", help="Base .env file")
    p.add_argument("targets", nargs="+", help="One or more target .env files")
    p.add_argument(
        "--format", "-f",
        choices=["json", "csv", "markdown"],
        default="json",
        dest="fmt",
        help="Output format (default: json)",
    )
    p.add_argument(
        "--show-values",
        action="store_true",
        default=False,
        help="Include actual values in the export",
    )
    p.add_argument(
        "--output", "-o",
        default=None,
        metavar="FILE",
        help="Write output to FILE instead of stdout",
    )
    p.set_defaults(func=_run_export)


def _run_export(args) -> int:  # type: ignore[type-arg]
    base_path = Path(args.base)
    try:
        base_env = parse_env_file(base_path)
    except Exception as exc:
        print(f"error: cannot parse base file: {exc}", file=sys.stderr)
        return 2

    diffs = []
    for target_str in args.targets:
        target_path = Path(target_str)
        try:
            target_env = parse_env_file(target_path)
        except Exception as exc:
            print(f"error: cannot parse {target_path}: {exc}", file=sys.stderr)
            return 2
        diffs.append(
            compare_envs(
                base_env,
                target_env,
                base_name=base_path.name,
                target_name=target_path.name,
            )
        )

    opts = ExportOptions(fmt=args.fmt, show_values=args.show_values)  # type: ignore[arg-type]
    output = export_many(diffs, opts)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)

    return 0
