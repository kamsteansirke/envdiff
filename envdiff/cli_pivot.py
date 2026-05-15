"""CLI sub-command: envdiff pivot — key-centric cross-environment table."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from envdiff.parser import parse_env_file
from envdiff.pivot import PivotTable, pivot_envs

_RESET = "\033[0m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_GREEN = "\033[32m"
_BOLD = "\033[1m"


def add_pivot_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("pivot", help="Key-centric cross-environment table")
    p.add_argument("files", nargs="+", metavar="FILE", help=".env files to pivot")
    p.add_argument("--show-values", action="store_true", help="Display actual values")
    p.add_argument("--only-gaps", action="store_true", help="Only show rows with missing keys")
    p.add_argument("--only-mismatches", action="store_true", help="Only show inconsistent rows")
    p.add_argument("--no-color", action="store_true", help="Disable ANSI colour output")
    p.set_defaults(func=_run_pivot)


def _run_pivot(args: argparse.Namespace) -> int:
    envs = {}
    for path_str in args.files:
        path = Path(path_str)
        try:
            envs[path.name] = parse_env_file(path)
        except Exception as exc:  # noqa: BLE001
            print(f"error: {path}: {exc}", file=sys.stderr)
            return 2

    table = pivot_envs(envs)

    rows = table.rows
    if args.only_gaps:
        rows = table.missing_rows()
    elif args.only_mismatches:
        rows = table.inconsistent_rows()

    color = not args.no_color
    _render(table, rows, show_values=args.show_values, color=color)
    print()
    print(table.summary())
    return 1 if table.missing_rows() or table.inconsistent_rows() else 0


def _render(table: PivotTable, rows, *, show_values: bool, color: bool) -> None:
    col_w = max((len(n) for n in table.env_names), default=8)
    key_w = max((len(r.key) for r in rows), default=3) if rows else 3

    header = f"{'KEY':<{key_w}}  " + "  ".join(f"{n:<{col_w}}" for n in table.env_names)
    print(header)
    print("-" * len(header))

    for row in rows:
        parts: List[str] = []
        for name in table.env_names:
            val = row.values[name]
            if val is None:
                cell = "(missing)"
                cell = _c(cell, _RED, color)
            else:
                cell = val if show_values else "present"
                cell = _c(cell, _GREEN, color)
            parts.append(f"{cell:<{col_w}}")
        key_label = row.key if row.is_consistent() else _c(row.key, _YELLOW, color)
        print(f"{key_label:<{key_w}}  " + "  ".join(parts))


def _c(text: str, code: str, enabled: bool) -> str:
    return f"{code}{text}{_RESET}" if enabled else text
