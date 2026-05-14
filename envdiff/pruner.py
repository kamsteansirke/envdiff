"""Pruner: identify keys that are present in a .env file but absent from a reference schema or key list."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


@dataclass
class PruneIssue:
    key: str
    value: str
    reason: str = "not in reference"

    def __str__(self) -> str:
        return f"{self.key}: {self.reason}"


@dataclass
class PruneResult:
    source: str
    issues: List[PruneIssue] = field(default_factory=list)
    kept: List[str] = field(default_factory=list)

    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def summary(self) -> str:
        if self.is_clean():
            return f"{self.source}: all {len(self.kept)} key(s) are in the reference set"
        return (
            f"{self.source}: {len(self.issues)} obsolete key(s) found "
            f"({len(self.kept)} kept)"
        )

    def obsolete_keys(self) -> List[str]:
        return [i.key for i in self.issues]

    def pruned_env(self) -> Dict[str, str]:
        """Return a copy of the env with obsolete keys removed."""
        obsolete = set(self.obsolete_keys())
        return {k: v for k, v in self._original.items() if k not in obsolete}

    # internal: set by prune_env
    _original: Dict[str, str] = field(default_factory=dict, repr=False)


def prune_env(
    env: Dict[str, str],
    reference: Iterable[str],
    source: str = "<env>",
    extra_reason: Optional[str] = None,
) -> PruneResult:
    """Compare *env* against *reference* keys and flag any key not present.

    Args:
        env: Parsed environment mapping.
        reference: Iterable of allowed / expected key names.
        source: Label used in the result summary.
        extra_reason: Optional custom reason string for flagged keys.

    Returns:
        A :class:`PruneResult` describing obsolete and kept keys.
    """
    ref_set = set(reference)
    reason = extra_reason or "not in reference"
    issues: List[PruneIssue] = []
    kept: List[str] = []

    for key, value in env.items():
        if key in ref_set:
            kept.append(key)
        else:
            issues.append(PruneIssue(key=key, value=value, reason=reason))

    result = PruneResult(source=source, issues=issues, kept=sorted(kept))
    result._original = dict(env)
    return result
