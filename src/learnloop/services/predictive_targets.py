"""P4 step 3b -- goal-conditioned predictive targets (spec §6.6, design §B step 3b).

Predictive EIG must evaluate the PINNED goal-contract target distribution, never an
ID-ordered slice of currently eligible probes (invariant 6). This module builds a
frozen target set from a ``goal_contracts`` contract body -- exemplar/blueprint
distribution + weights, required capabilities / task-feature cells, held-out target
eligibility, and unseen-surface constraints -- and REPLACES ``probe_episodes.py``'s
``resolved.sort(key=lambda entry: entry[0].id)[: predictive_target_cap + 1]`` pool.

Two acceptance invariants (spec §16.3):

- construction is invariant to candidate/ID insertion order (everything is sorted;
  the target-set hash changes only with the pinned contract's support, not with the
  order candidates were enumerated in);
- the candidate under consideration is excluded from its own target set (a candidate
  can never predict itself as a held-out target).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from learnloop.services.activities import _canonical_hash

# Structural schema version of the target-set body (enum, not a decision knob).
TARGET_SET_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class TargetExemplar:
    id: str | None
    surface_ref: str | None
    weight: float

    def key(self) -> tuple[str, str]:
        return (str(self.id or ""), str(self.surface_ref or ""))

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "surface_ref": self.surface_ref, "weight": round(float(self.weight), 6)}


@dataclass(frozen=True)
class TargetSet:
    """A frozen goal-conditioned predictive target set (§6.6)."""

    contract_version_id: str | None
    support_hash: str | None
    exemplars: tuple[TargetExemplar, ...]
    required_capabilities: tuple[str, ...]
    task_types: tuple[str, ...]
    held_out: bool
    excluded_candidate: str | None
    coverage_gaps: tuple[str, ...]
    target_set_hash: str

    def weight_of(self, exemplar_id: str) -> float:
        for ex in self.exemplars:
            if ex.id == exemplar_id or ex.surface_ref == exemplar_id:
                return ex.weight
        return 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": TARGET_SET_SCHEMA_VERSION,
            "contract_version_id": self.contract_version_id,
            "support_hash": self.support_hash,
            "exemplars": [ex.as_dict() for ex in self.exemplars],
            "required_capabilities": list(self.required_capabilities),
            "task_types": list(self.task_types),
            "held_out": self.held_out,
            "excluded_candidate": self.excluded_candidate,
            "coverage_gaps": list(self.coverage_gaps),
            "target_set_hash": self.target_set_hash,
        }


def _matches_candidate(ex: TargetExemplar, candidate_id: str | None) -> bool:
    if candidate_id is None:
        return False
    return ex.id == candidate_id or ex.surface_ref == candidate_id


def build_target_set(
    contract_body: Mapping[str, Any],
    *,
    contract_version_id: str | None = None,
    support_hash: str | None = None,
    candidate_id: str | None = None,
    available_capabilities: Sequence[str] | None = None,
) -> TargetSet:
    """Build the frozen predictive target set from a pinned contract body (§6.6).

    ``contract_body`` is the canonical ``goal_contracts`` contract dict (its
    ``exemplars`` / ``required_capabilities`` / ``task_types`` / ``eligibility``
    fields). The candidate under consideration (``candidate_id``) is excluded from its
    own target set. Construction is order-invariant: exemplars/capabilities/task-types
    are sorted before hashing, so shuffling the input yields the identical hash."""

    raw_exemplars = list(contract_body.get("exemplars") or [])
    exemplars = tuple(
        sorted(
            (
                TargetExemplar(
                    id=ex.get("id"),
                    surface_ref=ex.get("surface_ref"),
                    weight=float(ex.get("weight", 1.0)),
                )
                for ex in raw_exemplars
            ),
            key=lambda e: e.key(),
        )
    )
    # Exclude the candidate from its own target set (§6.6, candidate-can't-predict-self).
    exemplars = tuple(e for e in exemplars if not _matches_candidate(e, candidate_id))

    required_capabilities = tuple(sorted(str(c) for c in (contract_body.get("required_capabilities") or [])))
    task_types = tuple(sorted(str(t) for t in (contract_body.get("task_types") or [])))
    eligibility = contract_body.get("eligibility") or {}
    held_out = bool(eligibility.get("held_out", True))

    coverage_gaps: tuple[str, ...] = ()
    if available_capabilities is not None:
        have = {str(c) for c in available_capabilities}
        coverage_gaps = tuple(c for c in required_capabilities if c not in have)

    body = {
        "schema_version": TARGET_SET_SCHEMA_VERSION,
        "contract_version_id": contract_version_id,
        "support_hash": support_hash,
        "exemplars": [e.as_dict() for e in exemplars],
        "required_capabilities": list(required_capabilities),
        "task_types": list(task_types),
        "held_out": held_out,
        "excluded_candidate": candidate_id,
    }
    return TargetSet(
        contract_version_id=contract_version_id,
        support_hash=support_hash,
        exemplars=exemplars,
        required_capabilities=required_capabilities,
        task_types=task_types,
        held_out=held_out,
        excluded_candidate=candidate_id,
        coverage_gaps=coverage_gaps,
        target_set_hash=_canonical_hash(body),
    )


def build_from_contract_version(
    contract_version: Any,
    *,
    candidate_id: str | None = None,
    available_capabilities: Sequence[str] | None = None,
) -> TargetSet:
    """Convenience over a ``goal_contracts.ContractVersion`` (pins version id + support
    hash automatically). The contract body is the version's canonical ``contract``."""

    return build_target_set(
        contract_version.contract,
        contract_version_id=getattr(contract_version, "id", None),
        support_hash=getattr(contract_version, "support_hash", None),
        candidate_id=candidate_id,
        available_capabilities=available_capabilities,
    )
