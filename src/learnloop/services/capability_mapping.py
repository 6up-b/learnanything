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


def _observed_capability(item: PracticeItem, tier: str) -> str:
    """Capability a criterion of ``tier`` observes on ``item``.

    A ``transfer``-tier criterion deliberately probes past the item's own
    waypoint (§5.1), so it keeps the tier default; every other criterion follows
    the item's authored capability when it names one in the closed vocabulary.
    """

    if tier != "transfer":
        declared = getattr(item, "capability", None)
        if declared and is_valid_capability(str(declared)):
            return str(declared)
    return default_capability_for(item.practice_mode, tier=tier)


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
    set) becomes a ``primary`` target at the item's declared capability, falling
    back to the mode/tier default.

    The item's own ``capability`` outranks the practice-mode default because it
    is the depth-rung annotation the item was authored AT, while the mode default
    is a coarse guess from a free-text mode string. Ignoring it filed every
    rung-targeted ``constructed_response`` item's evidence under
    ``procedure_execution`` regardless of the capability it actually probed, so
    blueprint components declared at other capabilities stayed ``unexamined`` no
    matter how much practice landed on them.
    """

    if criterion.targets:
        return list(criterion.targets)

    measurement_status = getattr(criterion, "measurement_status", None)
    if measurement_status in {"item_local", "no_canonical_facet"}:
        return []
    tier = getattr(criterion, "tier", "core")
    capability = _observed_capability(item, tier)
    mapped = item.criterion_facet_weights.get(criterion.id)
    # Once an author explicitly declares measurement status, an empty mapping
    # is an honest abstention. The whole-item fallback remains only for legacy
    # criteria whose measurement status predates P0b.
    facets = list(mapped) if mapped else ([] if measurement_status is not None else list(item.evidence_facets))
    role = "supporting" if measurement_status == "supporting" else "primary"
    return [
        CriterionTarget(facet=facet, capability=capability, role=role)
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


# -- First-error localization (§5.3), generalized from longform_trace ----------

# Assistance channels that earn zero certification credit (§5.4/§6): a facet is
# not *demonstrated* when the answer was hinted, scaffolded, or exposed.
UNASSISTED = "unassisted"
ASSISTED_CHANNELS: frozenset[str] = frozenset({"hinted", "scaffolded", "answer_exposed"})


@dataclass(frozen=True)
class CriterionOutcome:
    """One graded criterion within an attempt (projection input)."""

    criterion_id: str
    passed: bool
    depends_on: tuple[str, ...] = ()


@dataclass(frozen=True)
class LocalizedCriterion:
    criterion_id: str
    assessable: bool          # False => descendant of a failed criterion (share 0)
    passed: bool
    first_error: bool         # earliest failed criterion on its branch


def localize_criterion_outcomes(outcomes: list[CriterionOutcome]) -> list[LocalizedCriterion]:
    """First-error localization over a criterion dependency DAG (§5.3).

    - A criterion is *unassessable* (evidence share 0) when any criterion it
      transitively depends on failed — its valid evaluation depended on that
      failed step. Independent branches stay assessable.
    - An assessable failed criterion whose dependencies all passed is a
      *first error* carrying localized failure attribution.
    - Correct assessable criteria yield normal positive evidence, prefix or not.
    - Whole-item failure therefore never penalizes every listed facet.
    """

    passed_by_id = {o.criterion_id: o.passed for o in outcomes}
    depends = {o.criterion_id: tuple(o.depends_on) for o in outcomes}

    # Memoized: does this criterion have a failed transitive ancestor?
    cache: dict[str, bool] = {}

    def has_failed_ancestor(cid: str, stack: frozenset[str]) -> bool:
        if cid in cache:
            return cache[cid]
        if cid in stack:  # defensive against an authored cycle
            return False
        result = False
        for dep in depends.get(cid, ()):  # a dep that failed, or whose ancestor failed
            if passed_by_id.get(dep, True) is False or has_failed_ancestor(dep, stack | {cid}):
                result = True
                break
        cache[cid] = result
        return result

    localized: list[LocalizedCriterion] = []
    for outcome in outcomes:
        blocked = has_failed_ancestor(outcome.criterion_id, frozenset())
        assessable = not blocked
        first_error = assessable and not outcome.passed
        localized.append(
            LocalizedCriterion(
                criterion_id=outcome.criterion_id,
                assessable=assessable,
                passed=outcome.passed,
                first_error=first_error,
            )
        )
    return localized


# -- Bounded certification credit (§5.4, the four quantities) -------------------


def certification_credit(
    pseudo_mass: float,
    *,
    relationship: str,
    assistance: str,
) -> float:
    """Credit for one observation = its pseudo-mass iff direct/embedded and
    unassisted; zero otherwise (§5.4 quantity 2).

    Capability-matching is structural: credit accrues only to the ledger cell of
    the *observed* capability, so retrieval evidence can never reach the
    (facet, method_selection) cell. Assistance and projection/prior signals earn
    zero.
    """

    if relationship not in ("direct", "embedded"):
        return 0.0
    if assistance in ASSISTED_CHANNELS:
        return 0.0
    return max(0.0, pseudo_mass)


def group_budget(
    attempt_type: str,
    correlation_group: str | None,
    *,
    evidence_mass: float,
    overrides: Mapping[str, float] | None = None,
) -> float:
    """Per-(attempt_type, correlation-group) certification budget (§5.4 q.3).

    Defaults to ``evidence_mass(attempt_type)``; ``[evidence.certification].group_budgets``
    overrides by ``"attempt_type:group"`` or bare ``"group"``.
    """

    overrides = overrides or {}
    if correlation_group is not None:
        keyed = f"{attempt_type}:{correlation_group}"
        if keyed in overrides:
            return float(overrides[keyed])
        if correlation_group in overrides:
            return float(overrides[correlation_group])
    return evidence_mass


def cap_certification_by_group(
    credits_by_group: Mapping[str, float],
    *,
    attempt_type: str,
    evidence_mass: float,
    overrides: Mapping[str, float] | None = None,
    max_groups_per_attempt: int,
) -> dict[str, float]:
    """Apply the per-group cap and the attempt-wide ceiling (§5.4 q.3/q.4).

    Each correlation group's summed credit is capped at its ``group_budget``;
    the total across groups is then capped at
    ``evidence_mass * max_groups_per_attempt``. A rich constructed response can
    out-earn a binary item (several independent groups) but never without bound.
    """

    capped: dict[str, float] = {}
    for group, credit in credits_by_group.items():
        budget = group_budget(
            attempt_type, group, evidence_mass=evidence_mass, overrides=overrides
        )
        capped[group] = min(credit, budget)
    ceiling = evidence_mass * max_groups_per_attempt
    total = sum(capped.values())
    if total > ceiling and total > 0:
        scale = ceiling / total
        capped = {group: credit * scale for group, credit in capped.items()}
    return capped


def group_proliferation_flag(
    group_variation_counts: Mapping[str, int],
    *,
    min_independent_variations: int = 2,
) -> list[str]:
    """Correlation groups whose observations never vary independently (§5.4).

    ``group_variation_counts`` maps a correlation group to how many distinct
    outcome patterns its observations have shown across attempts. A group that
    always co-varies (count < ``min_independent_variations``) is flagged for the
    identifiability doctor / synthesis gate as suspicious group proliferation.
    """

    return sorted(
        group
        for group, count in group_variation_counts.items()
        if count < min_independent_variations
    )


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
