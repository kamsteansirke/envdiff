"""Tests for envdiff.sorter."""
import pytest

from envdiff.sorter import SortStrategy, sort_env


ENV = {
    "DB_HOST": "localhost",
    "APP_NAME": "myapp",
    "DB_PORT": "5432",
    "APP_DEBUG": "true",
    "SECRET_KEY": "abc",
    "TIMEOUT": "30",
}


def test_alpha_sorts_ascending():
    result = sort_env(ENV, SortStrategy.ALPHA)
    assert result.sorted_order == sorted(ENV.keys())


def test_alpha_desc_sorts_descending():
    result = sort_env(ENV, SortStrategy.ALPHA_DESC)
    assert result.sorted_order == sorted(ENV.keys(), reverse=True)


def test_length_sorts_by_key_length():
    result = sort_env(ENV, SortStrategy.LENGTH)
    lengths = [len(k) for k in result.sorted_order]
    assert lengths == sorted(lengths)


def test_length_stable_on_equal_length():
    env = {"BB": "1", "AA": "2", "CC": "3"}
    result = sort_env(env, SortStrategy.LENGTH)
    # equal length -> alphabetical tiebreak
    assert result.sorted_order == ["AA", "BB", "CC"]


def test_group_clusters_by_prefix():
    result = sort_env(ENV, SortStrategy.GROUP)
    # APP_ keys should be consecutive, DB_ keys consecutive
    app_indices = [result.sorted_order.index(k) for k in result.sorted_order if k.startswith("APP_")]
    db_indices  = [result.sorted_order.index(k) for k in result.sorted_order if k.startswith("DB_")]
    assert app_indices == sorted(app_indices)
    assert db_indices  == sorted(db_indices)
    # The two groups should not interleave
    assert max(app_indices) < min(db_indices) or max(db_indices) < min(app_indices)


def test_group_ungrouped_keys_go_last():
    result = sort_env(ENV, SortStrategy.GROUP)
    ungrouped = [k for k in result.sorted_order if "_" not in k]
    if ungrouped:
        last_idx = max(result.sorted_order.index(k) for k in ungrouped)
        grouped  = [k for k in result.sorted_order if "_" in k]
        first_grouped_after = any(
            result.sorted_order.index(k) > last_idx for k in grouped
        )
        assert not first_grouped_after


def test_group_respects_explicit_group_order():
    result = sort_env(ENV, SortStrategy.GROUP, group_order=["DB", "APP"])
    db_max  = max(result.sorted_order.index(k) for k in result.sorted_order if k.startswith("DB_"))
    app_min = min(result.sorted_order.index(k) for k in result.sorted_order if k.startswith("APP_"))
    assert db_max < app_min


def test_changed_is_false_when_already_sorted():
    env = {"A": "1", "B": "2", "C": "3"}
    result = sort_env(env, SortStrategy.ALPHA)
    assert not result.changed


def test_changed_is_true_when_reordered():
    env = {"C": "3", "A": "1", "B": "2"}
    result = sort_env(env, SortStrategy.ALPHA)
    assert result.changed


def test_summary_contains_strategy():
    result = sort_env(ENV, SortStrategy.ALPHA)
    assert "alpha" in result.summary()


def test_summary_group_lists_prefixes():
    result = sort_env(ENV, SortStrategy.GROUP)
    s = result.summary()
    assert "DB" in s
    assert "APP" in s


def test_empty_env_returns_empty_sorted_order():
    result = sort_env({}, SortStrategy.ALPHA)
    assert result.sorted_order == []
    assert not result.changed
