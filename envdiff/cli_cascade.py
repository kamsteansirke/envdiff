"""CLI sub-command: cascade — resolve .env files in priority order."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from envdiff.cascader import cascade_envs


def add_cascade_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "cascade",
        help="Resolve keys by cascading env files from lowest to highest priority.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Env files in priority order (last file wins).",
    )
    p.add_argument(
        "--labels",
        nargs="+",
        metavar="LABEL",
        default=None,
        help="Optional display labels for each file (must match file count).",
    )
    p.add_argument(
        "--show-values",
        action="store_true",
        default=False,
        help="Print resolved values alongside keys.",
    )
    p.add_argument(
        "--overrides-only",
        action="store_true",
        default=False,
        help="Only list keys that were overridden by a higher-priority layer.",
    )
    p.set_defaults(func=_run_cascade)


def _run_cascade(args: argparse.Namespace) -> int:
    paths = [Path(f) for f in args.files]
    for p in paths:
        if not p.exists():
            print(f"error: file not found: {p}", file=sys.stderr)
            return 2

    labels: Optional[List[str]] = args.labels
    try:
        result = cascade_envs(paths, labels=labels)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(result.summary())
    print()

    keys_to_show = result.overrides if args.overrides_only else result.keys

    if not keys_to_show:
        print("(no keys to display)")
        return 0

    for key in keys_to_show:
        entry = result.entries[key]
        if args.show_values:
            line = f"  {key}={entry.value!r}  [{entry.source}]"
        else:
            line = f"  {key}  [{entry.source}]"
        if entry.overridden_by:
            line += f"  (overrides: {', '.join(entry.overridden_by[:1])})"
        print(line)

    return 0
