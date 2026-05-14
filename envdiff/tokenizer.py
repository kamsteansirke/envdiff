"""Tokenize .env file content into typed tokens for downstream analysis."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List


class TokenKind(Enum):
    KEY_VALUE = auto()
    COMMENT = auto()
    BLANK = auto()
    EXPORT = auto()
    INVALID = auto()


@dataclass
class Token:
    kind: TokenKind
    raw: str
    line_no: int
    key: str | None = None
    value: str | None = None

    def __str__(self) -> str:
        if self.key is not None:
            return f"[{self.kind.name}:{self.line_no}] {self.key}={self.value!r}"
        return f"[{self.kind.name}:{self.line_no}] {self.raw!r}"


@dataclass
class TokenizeResult:
    tokens: List[Token]

    @property
    def key_value_tokens(self) -> List[Token]:
        return [t for t in self.tokens if t.kind in (TokenKind.KEY_VALUE, TokenKind.EXPORT)]

    @property
    def comment_tokens(self) -> List[Token]:
        return [t for t in self.tokens if t.kind == TokenKind.COMMENT]

    @property
    def invalid_tokens(self) -> List[Token]:
        return [t for t in self.tokens if t.kind == TokenKind.INVALID]

    def summary(self) -> str:
        kv = len(self.key_value_tokens)
        comments = len(self.comment_tokens)
        blanks = sum(1 for t in self.tokens if t.kind == TokenKind.BLANK)
        invalid = len(self.invalid_tokens)
        return (
            f"{kv} key-value(s), {comments} comment(s), "
            f"{blanks} blank(s), {invalid} invalid line(s)"
        )


_VALID_KEY_CHARS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_"
)


def _parse_kv(raw: str) -> tuple[str, str] | None:
    """Return (key, value) or None if the line is not a valid key=value pair."""
    line = raw.strip()
    export = False
    if line.startswith("export "):
        line = line[7:].lstrip()
        export = True
    if "=" not in line:
        return None
    key, _, value = line.partition("=")
    key = key.strip()
    if not key or not all(c in _VALID_KEY_CHARS for c in key):
        return None
    return key, value.strip()


def tokenize(text: str) -> TokenizeResult:
    """Tokenize raw .env file text into a TokenizeResult."""
    tokens: List[Token] = []
    for line_no, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped:
            tokens.append(Token(kind=TokenKind.BLANK, raw=raw, line_no=line_no))
        elif stripped.startswith("#"):
            tokens.append(Token(kind=TokenKind.COMMENT, raw=raw, line_no=line_no))
        else:
            is_export = stripped.startswith("export ")
            result = _parse_kv(stripped)
            if result is None:
                tokens.append(Token(kind=TokenKind.INVALID, raw=raw, line_no=line_no))
            else:
                key, value = result
                kind = TokenKind.EXPORT if is_export else TokenKind.KEY_VALUE
                tokens.append(
                    Token(kind=kind, raw=raw, line_no=line_no, key=key, value=value)
                )
    return TokenizeResult(tokens=tokens)
