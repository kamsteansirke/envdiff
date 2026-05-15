"""cli_digest.py – 'envdiff digest' sub-command."""
from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from envdiff.digester import digest_many, compare_digests


def add_digest_subparser(sub: "_SubParsersAction") -> None:  # type: ignore[type-arg]
    p: ArgumentParser = sub.add_parser(
        "digest",
        help="Print SHA-256 fingerprints for one or more .env files.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help=".env files to fingerprint.",
    )
    p.add_argument(
        "--keys-only",
        action="store_true",
        default=False,
        help="Hash keys only (ignore values).",
    )
    p.add_argument(
        "--check-identical",
        action="store_true",
        default=False,
        help="Exit 1 if files do not share the same digest.",
    )
    p.set_defaults(func=_run_digest)


def _run_digest(args: Namespace) -> int:
    paths = [Path(f) for f in args.files]
    results = digest_many(paths, keys_only=args.keys_only)

    for r in results:
        mode = "keys-only" if r.keys_only else "full"
        print(f"{r.digest}  {r.path}  ({r.key_count} keys, {mode})")

    if args.check_identical:
        common = compare_digests(results)
        if common is None:
            print("\ndigest: files differ", file=sys.stderr)
            return 1
        print(f"\ndigest: all files match ({common[:12]})")

    return 0


def main() -> None:  # pragma: no cover
    parser = ArgumentParser(prog="envdiff-digest")
    subs = parser.add_subparsers()
    add_digest_subparser(subs)
    args = parser.parse_args()
    if hasattr(args, "func"):
        sys.exit(args.func(args))
