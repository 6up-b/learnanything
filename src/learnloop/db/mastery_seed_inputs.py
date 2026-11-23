"""The claims a learning object's mastery was first seeded from (mvp-0.67; migration 265, ``mastery_seed_inputs``).

A learning object's mastery row is created once, from the learner claims then in force, and a claim that does not
re-anchor (a changed starting level, a manual claim) never re-seeds it afterwards. Replay cannot tell from the claims
on record which of them existed when the row was first persisted, so from the tag the writer that persists it records
every claim it considered, and replay seeds from the record. Stdlib only: the store writes and reads the rows, the
learner model decides what the seed is.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

MASTERY_SEED_TABLE = "mastery_seed_inputs"
#: Written by the writer that first persisted the learning object's mastery, in that write's transaction.
BASIS_CAPTURED = "captured_at_materialization"
#: Written once by the upgrade to the tag for a learning object with no row: the claims the predecessor's own rebuild
#: seeds it from (its first attempt's, or now's when it has none). A reconstruction, never observed history.
BASIS_LEGACY_RECONSTRUCTED = "legacy_reconstructed"
#: How the seed reads the claims: the most specific in-force claim's level (recency, then pseudo-count), the variance
#: bounded by every earlier re-anchoring claim's seed, under the vault's mastery settings at the time of reading.
SEED_POLICY = "covering_claims_seed_v1"
#: The fields of a claim the seed reads, kept in each recorded claim (plus whether it was in force).
SEED_CLAIM_FIELDS = (
    "id", "source", "scope_type", "scope_id", "claimed_level", "prior_pseudo_count", "created_at", "superseded_by",
)


@dataclass(frozen=True)
class MasterySeedInputs:
    """Every claim one learning object's first mastery seed considered, the claim that won, and where they came from.

    ``claims`` are the recorded claims (``SEED_CLAIM_FIELDS`` and ``in_force``) in ``(created_at, id)`` order: the
    winner is read among the in-force ones, the variance bound among all of them, so a claim replaced or made later
    never changes what the record seeds."""

    learning_object_id: str
    claims: tuple[Mapping[str, Any], ...]
    selected_claim_id: str | None
    basis: str
    materialized_at: str | None
    policy_version: str = SEED_POLICY

    @classmethod
    def of(
        cls,
        learning_object_id: str,
        considered: Iterable[Mapping[str, Any]],
        in_force_ids: Iterable[str],
        selected_claim_id: str | None,
        *,
        basis: str,
        materialized_at: str | None,
    ) -> MasterySeedInputs:
        in_force = {str(claim_id) for claim_id in in_force_ids}
        claims = [
            {**{field: claim.get(field) for field in SEED_CLAIM_FIELDS}, "in_force": str(claim.get("id")) in in_force}
            for claim in considered
        ]
        claims.sort(key=lambda claim: (str(claim.get("created_at") or ""), str(claim.get("id") or "")))
        return cls(
            str(learning_object_id), tuple(claims), None if selected_claim_id is None else str(selected_claim_id),
            basis, materialized_at,
        )

    @property
    def claim_ids(self) -> frozenset[str]:
        return frozenset(str(claim.get("id")) for claim in self.claims)

    @property
    def in_force_ids(self) -> frozenset[str]:
        return frozenset(str(claim.get("id")) for claim in self.claims if claim.get("in_force"))

    def claims_made_json(self) -> str:
        return json.dumps([dict(claim) for claim in self.claims], sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_row(cls, row) -> MasterySeedInputs:
        return cls(
            str(row["learning_object_id"]),
            tuple(json.loads(row["claims_made_json"])),
            None if row["selected_claim_id"] is None else str(row["selected_claim_id"]),
            str(row["basis"]),
            None if row["materialized_at"] is None else str(row["materialized_at"]),
            str(row["policy_version"]),
        )


__all__ = [
    "BASIS_CAPTURED",
    "BASIS_LEGACY_RECONSTRUCTED",
    "MASTERY_SEED_TABLE",
    "MasterySeedInputs",
    "SEED_CLAIM_FIELDS",
    "SEED_POLICY",
]
