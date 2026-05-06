"""CLI sub-command: envdiff rename

Detect probable key renames between a base and a target .env file.
"""
from __future__ import annotations

import argparse
import sys
from typing import List

from envdiff.parser import parse_env_file
from envdiff.renamer import detect_renames


def add_rename_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "rename",
        help="Detect probable key renames between two .env files.",
    )
    p.add_argument("base", help="Base .env file (e.g. .env.example)")
    p.add_argument("target", help="Target .env file to compare against base")
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output",
    )
    p.set_defaults(func=_run_rename)


def _color(text: str, code: str, enabled: bool) -> str:
    if not enabled:
        return text
    return f"\033[{code}m{text}\033[0m"


def _run_rename(args: argparse.Namespace) -> int:
    try:
        base_env = parse_env_file(args.base)
        target_env = parse_env_file(args.target)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 2

    use_color = not args.no_color
    result = detect_renames(base_env, target_env)

    if result.candidates:
        header = _color("Rename candidates:", "1;34", use_color)
        print(header)
        for c in result.candidates:
            old = _color(c.old_key, "31", use_color)
            new = _color(c.new_key, "32", use_color)
            tag = _color(f"[{c.confidence}]", "33", use_color)
            print(f"  {old} -> {new}  {tag}")
    else:
        print("No rename candidates detected.")

    if result.unmatched_removed:
        label = _color("Removed (unmatched):", "1", use_color)
        print(f"{label} {', '.join(sorted(result.unmatched_removed))}")

    if result.unmatched_added:
        label = _color("Added (unmatched):", "1", use_color)
        print(f"{label} {', '.join(sorted(result.unmatched_added))}")

    return 1 if result.has_candidates else 0
