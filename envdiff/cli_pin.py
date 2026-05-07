"""CLI subcommands: pin capture / pin check."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.pinner import PinError, check_pin, create_pin, save_pin


def add_pin_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser("pin", help="Pin or check env key drift")
    sub = parser.add_subparsers(dest="pin_cmd", required=True)

    cap = sub.add_parser("capture", help="Capture current env state as a pin")
    cap.add_argument("env_file", help="Path to .env file")
    cap.add_argument("--pin-file", default=".envpin", help="Output pin file (default: .envpin)")
    cap.add_argument("--pin-values", action="store_true", help="Also hash values")
    cap.set_defaults(func=_run_capture)

    chk = sub.add_parser("check", help="Check env file against saved pin")
    chk.add_argument("env_file", help="Path to .env file")
    chk.add_argument("--pin-file", default=".envpin", help="Pin file to compare (default: .envpin)")
    chk.add_argument("--pin-values", action="store_true", help="Also compare value hashes")
    chk.set_defaults(func=_run_check)


def _run_capture(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    pin_path = Path(args.pin_file)
    try:
        entries = create_pin(env_path, pin_values=args.pin_values)
        save_pin(entries, pin_path)
    except (PinError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Pinned {len(entries)} key(s) to {pin_path}")
    return 0


def _run_check(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    pin_path = Path(args.pin_file)
    try:
        result = check_pin(env_path, pin_path, pin_values=args.pin_values)
    except (PinError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(result.summary())
    if result.added:
        for k in sorted(result.added):
            print(f"  + {k}")
    if result.removed:
        for k in sorted(result.removed):
            print(f"  - {k}")
    if result.changed:
        for k in sorted(result.changed):
            print(f"  ~ {k}")
    return 0 if result.is_clean else 1
