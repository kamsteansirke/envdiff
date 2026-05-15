"""CLI sub-command: envdiff matrix — compare all pairs of env files."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.comparator_matrix import build_matrix


def add_matrix_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "matrix",
        help="Compare every pair of env files and show a summary matrix.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Two or more .env files to compare.",
    )
    p.add_argument(
        "--ignore-values",
        action="store_true",
        default=False,
        help="Only check key presence, ignore value differences.",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
    )
    p.set_defaults(func=_run_matrix)


def _color(text: str, code: str, *, no_color: bool) -> str:
    if no_color:
        return text
    return f"\033[{code}m{text}\033[0m"


def _run_matrix(args: argparse.Namespace) -> int:
    paths = args.files
    if len(paths) < 2:
        print("error: at least two files required", file=sys.stderr)
        return 2

    env_map = {Path(p).stem: p for p in paths}
    result = build_matrix(env_map, ignore_values=args.ignore_values)

    no_color = getattr(args, "no_color", False)

    header = "  " + "  ".join(f"{n:>12}" for n in result.env_names)
    print(header)

    for base in result.env_names:
        row_parts = [f"{base:>12}"]
        for target in result.env_names:
            if base == target:
                row_parts.append(f"{'—':>12}")
            else:
                cell = result.cell(base, target)
                if cell and cell.is_clean:
                    row_parts.append(
                        _color(f"{'OK':>12}", "32", no_color=no_color)
                    )
                else:
                    row_parts.append(
                        _color(f"{'DIFF':>12}", "31", no_color=no_color)
                    )
        print("  ".join(row_parts))

    print()
    print(result.summary())
    return 1 if result.dirty_pairs() else 0
