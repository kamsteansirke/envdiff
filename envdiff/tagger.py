"""Tag keys in an env file with arbitrary labels for categorisation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Mapping, Set


@dataclass
class TagResult:
    """Outcome of tagging an env mapping."""

    # key -> frozenset of tags
    tagged: Dict[str, FrozenSet[str]] = field(default_factory=dict)

    def tags_for(self, key: str) -> FrozenSet[str]:
        """Return the tags assigned to *key* (empty set if none)."""
        return self.tagged.get(key, frozenset())

    def keys_with_tag(self, tag: str) -> List[str]:
        """Return all keys that carry *tag*, sorted alphabetically."""
        return sorted(k for k, tags in self.tagged.items() if tag in tags)

    def all_tags(self) -> FrozenSet[str]:
        """Return the union of every tag used across all keys."""
        result: Set[str] = set()
        for tags in self.tagged.values():
            result.update(tags)
        return frozenset(result)

    def untagged_keys(self, env: Mapping[str, str]) -> List[str]:
        """Return keys present in *env* that received no tag, sorted alphabetically."""
        return sorted(k for k in env if k not in self.tagged)

    def summary(self) -> str:
        """Human-readable one-liner."""
        n_keys = len(self.tagged)
        n_tags = len(self.all_tags())
        return f"{n_keys} key(s) tagged across {n_tags} distinct tag(s)"


def tag_env(
    env: Mapping[str, str],
    rules: Mapping[str, List[str]],
) -> TagResult:
    """Tag every key in *env* according to *rules*.

    *rules* maps a tag name to a list of key prefixes (or exact names).
    A key receives a tag when it starts with any of the prefixes for that tag.

    Example::

        rules = {
            "database": ["DB_", "DATABASE_"],
            "auth": ["AUTH_", "JWT_", "SECRET"],
        }
    """
    tagged: Dict[str, FrozenSet[str]] = {}
    for key in env:
        key_tags: Set[str] = set()
        for tag, prefixes in rules.items():
            for prefix in prefixes:
                if key.startswith(prefix) or key == prefix.rstrip("_"):
                    key_tags.add(tag)
                    break
        if key_tags:
            tagged[key] = frozenset(key_tags)
    return TagResult(tagged=tagged)
