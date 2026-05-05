"""CLI sub-command: envdiff watch — live-watch .env files for drift."""

from __future__ import annotations

import argparse
from pathlib import Path

from envdiff.reporter import ReportOptions
from envdiff.watcher import EnvWatcher


def add_watch_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *watch* sub-command onto *subparsers*."""
    p = subparsers.add_parser(
        "watch",
        help="Poll .env files and print diffs when files change.",
    )
    p.add_argument("base", type=Path, help="Base .env file.")
    p.add_argument("targets", type=Path, nargs="+", help="Target .env files to compare.")
    p.add_argument(
        "--interval",
        type=float,
        default=2.0,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 2.0).",
    )
    p.add_argument(
        "--show-values",
        action="store_true",
        default=False,
        help="Show actual values in output.",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output.",
    )
    p.set_defaults(func=_run_watch)


def _run_watch(args: argparse.Namespace) -> int:
    options = ReportOptions(
        show_values=args.show_values,
        color=not args.no_color,
    )

    def _on_change(label: str, diff) -> None:  # type: ignore[type-arg]
        from envdiff.reporter import format_diff

        print(f"[envdiff:watch] change detected — {label}")
        print(format_diff(diff, options))
        print()

    watcher = EnvWatcher(
        base=args.base,
        targets=args.targets,
        options=options,
        poll_interval=args.interval,
        on_change=_on_change,
    )
    print(f"[envdiff:watch] watching {args.base} against {[str(t) for t in args.targets]}")
    print(f"[envdiff:watch] poll interval: {args.interval}s  (Ctrl-C to stop)")
    watcher.watch()
    return 0
