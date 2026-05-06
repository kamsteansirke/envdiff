"""Tests for envdiff.grouper."""
import pytest
from envdiff.grouper import GroupResult, group_by_prefix, group_env


# ---------------------------------------------------------------------------
# GroupResult
# ---------------------------------------------------------------------------

class TestGroupResult:
    def test_group_names_sorted(self):
        gr = GroupResult(groups={"DB": ["DB_HOST"], "AWS": ["AWS_KEY"]}, ungrouped=[])
        assert gr.group_names() == ["AWS", "DB"]

    def test_summary_with_groups_and_ungrouped(self):
        gr = GroupResult(
            groups={"DB": ["DB_HOST", "DB_PORT"]},
            ungrouped=["DEBUG"],
        )
        text = gr.summary()
        assert "[DB]" in text
        assert "2 key(s)" in text
        assert "[ungrouped]" in text

    def test_summary_empty(self):
        gr = GroupResult()
        assert gr.summary() == "(no keys)"


# ---------------------------------------------------------------------------
# group_by_prefix
# ---------------------------------------------------------------------------

class TestGroupByPrefix:
    def test_basic_grouping(self):
        keys = ["DB_HOST", "DB_PORT", "AWS_KEY", "AWS_SECRET", "DEBUG"]
        result = group_by_prefix(keys, separator="_", min_group_size=2)
        assert set(result.groups["DB"]) == {"DB_HOST", "DB_PORT"}
        assert set(result.groups["AWS"]) == {"AWS_KEY", "AWS_SECRET"}
        assert "DEBUG" in result.ungrouped

    def test_min_group_size_one_includes_singletons(self):
        keys = ["DB_HOST", "SOLO"]
        result = group_by_prefix(keys, min_group_size=1)
        assert "DB" in result.groups
        # SOLO has no underscore so goes ungrouped regardless
        assert "SOLO" in result.ungrouped

    def test_no_separator_all_ungrouped(self):
        keys = ["FOO", "BAR", "BAZ"]
        result = group_by_prefix(keys)
        assert result.groups == {}
        assert set(result.ungrouped) == {"FOO", "BAR", "BAZ"}

    def test_empty_keys(self):
        result = group_by_prefix([])
        assert result.groups == {}
        assert result.ungrouped == []

    def test_max_prefix_parts_two(self):
        keys = ["AWS_S3_BUCKET", "AWS_S3_REGION", "AWS_EC2_AMI"]
        result = group_by_prefix(keys, separator="_", min_group_size=2, max_prefix_parts=2)
        assert "AWS_S3" in result.groups
        assert set(result.groups["AWS_S3"]) == {"AWS_S3_BUCKET", "AWS_S3_REGION"}
        assert "AWS_EC2_AMI" in result.ungrouped


# ---------------------------------------------------------------------------
# group_env
# ---------------------------------------------------------------------------

class TestGroupEnv:
    def test_groups_dict_keys(self):
        env = {
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "SECRET_KEY": "abc",
            "SECRET_SALT": "xyz",
            "DEBUG": "true",
        }
        result = group_env(env, min_group_size=2)
        assert "DB" in result.groups
        assert "SECRET" in result.groups
        assert "DEBUG" in result.ungrouped

    def test_empty_env(self):
        result = group_env({})
        assert result.groups == {}
        assert result.ungrouped == []

    def test_all_ungrouped_when_min_group_size_high(self):
        env = {"DB_HOST": "h", "DB_PORT": "p"}
        result = group_env(env, min_group_size=5)
        assert result.groups == {}
        assert set(result.ungrouped) == {"DB_HOST", "DB_PORT"}
