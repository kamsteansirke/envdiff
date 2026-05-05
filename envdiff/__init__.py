"""envdiff — Compare .env files across environments."""

from envdiff.comparator import EnvDiff, compare_envs, has_differences, summary
from envdiff.exporter import ExportOptions, export_diff, export_many
from envdiff.multi_comparator import compare_many, full_summary
from envdiff.parser import EnvParseError, parse_env_file
from envdiff.reporter import ReportOptions, format_diff, format_many

__all__ = [
    # parser
    "EnvParseError",
    "parse_env_file",
    # comparator
    "EnvDiff",
    "compare_envs",
    "has_differences",
    "summary",
    # multi_comparator
    "compare_many",
    "full_summary",
    # reporter
    "ReportOptions",
    "format_diff",
    "format_many",
    # exporter
    "ExportOptions",
    "export_diff",
    "export_many",
]

__version__ = "0.1.0"
