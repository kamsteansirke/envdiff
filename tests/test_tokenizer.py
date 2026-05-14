"""Tests for envdiff.tokenizer."""
import pytest
from envdiff.tokenizer import TokenKind, tokenize


def test_blank_line_produces_blank_token():
    result = tokenize("\n")
    assert len(result.tokens) == 1
    assert result.tokens[0].kind == TokenKind.BLANK


def test_comment_line_produces_comment_token():
    result = tokenize("# this is a comment")
    assert result.tokens[0].kind == TokenKind.COMMENT
    assert result.tokens[0].key is None


def test_simple_key_value():
    result = tokenize("FOO=bar")
    t = result.tokens[0]
    assert t.kind == TokenKind.KEY_VALUE
    assert t.key == "FOO"
    assert t.value == "bar"


def test_export_prefix_produces_export_token():
    result = tokenize("export MY_VAR=hello")
    t = result.tokens[0]
    assert t.kind == TokenKind.EXPORT
    assert t.key == "MY_VAR"
    assert t.value == "hello"


def test_invalid_line_no_equals():
    result = tokenize("NOTAVALIDLINE")
    assert result.tokens[0].kind == TokenKind.INVALID


def test_invalid_key_with_spaces():
    result = tokenize("BAD KEY=value")
    assert result.tokens[0].kind == TokenKind.INVALID


def test_empty_value_is_valid():
    result = tokenize("EMPTY=")
    t = result.tokens[0]
    assert t.kind == TokenKind.KEY_VALUE
    assert t.key == "EMPTY"
    assert t.value == ""


def test_multiple_lines():
    text = "FOO=1\n# comment\n\nBAR=2"
    result = tokenize(text)
    assert len(result.tokens) == 4
    kinds = [t.kind for t in result.tokens]
    assert kinds == [
        TokenKind.KEY_VALUE,
        TokenKind.COMMENT,
        TokenKind.BLANK,
        TokenKind.KEY_VALUE,
    ]


def test_key_value_tokens_filters_correctly():
    text = "FOO=1\n# comment\nexport BAR=2\nINVALID"
    result = tokenize(text)
    kvs = result.key_value_tokens
    assert len(kvs) == 2
    assert {t.key for t in kvs} == {"FOO", "BAR"}


def test_comment_tokens_property():
    text = "# first\nFOO=1\n# second"
    result = tokenize(text)
    assert len(result.comment_tokens) == 2


def test_invalid_tokens_property():
    text = "FOO=1\nNOT_VALID\nBAR=2"
    result = tokenize(text)
    assert len(result.invalid_tokens) == 1
    assert result.invalid_tokens[0].raw == "NOT_VALID"


def test_summary_string():
    text = "FOO=1\n# c\n\nBAD"
    result = tokenize(text)
    s = result.summary()
    assert "1 key-value" in s
    assert "1 comment" in s
    assert "1 blank" in s
    assert "1 invalid" in s


def test_token_str_kv():
    result = tokenize("KEY=val")
    s = str(result.tokens[0])
    assert "KEY" in s
    assert "val" in s


def test_token_str_comment():
    result = tokenize("# hello")
    s = str(result.tokens[0])
    assert "COMMENT" in s


def test_line_numbers_are_correct():
    text = "A=1\nB=2\nC=3"
    result = tokenize(text)
    for i, token in enumerate(result.tokens, start=1):
        assert token.line_no == i
