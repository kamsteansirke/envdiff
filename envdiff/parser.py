"""Parser for .env files."""

from pathlib import Path
from typing import Dict, Optional


class EnvParseError(Exception):
    """Raised when a .env file cannot be parsed."""
    pass


def parse_env_file(filepath: str | Path) -> Dict[str, Optional[str]]:
    """
    Parse a .env file and return a dictionary of key-value pairs.

    Supports:
      - KEY=VALUE
      - KEY="VALUE" or KEY='VALUE' (quotes are stripped)
      - # comments (full line or inline)
      - Keys with no value (KEY=) -> empty string
      - Export prefix (export KEY=VALUE)

    Args:
        filepath: Path to the .env file.

    Returns:
        A dict mapping env var names to their string values.

    Raises:
        EnvParseError: If the file cannot be read or contains invalid syntax.
    """
    path = Path(filepath)
    if not path.exists():
        raise EnvParseError(f"File not found: {filepath}")
    if not path.is_file():
        raise EnvParseError(f"Not a file: {filepath}")

    env: Dict[str, Optional[str]] = {}

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise EnvParseError(f"Cannot read file {filepath}: {exc}") from exc

    for lineno, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        # Skip blank lines and full-line comments
        if not line or line.startswith("#"):
            continue

        # Strip optional 'export ' prefix
        if line.startswith("export "):
            line = line[len("export "):].strip()

        if "=" not in line:
            raise EnvParseError(
                f"Invalid syntax at line {lineno} in {filepath}: {raw_line!r}"
            )

        key, _, value = line.partition("=")
        key = key.strip()

        if not key:
            raise EnvParseError(
                f"Empty key at line {lineno} in {filepath}: {raw_line!r}"
            )

        # Strip inline comments (only outside quotes)
        value = _strip_inline_comment(value)

        # Strip surrounding quotes
        value = _strip_quotes(value)

        env[key] = value

    return env


def _strip_inline_comment(value: str) -> str:
    """Remove inline # comments that are not inside quotes."""
    in_single = False
    in_double = False
    for i, ch in enumerate(value):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            return value[:i].strip()
    return value.strip()


def _strip_quotes(value: str) -> str:
    """Remove surrounding single or double quotes from a value."""
    if len(value) >= 2:
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
    return value
