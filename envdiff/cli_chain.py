"""CLI sub-command: envdiff chain — compare a base .env against many targets."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file
from envdiff.comparator_chain import compare_chain


def add_chain_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "chain",
        help="Compare a base .env against one or more target files.",
    )
    p.add_argument("base", metavar="BASE", help="Base .env file path.")
    p.add_argument(
        "targets",
        metavar="TARGET",
        nargs="+",
        help="One or more target .env file paths.",
    )
    p.add_argument(
        "--ignore-values",
        action="store_true",
        default=False,
        help="Report key presence differences only; ignore value mismatches.",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output.",
    )
    p.set_defaults(func=_run_chain)


def _color(text: str, code: str, *, enabled: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if enabled else text


def _run_chain(args: argparse.Namespace) -> int:
    base_path = Path(args.base)
    use_color = not args.no_color and sys.stdout.isatty()

    try:
        base_env = parse_env_file(base_path)
    except Exception as exc:  # noqa: BLE001
        print(f"error reading base file: {exc}", file=sys.stderr)
        return 2

    targets: dict[str, dict[str, str]] = {}
    for raw in args.targets:
        path = Path(raw)
        try:
            targets[path.name] = parse_env_file(path)
        except Exception as exc:  # noqa: BLE001
            print(f"error reading {raw}: {exc}", file=sys.stderr)
            return 2

    result = compare_chain(
        base_env,
        targets,
        base_name=base_path.name,
        ignore_values=args.ignore_values,
    )

    print(result.summary())

    for label in result.target_names:
        diff = result.diff_for(label)
        if diff is None or not diff.has_differences:
            continue
        for key in sorted(diff.missing_in_target):
            print(_color(f"  [{label}] MISSING  {key}", "31", enabled=use_color))
        for key in sorted(diff.missing_in_base):
            print(_color(f"  [{label}] EXTRA    {key}", "33", enabled=use_color))
        for key in sorted(diff.mismatched):
            print(_color(f"  [{label}] MISMATCH {key}", "35", enabled=use_color))

    return 1 if result.any_differences else 0
