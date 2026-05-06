"""Generate a .env.example template from one or more parsed env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from envdiff.parser import parse_env_file


@dataclass
class TemplateEntry:
    key: str
    comment: Optional[str] = None
    example_value: str = ""

    def render(self) -> str:
        lines: List[str] = []
        if self.comment:
            lines.append(f"# {self.comment}")
        lines.append(f"{self.key}={self.example_value}")
        return "\n".join(lines)


@dataclass
class TemplateResult:
    entries: List[TemplateEntry] = field(default_factory=list)

    @property
    def keys(self) -> List[str]:
        return [e.key for e in self.entries]

    def render(self) -> str:
        """Return the full template as a string."""
        return "\n".join(e.render() for e in self.entries)

    def write(self, path: Path) -> None:
        path.write_text(self.render() + "\n", encoding="utf-8")


def build_template(
    env_files: Iterable[Path],
    *,
    placeholder: str = "",
    comments: Optional[Dict[str, str]] = None,
    sort_keys: bool = True,
) -> TemplateResult:
    """Merge keys from *env_files* into a single template.

    Args:
        env_files: Paths to .env files to read keys from.
        placeholder: Value to use for every key in the template.
        comments: Optional mapping of key -> comment string.
        sort_keys: Whether to sort keys alphabetically (default True).

    Returns:
        A :class:`TemplateResult` with one entry per unique key.
    """
    comments = comments or {}
    seen: Dict[str, None] = {}

    for path in env_files:
        data = parse_env_file(path)
        for key in data:
            seen.setdefault(key, None)

    ordered = sorted(seen) if sort_keys else list(seen)

    entries = [
        TemplateEntry(
            key=k,
            comment=comments.get(k),
            example_value=placeholder,
        )
        for k in ordered
    ]
    return TemplateResult(entries=entries)
