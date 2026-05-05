"""Command-line interface for envdiff."""

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.comparator import compare_envs
from envdiff.multi_comparator import compare_many
from envdiff.reporter import ReportOptions, format_diff, format_many


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff",
        description="Compare .env files across environments.",
    )
    p.add_argument("base", help="Base .env file")
    p.add_argument("targets", nargs="+", help="One or more target .env files")
    p.add_argument("--no-color", action="store_true", help="Disable colored output")
    p.add_argument(
        "--show-values",
        action="store_true",
        help="Show actual values in mismatch output (caution: exposes secrets)",
    )
    p.add_argument("--ignore-values", action="store_true", help="Only check key presence")
    p.add_argument("--compact", action="store_true", help="Compact output format")
    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    options = ReportOptions(
        color=not args.no_color,
        show_values=args.show_values,
        compact=args.compact,
    )

    try:
        base_data = parse_env_file(Path(args.base))
    except (EnvParseError, OSError) as exc:
        print(f"Error reading base file: {exc}", file=sys.stderr)
        return 2

    target_paths = [Path(t) for t in args.targets]

    if len(target_paths) == 1:
        try:
            target_data = parse_env_file(target_paths[0])
        except (EnvParseError, OSError) as exc:
            print(f"Error reading target file: {exc}", file=sys.stderr)
            return 2
        diff = compare_envs(base_data, target_data, target_paths[0].name, args.ignore_values)
        print(format_diff(diff, options))
        return 1 if diff.has_differences() else 0

    diffs = compare_many(Path(args.base), target_paths, args.ignore_values)
    print(format_many(diffs, options))
    return 1 if any(d.has_differences() for d in diffs) else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
