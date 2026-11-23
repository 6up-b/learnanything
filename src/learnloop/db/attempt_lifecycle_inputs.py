"""The lifecycle inputs an attempt's grade application read (mvp-0.66; migration 263, ``attempt_lifecycle_inputs``).

A grade's relative coverage and its legacy breadth denominator count the facets of its learning object's active items
(``facet_diagnostics.required_facets``). An item's lifecycle changes outside the attempt ledger (retirement, review
parking, a superseded measurement, removal from the vault), so replay cannot tell from today's flags which siblings
an earlier attempt saw. From the tag the live grade application records the set it read, and replay and regrade read
it back. Stdlib only: the store writes and reads the rows, the attempt pipeline decides which set applies.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass

LIFECYCLE_INPUTS_TABLE = "attempt_lifecycle_inputs"
#: Written by the live grade application, in the attempt's own transaction.
BASIS_CAPTURED = "captured_at_application"
#: Written once by the upgrade to the tag for an attempt applied before it: the set the predecessor's replay read at
#: that attempt, from the item lifecycle as it stood at the upgrade. A reconstruction, never observed history.
BASIS_LEGACY_RECONSTRUCTED = "legacy_reconstructed"
#: How the set was read: the evidence facets of the learning object's items whose serving row is active or absent.
REQUIRED_FACETS_POLICY = "active_item_evidence_facets_v1"


@dataclass(frozen=True)
class LifecycleInputs:
    """One attempt's required facet set, in its canonical (sorted) order, and where it came from."""

    learning_object_id: str
    required_facets: tuple[str, ...]
    basis: str
    policy_version: str = REQUIRED_FACETS_POLICY

    @classmethod
    def of(cls, learning_object_id: str, facets: Iterable[str], *, basis: str) -> LifecycleInputs:
        return cls(str(learning_object_id), tuple(sorted({str(facet) for facet in facets})), basis)

    def required_facets_json(self) -> str:
        return json.dumps(list(self.required_facets), separators=(",", ":"))

    @classmethod
    def from_row(cls, row) -> LifecycleInputs:
        return cls(
            str(row["learning_object_id"]),
            tuple(str(facet) for facet in json.loads(row["required_facets_json"])),
            str(row["basis"]),
            str(row["policy_version"]),
        )


__all__ = [
    "BASIS_CAPTURED",
    "BASIS_LEGACY_RECONSTRUCTED",
    "LIFECYCLE_INPUTS_TABLE",
    "LifecycleInputs",
    "REQUIRED_FACETS_POLICY",
]
