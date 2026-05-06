"""CLI subcommands: baseline capture / baseline check."""
from __future__ import annotations

import argparse
import json
import sys

from envdiff.baseline import (
    BaselineError,
    capture_baseline,
    diff_against_baseline,
    load_baseline,
    save_baseline,
)
from envdiff.parser import parse_env_file


def add_baseline_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("baseline", help="Capture or check env baselines")
    sub = p.add_subparsers(dest="baseline_cmd", required=True)

    cap = sub.add_parser("capture", help="Save current env as baseline")
    cap.add_argument("env_file", help="Path to .env file")
    cap.add_argument("-o", "--output", default="baseline.json", help="Output JSON path")
    cap.set_defaults(func=_run_capture)

    chk = sub.add_parser("check", help="Compare env file against saved baseline")
    chk.add_argument("env_file", help="Path to .env file")
    chk.add_argument("-b", "--baseline", default="baseline.json", help="Baseline JSON path")
    chk.add_argument("--json", dest="as_json", action="store_true", help="Output JSON")
    chk.set_defaults(func=_run_check)


def _run_capture(args: argparse.Namespace) -> int:
    try:
        bl = capture_baseline(args.env_file)
        save_baseline(bl, args.output)
        print(f"Baseline saved to {args.output!r} ({len(bl.keys)} keys, captured {bl.captured_at})")
        return 0
    except (BaselineError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _run_check(args: argparse.Namespace) -> int:
    try:
        bl = load_baseline(args.baseline)
        current = parse_env_file(args.env_file)
    except (BaselineError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    drift = diff_against_baseline(bl, current)
    has_drift = any(drift[k] for k in ("added", "removed", "changed"))

    if args.as_json:
        print(json.dumps(drift, indent=2))
    else:
        if not has_drift:
            print("No drift detected.")
        else:
            for k, v in drift["added"].items():
                print(f"  + {k} (added)")
            for k, v in drift["removed"].items():
                print(f"  - {k} (removed)")
            for k, v in drift["changed"].items():
                print(f"  ~ {k}: {v['baseline']!r} -> {v['current']!r}")

    return 1 if has_drift else 0
