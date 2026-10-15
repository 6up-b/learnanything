"""The seal binding a source-set member's scope to the reading it names
(exam protection by extraction identity, docs/reviews/exam-protection-identity.md).

A member's scope lists unit ids, and unit ids are positional: they mean
something only on the reading they were chosen on
(``SourceSetMember.scope_extraction_id``). The vault writer seals that binding
when it writes the member; ``content.sources.exam_material`` treats a scope
whose seal no longer matches (its units or its reading edited outside the
writer) as naming no reading. Standard library only, so the exam predicate
(a leaf) can read it.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def scope_seal(member: Any) -> str | None:
    """A hash of the book, ``scope_extraction_id``, ``scope_revision_id`` and
    every scope entry's unit id and role override, in order (the pinned
    revision is left out: a refresh may advance it). None when the member
    names no reading or has no scope. ``member`` is a ``SourceSetMember`` or
    its YAML mapping."""

    def get(key: str) -> Any:
        return member.get(key) if isinstance(member, dict) else getattr(member, key, None)

    entries = get("scope") or []
    if not get("scope_extraction_id") or not entries:
        return None
    rows = []
    for entry in entries:
        unit_id = entry.get("unit_id") if isinstance(entry, dict) else getattr(entry, "unit_id", None)
        role = entry.get("role_override") if isinstance(entry, dict) else getattr(entry, "role_override", None)
        rows.append([str(unit_id or ""), role or None])
    payload = [str(get("source_id") or ""), str(get("scope_extraction_id")), get("scope_revision_id") or None, rows]
    return "sha256:" + hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()[:32]


__all__ = ["scope_seal"]
