"""Classify .env keys by inferred purpose/category based on naming patterns."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# (label, compiled pattern)
_RULES: List[tuple[str, re.Pattern[str]]] = [
    ("database",  re.compile(r"(DB|DATABASE|POSTGRES|MYSQL|MONGO|REDIS|SQLITE)", re.I)),
    ("auth",      re.compile(r"(SECRET|TOKEN|JWT|OAUTH|AUTH|PASSWORD|PASSWD|API_KEY)", re.I)),
    ("network",   re.compile(r"(HOST|PORT|URL|URI|ENDPOINT|ADDR|ADDRESS|DOMAIN)", re.I)),
    ("storage",   re.compile(r"(BUCKET|S3|BLOB|STORAGE|DISK|PATH|DIR|FOLDER)", re.I)),
    ("email",     re.compile(r"(SMTP|MAIL|EMAIL|SENDGRID|MAILGUN)", re.I)),
    ("logging",   re.compile(r"(LOG|LOGGING|SENTRY|ROLLBAR|BUGSNAG|DATADOG)", re.I)),
    ("feature",   re.compile(r"(FEATURE|FLAG|ENABLE|DISABLE|TOGGLE)", re.I)),
    ("environment", re.compile(r"^(ENV|ENVIRONMENT|APP_ENV|NODE_ENV|RAILS_ENV|DJANGO_ENV)$", re.I)),
]

UNCLASSIFIED = "unclassified"


def classify_key(key: str) -> str:
    """Return the first matching category label for *key*, or 'unclassified'."""
    for label, pattern in _RULES:
        if pattern.search(key):
            return label
    return UNCLASSIFIED


@dataclass
class ClassifyResult:
    """Holds per-category groupings for a set of env keys."""
    categories: Dict[str, List[str]] = field(default_factory=dict)

    # ------------------------------------------------------------------ #
    def all_categories(self) -> List[str]:
        """Sorted list of category names that have at least one key."""
        return sorted(self.categories.keys())

    def keys_for(self, category: str) -> List[str]:
        """Sorted list of keys belonging to *category*."""
        return sorted(self.categories.get(category, []))

    def category_for(self, key: str) -> Optional[str]:
        """Reverse-lookup: return the category that contains *key*, or None."""
        for cat, keys in self.categories.items():
            if key in keys:
                return cat
        return None

    def summary(self) -> str:
        lines: List[str] = []
        for cat in self.all_categories():
            keys = self.keys_for(cat)
            lines.append(f"{cat}: {len(keys)} key(s)")
        return "\n".join(lines) if lines else "no keys classified"


def classify_env(env: Dict[str, str]) -> ClassifyResult:
    """Classify every key in *env* and return a :class:`ClassifyResult`."""
    buckets: Dict[str, List[str]] = {}
    for key in env:
        label = classify_key(key)
        buckets.setdefault(label, []).append(key)
    return ClassifyResult(categories=buckets)
