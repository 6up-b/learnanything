"""The recurrence-key seam (Slice 1 §7.6), dependency-neutral.

Every site that asks "is this the same hypothesis as that one?" groups by
``recurrence_key(hypothesis, groups)``. Without ``groups`` it is exactly the
exact-statement key the sites used before (``statement_normalized``).

Slice 2 T1 (M3) supplies ``groups``: the vault's recurrence-group map
(``Repository.recurrence_group_map()``), which maps every normalized
statement whose class was MERGED with another class to its group key. A
statement class that was never merged is absent from the map and keeps its
old key, so a vault with no merges groups (and rebuilds) exactly as before.
The map is empty unless the T1 successor is active and its kill switch is on.

Groups are unions of statement classes: two hypotheses with the same
normalized statement are always in one group (the exact key is the base), and
classes are joined only by a validated diagnoser citation or a ``same_cause``
verdict (``learnloop.substrate.recurrence_groups``). Embedding scores never
join anything.

It lives below the domains (like ``algorithm_versions``) because the
repository's candidate projection is one of its callers.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping

#: Identity of the exact-statement grouping rule (Slice 1).
RECURRENCE_KEY_VERSION = "statement-normalized-v1"
#: Identity of the T1 grouping rule (exact classes joined by validated
#: citations and ``same_cause`` verdicts, with the no-chaining refusal).
GROUP_RECURRENCE_KEY_VERSION = "recurrence-groups-v1"
#: Merged groups' keys carry this prefix; a normalized statement never does
#: (normalization turns ``:`` into a space).
GROUP_KEY_PREFIX = "rg:"

_NORMALIZE_RE = re.compile(r"\W+")


def normalize_statement(value: str | None) -> str:
    """The ``statement_normalized`` of a causal hypothesis.

    The same rule causal materialization applies when it mints a hypothesis
    (``diagnosis.causal_attribution._normalized``), so a cause statement read
    back from a diagnosis resolves to the class its hypothesis was minted in.
    """

    return _NORMALIZE_RE.sub(" ", str(value or "").casefold()).strip()


def group_key_for(root_statement: str) -> str:
    """The key of a merged group, from its root class's normalized statement."""

    digest = hashlib.sha256(str(root_statement).encode("utf-8")).hexdigest()[:20]
    return f"{GROUP_KEY_PREFIX}{digest}"


def is_group_key(value: str | None) -> bool:
    return bool(value) and str(value).startswith(GROUP_KEY_PREFIX)


def key_for_statement(statement_normalized: str | None, groups: Mapping[str, str] | None = None) -> str:
    """The recurrence key of one normalized statement (or of a key itself).

    Idempotent: a group key maps to itself, so callers may pass either a raw
    normalized statement or a key they already hold.
    """

    value = "" if statement_normalized is None else str(statement_normalized)
    if groups:
        return str(groups.get(value, value))
    return value


def recurrence_key(hypothesis: Mapping[str, Any], groups: Mapping[str, str] | None = None) -> str:
    """The group a hypothesis (or projected candidate) recurs under."""

    return key_for_statement(hypothesis.get("statement_normalized"), groups)


__all__ = [
    "GROUP_KEY_PREFIX",
    "GROUP_RECURRENCE_KEY_VERSION",
    "RECURRENCE_KEY_VERSION",
    "group_key_for",
    "is_group_key",
    "key_for_statement",
    "normalize_statement",
    "recurrence_key",
]
