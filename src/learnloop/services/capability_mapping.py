"""Mode->capability defaults, criterion-target compilation, and the launch
observation-mass allocation rule (knowledge-model §5.1/§5.4).

This module is deterministic and adds zero provider tokens. It compiles legacy
content (criteria without authored ``targets``) into the new capability-aware
observation contract; authored targets always override the defaults. No belief
state is written here — allocation is a pure compile function whose consumer
(the mvp-0.7 write path) lands with KM2.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from learnloop.vault.models import CAPABILITY_VOCABULARY, CriterionTarget, PracticeItem, Rubric

# Default capability mapping for existing practice modes (§5.1). Used only when
# recreating fixtures / compiling legacy content; authored criterion targets
# always override. Keyed by practice mode; the transfer-tier override handles
# teach_back's transfer criteria (method_selection).
MODE_CAPABILITY_DEFAULTS: dict[str, str] = {
    "retrieval": "retrieval",
    "cloze": "retrieval",
    "recognition": "retrieval",
    "definition": "retrieval",
    "multiple_choice": "retrieval",
    "flashcard": "retrieval",
    "short_answer": "schema_interpretation",
    "explain": "schema_interpretation",
    "explanation": "schema_interpretation",
    "teach_back": "schema_interpretation",
    "constructed_response": "procedure_execution",
    "completion": "procedure_execution",
    "computation": "procedure_execution",
    "derivation": "procedure_execution",
    "proof": "procedure_execution",
    "open_text": "procedure_execution",
    "independent_attempt": "procedure_execution",
    "method_selection": "method_selection",
    "discrimination": "method_selection",
    "diagnostic_probe": "method_selection",
    "diagnostic_microprobe": "method_selection",
}

# Fallback when a practice mode is unrecognized: schema interpretation is the
# conservative middle capability (not retrieval, not coordination).
DEFAULT_CAPABILITY = "schema_interpretation"

# Role weights for splitting success mass across a criterion's targets (§5.4).
ROLE_WEIGHTS: dict[str, float] = {"primary": 1.0, "supporting": 0.3}


def is_valid_capability(capability: str) -> bool:
    return capability in CAPABILITY_VOCABULARY


def default_capability_for(practice_mode: str, *, tier: str = "core") -> str:
    """The default observed capability for a practice mode / rubric tier (§5.1).

    Transfer-tier criteria on any mode default to ``method_selection`` (the
    transfer-tier "which method/theorem applies" discrimination style).
    """

    if tier == "transfer":
        return "method_selection"
    return MODE_CAPABILITY_DEFAULTS.get(practice_mode, DEFAULT_CAPABILITY)


def compile_criterion_targets(
    item: PracticeItem,
    criterion,
    *,
    resolved_rubric: Rubric | None = None,
) -> list[CriterionTarget]:
    """Targets a criterion observes, authored-or-compiled (§5.1).

    Authored ``criterion.targets`` win verbatim. Otherwise legacy content is
    compiled: each evidence facet the criterion is mapped to (via
    ``criterion_facet_weights`` when present, else the item's whole-item facet
    set) becomes a ``primary`` target at the mode/tier default capability.
    """

    if criterion.targets:
        return list(criterion.targets)

    capability = default_capability_for(item.practice_mode, tier=getattr(criterion, "tier", "core"))
    mapped = item.criterion_facet_weights.get(criterion.id)
    facets = list(mapped) if mapped else list(item.evidence_facets)
    return [
        CriterionTarget(facet=facet, capability=capability, role="primary")
        for facet in facets
    ]


@dataclass(frozen=True)
class TargetAllocation:
    facet: str
    capability: str
    role: str
    pseudo_mass: float


def allocate_success_mass(
    targets: list[CriterionTarget],
    criterion_pseudo_mass: float,
) -> list[TargetAllocation]:
    """Split a criterion's success pseudo-mass across its targets by role (§5.4).

    ``primary`` weight 1.0, ``supporting`` 0.3, normalized to sum to 1, then
    scaled by ``criterion_pseudo_mass``. Pure function; writes nothing.
    """

    if not targets:
        return []
    weights = [ROLE_WEIGHTS.get(target.role, 1.0) for target in targets]
    total = sum(weights)
    if total <= 0:
        return []
    return [
        TargetAllocation(
            facet=target.facet,
            capability=target.capability,
            role=target.role,
            pseudo_mass=criterion_pseudo_mass * weight / total,
        )
        for target, weight in zip(targets, weights)
    ]


def criterion_pseudo_mass(criterion_points: float, rubric_total: float, evidence_mass: float) -> float:
    """A criterion's total pseudo-mass = evidence_mass * (points / rubric total)."""

    if rubric_total <= 0:
        return 0.0
    return evidence_mass * (criterion_points / rubric_total)


def unregistered_facet_errors(
    known_facets: Mapping[str, object] | set[str],
    facet_ids,
) -> list[str]:
    """Facet ids in ``facet_ids`` that are not registered (item gate, §3.2).

    Mirrors ``probe_instance_generation.instance_gate_errors``: returns a list of
    human-readable error strings (empty when every facet is registered). The
    caller rejects a newly generated item when this is non-empty.
    """

    known = set(known_facets)
    errors: list[str] = []
    for facet in facet_ids:
        if str(facet) not in known:
            errors.append(f"unregistered evidence facet {str(facet)!r} (not in facets.yaml)")
    return errors
