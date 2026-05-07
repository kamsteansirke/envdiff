"""Tests for envdiff.summarizer."""
from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.summarizer import summarize_files, FileSummary, SummaryReport


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


def test_summarize_empty_list_returns_empty_report():
    report = summarize_files([])
    assert report.files == []
    assert report.overall_grade() == "N/A"
    assert report.render() == "No files summarized."


def test_summarize_single_clean_file(env_dir):
    p = _write(env_dir, ".env", "APP_NAME=myapp\nDEBUG=false\n")
    report = summarize_files([p])
    assert len(report.files) == 1
    fs = report.files[0]
    assert fs.path == p
    assert fs.key_count == 2
    assert fs.empty_count == 0
    assert isinstance(fs.health_score, float)
    assert fs.grade in {"A", "B", "C", "D", "F"}


def test_summarize_file_with_empty_values(env_dir):
    p = _write(env_dir, ".env", "KEY_A=\nKEY_B=value\n")
    report = summarize_files([p])
    fs = report.files[0]
    assert fs.empty_count == 1
    assert fs.key_count == 2


def test_summarize_multiple_files(env_dir):
    p1 = _write(env_dir, ".env.dev", "HOST=localhost\nPORT=8080\n")
    p2 = _write(env_dir, ".env.prod", "HOST=prod.example.com\nPORT=443\nSECRET=abc\n")
    report = summarize_files([p1, p2])
    assert len(report.files) == 2
    names = [fs.path.name for fs in report.files]
    assert ".env.dev" in names
    assert ".env.prod" in names


def test_overall_grade_is_string(env_dir):
    p = _write(env_dir, ".env", "A=1\nB=2\n")
    report = summarize_files([p])
    grade = report.overall_grade()
    assert grade in {"A", "B", "C", "D", "F"}


def test_render_contains_filename(env_dir):
    p = _write(env_dir, ".env.staging", "FOO=bar\n")
    report = summarize_files([p])
    output = report.render()
    assert ".env.staging" in output
    assert "keys" in output
    assert "Overall grade" in output


def test_file_summary_one_line(env_dir):
    p = _write(env_dir, ".env", "X=1\n")
    report = summarize_files([p])
    line = report.files[0].one_line()
    assert ".env" in line
    assert "keys" in line
    assert "score=" in line
