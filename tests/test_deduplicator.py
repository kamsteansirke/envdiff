"""Tests for envdiff.deduplicator and envdiff.cli_dedup."""
from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.deduplicator import DeduplicateResult, DuplicateEntry, find_duplicates
from envdiff.cli_dedup import _run_dedup, add_dedup_subparser


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# DeduplicateResult helpers
# ---------------------------------------------------------------------------

def test_no_duplicates_has_duplicates_false(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "FOO=1\nBAR=2\n")
    result = find_duplicates(p)
    assert not result.has_duplicates


def test_no_duplicates_summary(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "FOO=1\n")
    result = find_duplicates(p)
    assert "no duplicate keys" in result.summary()


def test_detects_single_duplicate(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "FOO=1\nBAR=2\nFOO=3\n")
    result = find_duplicates(p)
    assert result.has_duplicates
    assert len(result.duplicates) == 1
    assert result.duplicates[0].key == "FOO"
    assert result.duplicates[0].lines == [1, 3]


def test_detects_multiple_duplicates(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "A=1\nB=2\nA=3\nB=4\nB=5\n")
    result = find_duplicates(p)
    assert len(result.duplicates) == 2
    keys = {d.key for d in result.duplicates}
    assert keys == {"A", "B"}


def test_ignores_comments_and_blank_lines(env_dir: Path) -> None:
    content = "# comment\n\nFOO=1\n# another\nFOO=2\n"
    p = _write(env_dir, ".env", content)
    result = find_duplicates(p)
    assert result.duplicates[0].lines == [3, 5]


def test_export_prefix_stripped(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "export FOO=1\nFOO=2\n")
    result = find_duplicates(p)
    assert result.has_duplicates
    assert result.duplicates[0].key == "FOO"


def test_duplicate_entry_str() -> None:
    entry = DuplicateEntry(key="KEY", lines=[2, 7])
    assert "KEY" in str(entry)
    assert "2" in str(entry)
    assert "7" in str(entry)


def test_summary_lists_duplicates(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "X=1\nX=2\n")
    result = find_duplicates(p)
    summary = result.summary()
    assert "1 duplicate" in summary
    assert "X" in summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

class FakeArgs:
    def __init__(self, files, strict=False):
        self.files = files
        self.strict = strict


def test_run_dedup_clean_exits_zero(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "FOO=1\nBAR=2\n")
    code = _run_dedup(FakeArgs(files=[str(p)]))
    assert code == 0


def test_run_dedup_with_duplicate_no_strict_exits_zero(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "FOO=1\nFOO=2\n")
    code = _run_dedup(FakeArgs(files=[str(p)], strict=False))
    assert code == 0


def test_run_dedup_with_duplicate_strict_exits_one(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "FOO=1\nFOO=2\n")
    code = _run_dedup(FakeArgs(files=[str(p)], strict=True))
    assert code == 1


def test_run_dedup_missing_file_exits_two(env_dir: Path) -> None:
    code = _run_dedup(FakeArgs(files=[str(env_dir / "ghost.env")]))
    assert code == 2


def test_add_dedup_subparser_registers_command() -> None:
    import argparse
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_dedup_subparser(sub)
    args = root.parse_args(["dedup", "/tmp/x.env"])
    assert args.func is _run_dedup
    assert args.files == ["/tmp/x.env"]
    assert args.strict is False
