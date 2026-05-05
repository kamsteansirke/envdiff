"""Formatting and reporting utilities for envdiff output."""

from dataclasses import dataclass
from typing import List, Optional
from envdiff.comparator import EnvDiff


ANSI_RED = "\033[31m"
ANSI_YELLOW = "\033[33m"
ANSI_GREEN = "\033[32m"
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"


@dataclass
class ReportOptions:
    color: bool = True
    show_values: bool = False
    compact: bool = False


def _colorize(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{color}{text}{ANSI_RESET}"


def format_diff(diff: EnvDiff, options: Optional[ReportOptions] = None) -> str:
    """Format a single EnvDiff into a human-readable string."""
    if options is None:
        options = ReportOptions()

    lines: List[str] = []
    header = f"--- base  vs  {diff.target_name} ---"
    lines.append(_colorize(header, ANSI_BOLD, options.color))

    if not diff.has_differences():
        lines.append(_colorize("  No differences found.", ANSI_GREEN, options.color))
        return "\n".join(lines)

    for key in sorted(diff.missing_in_target):
        label = f"  MISSING in {diff.target_name}: {key}"
        lines.append(_colorize(label, ANSI_RED, options.color))

    for key in sorted(diff.missing_in_base):
        label = f"  EXTRA   in {diff.target_name}: {key}"
        lines.append(_colorize(label, ANSI_YELLOW, options.color))

    for key in sorted(diff.mismatched_values):
        if options.show_values:
            base_val = diff.base_data.get(key, "")
            target_val = diff.target_data.get(key, "")
            label = f"  MISMATCH: {key}  (base={base_val!r}, {diff.target_name}={target_val!r})"
        else:
            label = f"  MISMATCH: {key}"
        lines.append(_colorize(label, ANSI_YELLOW, options.color))

    return "\n".join(lines)


def format_many(diffs: List[EnvDiff], options: Optional[ReportOptions] = None) -> str:
    """Format multiple EnvDiff results into a combined report."""
    if options is None:
        options = ReportOptions()

    if not diffs:
        return _colorize("No comparisons to report.", ANSI_GREEN, options.color)

    sections = [format_diff(d, options) for d in diffs]
    separator = "" if options.compact else "\n"
    return ("\n" + separator).join(sections)
