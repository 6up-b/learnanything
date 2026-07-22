"""P4 step 1 -- the versioned feasible-set constraint engine (spec §5, design B step 1).

Constraints define the FEASIBLE SET; scores rank only WITHIN it (invariant 1, the
U-023 hierarchy level 1). This engine's output for every candidate is ``eligible`` or
a typed list of exclusion reasons -- fully inspectable. A high estimated gain can
never compensate for a violation: the staged policy consumes ``feasible_set`` and can
only ever select a ``feasible=True`` candidate (see the adversarial acceptance test).

Constraint DEFINITIONS are versioned and content-hashed: :func:`manifest` freezes the
active set (key + version + bound parameter paths) and hashes it, and every decision
records the manifest hash it evaluated under. A constraint bound to a *dormant*
guardrail parameter logs a bind event when it actually fires (U-022, §4/§6 of the
parameter-registry spec) -- an unmonitored guardrail is dead code.

Every constraint reads ONLY from the :class:`~learnloop.services.controller_snapshot`
material (bulk/bounded reads, §3.1) plus the chosen attention block -- never the DB
per candidate. Composition of existing authorities is read-only: exposure/hard
collision from the ``activity_exposure_events`` ledger (§3.6, invariant 11), purpose/
administration-context, assessment reservation, and burden/fatigue bounds. Depth-edge
constraints are evaluated structurally in :mod:`staged_policy` via ``depth_transition``
(the U-018 gate), which is the "structurally before ranking" authority of §5.

Same-facet dispersion and stage-aware interleaving are deliberately NOT implemented
here -- they are P4 step 4 (``services/dispersion.py`` / ``services/interleaving.py``),
a separate module boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services import parameter_registry as pr
from learnloop.services.activities import _canonical_hash

if TYPE_CHECKING:  # avoid an import cycle: the snapshot imports nothing from here
    from learnloop.services.controller_snapshot import Candidate, ControllerSnapshot
    from learnloop.services.staged_policy import AttentionBlock

# Structural version of the constraint manifest schema (enum, not a decision knob).
CONSTRAINT_MANIFEST_VERSION = 1

# A dormant guardrail: minutes of slack the fatigue/budget constraint tolerates before
# it excludes an over-budget candidate. Frozen at 0 (strict) at launch; only fires
# under budget pressure, so it is bind-logged rather than swept (U-022).
FATIGUE_BUDGET_SLACK_MINUTES = 0.0


@dataclass(frozen=True)
class ExclusionReason:
    """One typed reason a candidate is infeasible or deferred (§5)."""

    constraint_key: str
    constraint_version: int
    reason: str
    detail: dict[str, Any] = field(default_factory=dict)
    kind: str = "exclude"  # "exclude" | "defer"

    def as_dict(self) -> dict[str, Any]:
        return {
            "constraint_key": self.constraint_key,
            "constraint_version": self.constraint_version,
            "reason": self.reason,
            "detail": self.detail,
            "kind": self.kind,
        }


@dataclass(frozen=True)
class Feasibility:
    """The engine output for one candidate: eligible, or a list of exclusions."""

    candidate_ref: str
    exclusions: tuple[ExclusionReason, ...] = ()

    @property
    def eligible(self) -> bool:
        return not self.exclusions

    def as_dict(self) -> dict[str, Any]:
        return {
            "candidate_ref": self.candidate_ref,
            "eligible": self.eligible,
            "exclusions": [e.as_dict() for e in self.exclusions],
        }


@dataclass(frozen=True)
class Constraint:
    """A versioned constraint definition. ``check`` returns an ``ExclusionReason`` when
    the candidate is infeasible/deferred under this constraint, else ``None``. ``check``
    may read only the candidate, the snapshot, and the block."""

    key: str
    version: int
    param_paths: tuple[str, ...]
    check: Callable[["Candidate", "ControllerSnapshot", "AttentionBlock | None"], ExclusionReason | None]
    dormant_bind_paths: tuple[str, ...] = ()  # dormant guardrail params to bind-log on fire

    def definition(self) -> dict[str, Any]:
        return {"key": self.key, "version": self.version, "params": list(self.param_paths)}


# ---------------------------------------------------------------------------
# Launch constraints (§5). Each reads only snapshot + block material.
# ---------------------------------------------------------------------------

_FRESH_EVIDENCE_ACTIONS = frozenset({"measure_diagnostic", "assess_terminal"})


def _requires_unseen(block: "AttentionBlock | None") -> bool:
    """Fresh-evidence blocks (diagnosis, terminal assessment) require an unseen
    surface; instruction/practice/maintenance do not (§5, §3.6)."""

    return bool(block is not None and block.action in _FRESH_EVIDENCE_ACTIONS)


def _c_active(candidate, snapshot, block):
    if not candidate.active:
        return ExclusionReason("active_status", 1, "card_inactive")
    if candidate.quarantined:
        return ExclusionReason("active_status", 1, "card_quarantined")
    return None


def _c_purpose(candidate, snapshot, block):
    if block is None:
        return None
    compatible = block.compatible_purposes
    if compatible and candidate.purpose not in compatible:
        return ExclusionReason(
            "purpose_compatibility", 1, "purpose_incompatible_with_block",
            {"candidate_purpose": candidate.purpose, "block_action": block.action},
        )
    return None


def _c_hard_exposure(candidate, snapshot, block):
    """Global exact/hard exposure collision (invariant 11): P1's deterministic
    authority. A high score can never make a hard collision fresh."""

    if not _requires_unseen(block):
        return None
    sh = candidate.surface_hash
    if sh is None:
        # Unknown freshness blocks an unseen claim but not ordinary instruction (§5).
        return ExclusionReason(
            "hard_exposure_collision", 1, "freshness_unknown",
            {"note": "no surface hash; cannot certify unseen for a fresh-evidence block"},
        )
    exact = snapshot.exposure_by_hash.get(sh, ())
    if exact:
        return ExclusionReason(
            "hard_exposure_collision", 1, "exact_surface_collision",
            {"surface_hash": sh, "exposures": len(exact)},
        )
    fp = candidate.fingerprint
    near = snapshot.exposure_by_fingerprint.get(fp, ()) if fp else ()
    if near:
        return ExclusionReason(
            "hard_exposure_collision", 1, "near_clone_collision",
            {"fingerprint": fp, "exposures": len(near)},
        )
    return None


def _c_assessment_reservation(candidate, snapshot, block):
    """A surface holding a live assessment reservation may only be served for
    assessment (P0 leakage/burn rules, §5)."""

    if candidate.surface_id is None:
        return None
    if candidate.surface_id in snapshot.reserved_assessment_surface_ids:
        if block is None or block.action != "assess_terminal":
            return ExclusionReason(
                "assessment_reservation", 1, "reserved_assessment_surface",
                {"surface_id": candidate.surface_id},
            )
    return None


def _c_fatigue_budget(candidate, snapshot, block):
    """Remaining minutes + expected duration bound (§5). Unknown duration fits only
    when its conservative upper bound fits the budget."""

    remaining = snapshot.remaining_minutes
    if remaining is None:
        return None
    slack = FATIGUE_BUDGET_SLACK_MINUTES
    expected = candidate.expected_minutes
    if expected is None:
        expected = snapshot.conservative_duration_minutes
    if expected is not None and expected > remaining + slack:
        return ExclusionReason(
            "fatigue_budget", 1, "over_remaining_minutes",
            {"expected_minutes": expected, "remaining_minutes": remaining, "slack": slack},
        )
    return None


def _c_same_facet_dispersion(candidate, snapshot, block):
    """Same-facet/near-kin dispersion (§9.1): two fresh-evidence administrations on the
    same facet/capability/lineage/hard-group/near-kin cannot be back-to-back. Policy
    logic lives in :mod:`dispersion`; the engine wraps its verdict into a typed reason.
    Feasible-set shaping, never a rank trade (invariant 1).

    RATIONALE / SCOPE (audit F6/L8): in production ``snapshot.last_fresh_evidence`` is
    populated from the exposure ledger, which carries only ``surface_hash``/``fingerprint``
    -- so this constraint disperses on NEAR-KIN SURFACE (fingerprint) in production; the
    finer facet/capability/lineage/hard-group dimensions fire only when that material is
    present on the snapshot (see the facet-join TODO in :mod:`dispersion`). The registered
    constraint is intentionally kept whole; only the input population is deferred."""

    from learnloop.services import dispersion as D

    v = D.same_facet_violation(candidate, snapshot, block)
    if v is None:
        return None
    return ExclusionReason(
        "same_facet_dispersion", D.DISPERSION_POLICY_VERSION, v["reason"], v["detail"],
        kind=v.get("kind", "defer"),
    )


def _c_stage_interleaving(candidate, snapshot, block):
    """Stage-aware interleaving (§9.2): acquisition stays coherent, assessment follows
    the frozen distribution, discrimination/transfer interleave. Policy logic lives in
    :mod:`interleaving`; the engine wraps its verdict. Feasible-set shaping only."""

    from learnloop.services import interleaving as I

    v = I.stage_violation(candidate, snapshot, block)
    if v is None:
        return None
    return ExclusionReason(
        "stage_interleaving", I.INTERLEAVING_POLICY_VERSION, v["reason"], v["detail"],
        kind=v.get("kind", "exclude"),
    )


CONSTRAINTS: tuple[Constraint, ...] = (
    Constraint("active_status", 1, (), _c_active),
    Constraint("purpose_compatibility", 1, (), _c_purpose),
    Constraint("hard_exposure_collision", 1, (), _c_hard_exposure),
    Constraint("assessment_reservation", 1, (), _c_assessment_reservation),
    Constraint(
        "fatigue_budget", 1, (),
        _c_fatigue_budget,
        dormant_bind_paths=("constraint_engine:FATIGUE_BUDGET_SLACK_MINUTES",),
    ),
    Constraint(
        "same_facet_dispersion", 1,
        ("dispersion:DISPERSION_MIN_INTERVENING_ADMINISTRATIONS",),
        _c_same_facet_dispersion,
    ),
    Constraint(
        "stage_interleaving", 1, (), _c_stage_interleaving,
    ),
)


def manifest() -> dict[str, Any]:
    """The frozen, content-hashed manifest of active constraint definitions (§5)."""

    definitions = [c.definition() for c in CONSTRAINTS]
    body = {"schema_version": CONSTRAINT_MANIFEST_VERSION, "constraints": definitions}
    return {"definitions": definitions, "manifest_hash": _canonical_hash(body),
            "schema_version": CONSTRAINT_MANIFEST_VERSION}


def evaluate(
    candidate: "Candidate",
    snapshot: "ControllerSnapshot",
    block: "AttentionBlock | None" = None,
) -> Feasibility:
    """Evaluate every constraint against one candidate. Pure: reads only the
    snapshot + block. Returns the full typed exclusion list (all violations, not the
    first) so the trace is complete (§16.1 exclusion-reason completeness)."""

    exclusions: list[ExclusionReason] = []
    for constraint in CONSTRAINTS:
        reason = constraint.check(candidate, snapshot, block)
        if reason is not None:
            exclusions.append(reason)
    return Feasibility(candidate.candidate_ref, tuple(exclusions))


@dataclass
class FeasibilityReport:
    feasible: list["Candidate"]
    excluded: list[tuple["Candidate", Feasibility]]
    per_candidate: dict[str, Feasibility]
    manifest_hash: str


def feasible_set(
    candidates: Sequence["Candidate"],
    snapshot: "ControllerSnapshot",
    block: "AttentionBlock | None" = None,
    *,
    repository: Repository | None = None,
    clock: Clock | None = None,
) -> FeasibilityReport:
    """Partition candidates into the feasible set + per-candidate exclusion reasons
    (§5). When ``repository`` is supplied, a dormant guardrail constraint that fires
    logs a bind event at its declared bind site (U-022)."""

    feasible: list[Candidate] = []
    excluded: list[tuple[Candidate, Feasibility]] = []
    per_candidate: dict[str, Feasibility] = {}
    fired_dormant: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        feas = evaluate(candidate, snapshot, block)
        per_candidate[candidate.candidate_ref] = feas
        if feas.eligible:
            feasible.append(candidate)
        else:
            excluded.append((candidate, feas))
            fired_keys = {e.constraint_key for e in feas.exclusions}
            for constraint in CONSTRAINTS:
                if constraint.key in fired_keys and constraint.dormant_bind_paths:
                    for path in constraint.dormant_bind_paths:
                        fired_dormant.setdefault(
                            path, {"constraint": constraint.key, "candidate_ref": candidate.candidate_ref},
                        )
    if repository is not None:
        for path, context in fired_dormant.items():
            pr.record_bind(repository, path, context, clock=clock)
    return FeasibilityReport(
        feasible=feasible, excluded=excluded, per_candidate=per_candidate,
        manifest_hash=manifest()["manifest_hash"],
    )
