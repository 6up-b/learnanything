"""Reads of a commitment's pinned depth policy and depth envelope versions."""

from __future__ import annotations

import json
from typing import Any

from learnloop.db.repositories import Repository


def depth_policy(repository: Repository, policy_version_id: str | None) -> str | None:
    """The policy name (for example ``auto_within_envelope``) of a depth-policy version."""

    if not policy_version_id:
        return None
    row = repository.depth_policy_version(policy_version_id)
    return row["policy"] if row is not None else None


def envelope_edges(repository: Repository, envelope_version_id: str | None) -> list[dict[str, Any]]:
    """Every edge recorded on a depth-envelope version, whether or not it was reviewed.

    Each edge carries its own ``reviewed`` flag; callers that may only act on
    reviewed edges filter on it.
    """

    if not envelope_version_id:
        return []
    row = repository.depth_envelope_version(envelope_version_id)
    if row is None:
        return []
    return json.loads(row["reviewed_edges_json"] or "[]")
