"""cli_graph.py – 'envdiff graph' sub-command.

Print the dependency graph of ${...} / $VAR references inside a .env file.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.grapher import build_graph
from envdiff.parser import parse_env_file


def add_graph_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "graph",
        help="Show key-reference dependency graph for a .env file.",
    )
    p.add_argument("file", help="Path to the .env file to analyse.")
    p.add_argument(
        "--show-undefined",
        action="store_true",
        default=False,
        help="List keys referenced but not defined in the file.",
    )
    p.add_argument(
        "--check-cycles",
        action="store_true",
        default=False,
        help="Exit with code 1 if a reference cycle is found.",
    )
    p.set_defaults(func=_run_graph)


def _run_graph(args: argparse.Namespace) -> int:
    path = Path(args.file)
    try:
        env = parse_env_file(path)
    except FileNotFoundError:
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    graph = build_graph(env)

    print(f"Graph summary: {graph.summary()}")
    print()

    for key in sorted(graph.edges):
        deps = sorted(graph.edges[key])
        if deps:
            print(f"  {key}  ->  {', '.join(deps)}")
        else:
            print(f"  {key}  (no refs)")

    if args.show_undefined and graph.undefined_refs:
        print()
        print("Undefined references:")
        for ref in sorted(graph.undefined_refs):
            print(f"  ! {ref}")

    if args.check_cycles and graph.has_cycles():
        print()
        print("error: reference cycle detected", file=sys.stderr)
        return 1

    return 0
