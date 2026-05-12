"""grapher.py – Build a dependency graph of .env key references.

For each key whose value contains ${OTHER_KEY} or $OTHER_KEY references,
record a directed edge  key -> referenced_key.  The result lets callers
detect cycles, find roots, and understand propagation order.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Set

_REF_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


def _refs_in(value: str) -> FrozenSet[str]:
    """Return every key name referenced inside *value*."""
    return frozenset(
        m.group(1) or m.group(2) for m in _REF_RE.finditer(value)
    )


@dataclass
class GraphResult:
    """Dependency graph derived from a parsed .env mapping."""

    # key -> set of keys it depends on
    edges: Dict[str, FrozenSet[str]] = field(default_factory=dict)

    # keys that appear in values but are not defined in the env
    undefined_refs: FrozenSet[str] = frozenset()

    def roots(self) -> List[str]:
        """Keys with no outgoing edges (no dependencies)."""
        return sorted(k for k, deps in self.edges.items() if not deps)

    def dependents_of(self, key: str) -> List[str]:
        """All keys that directly reference *key*."""
        return sorted(k for k, deps in self.edges.items() if key in deps)

    def has_cycles(self) -> bool:
        """Return True if the graph contains at least one cycle."""
        visited: Set[str] = set()
        path: Set[str] = set()

        def _dfs(node: str) -> bool:
            if node in path:
                return True
            if node in visited:
                return False
            visited.add(node)
            path.add(node)
            for dep in self.edges.get(node, frozenset()):
                if _dfs(dep):
                    return True
            path.discard(node)
            return False

        return any(_dfs(k) for k in self.edges)

    def summary(self) -> str:
        total = len(self.edges)
        with_deps = sum(1 for d in self.edges.values() if d)
        undef = len(self.undefined_refs)
        cycle_flag = " [CYCLE DETECTED]" if self.has_cycles() else ""
        return (
            f"{total} keys, {with_deps} with references, "
            f"{undef} undefined ref(s){cycle_flag}"
        )


def build_graph(env: Dict[str, str]) -> GraphResult:
    """Build a :class:`GraphResult` from a parsed env mapping."""
    edges: Dict[str, FrozenSet[str]] = {}
    all_undefined: Set[str] = set()

    for key, value in env.items():
        deps = _refs_in(value)
        edges[key] = deps

    defined = set(env.keys())
    for deps in edges.values():
        all_undefined.update(deps - defined)

    return GraphResult(edges=edges, undefined_refs=frozenset(all_undefined))
