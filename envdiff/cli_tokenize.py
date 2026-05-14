"""CLI sub-command: tokenize — show token breakdown of a .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.tokenizer import TokenKind, tokenize


def add_tokenize_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "tokenize",
        help="Show token breakdown of a .env file",
    )
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--show-invalid",
        action="store_true",
        default=False,
        help="Print invalid lines explicitly",
    )
    p.add_argument(
        "--summary-only",
        action="store_true",
        default=False,
        help="Print only the summary line",
    )
    p.set_defaults(func=_run_tokenize)


def _run_tokenize(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8")
    result = tokenize(text)

    if not args.summary_only:
        for token in result.tokens:
            if token.kind == TokenKind.KEY_VALUE or token.kind == TokenKind.EXPORT:
                tag = "EXPORT" if token.kind == TokenKind.EXPORT else "KV"
                print(f"  [{tag:6}] line {token.line_no:>4}: {token.key}")
            elif token.kind == TokenKind.COMMENT:
                print(f"  [COMMENT] line {token.line_no:>4}: {token.raw.strip()[:60]}")
            elif token.kind == TokenKind.BLANK:
                print(f"  [BLANK ] line {token.line_no:>4}")
            elif token.kind == TokenKind.INVALID and args.show_invalid:
                print(
                    f"  [INVALID] line {token.line_no:>4}: {token.raw.strip()[:60]}",
                    file=sys.stderr,
                )

    print(result.summary())

    return 1 if result.invalid_tokens else 0
