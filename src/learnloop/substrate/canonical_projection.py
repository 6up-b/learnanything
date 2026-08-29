"""KM2 canonical belief projection (§5.3/§5.4/§6/§7.1).

Recomputes the canonical shared facet belief state (`facet_recall_state`) and
the capability-sliced certification ledger (`facet_capability_evidence`) as a
pure, deterministic projection over the immutable observation ledger. Because
beta masses accumulate additively, the projection is order-independent for the
belief marginals; only timestamps and consecutive-failure runs depend on the
global chronological order the ledger already provides. This makes replay
byte-identical by construction, and sidesteps the shared-facet reset hazard of
incremental per-LO updates (a facet lives under many LOs).

Runs only under mvp-0.7 (`KM_ALGORITHM_VERSION`); the caller guards. The result
is derived state — not a new evidence source — consistent with "evidence, not
mastery": it is a fold over attempts + grading, exactly like every other
`rebuild_derived_state` output.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.learner.assessment_contracts import (
    CANONICAL_STATE_VERSIONS,
    KM_ALGORITHM_VERSION,
    P0_ALGORITHM_VERSION,
    P0_PROJECTION_VERSIONS,
)
from learnloop.diagnosis.causal_activity_policy import (
    ASSISTED_ATTEMPT_TYPES as _ASSISTED_ATTEMPT_TYPES,
    resolve_attempt_activity_policy,
)
from learnloop.diagnosis.causal_attribution import OPEN_SET_CAUSE_ID
from learnloop.learner.capability_mapping import (
    CriterionOutcome,
    allocate_success_mass,
    certification_credit,
    compile_criterion_targets,
    criterion_pseudo_mass,
    localize_criterion_outcomes,
)
from learnloop.content.authoring.conjunctive_items import cap_embedded_credit, supporting_unexercised
from learnloop.attempts.evidence import attempt_evidence_mass
from learnloop.goals.receipt_contributions import itemize_observation_contributions
from learnloop.vault.models import CriterionTarget, LoadedVault, PracticeItem

if TYPE_CHECKING:
    from learnloop.attempts.effective_observation import EffectiveObservationReferences

# Outcome fraction below which a criterion counts as failed (matches the legacy
# recall-coverage failure threshold so mvp-0.7 semantics stay comparable).
FAILURE_THRESHOLD = 0.40

# A repeated observation on an already-seen surface/correlation group is not
# fresh independent evidence (§6): its inference mass is discounted and it adds
# no new independent-surface group. Overridable via [evidence.correlation].
DEFAULT_REPEAT_SURFACE_DISCOUNT = 0.25

# Assistance channels that certify nothing (§5.4/§6).
#
# DEPRECATED as a decision point: the attempt-type set alone cannot see
# ``primed`` or ``hints_used``. Re-exported from the single authority for
# readers that still want the flat set; use
# ``resolve_attempt_activity_policy`` for decisions.
ASSISTED_ATTEMPT_TYPES = _ASSISTED_ATTEMPT_TYPES

# P2 §4.4 canonical projection semantics version. Bumped whenever the fold over
# the observation ledger changes what it derives from unchanged evidence, so a
# rebuild surfaces as ONE deliberate recalibration boundary
# (``derived_state_rebuild_version_changes`` -> learner review feed) instead of
# a silent retro-change.
#
#   v1  (implicit, pre-P2) attempt-type-only assistance test.
#   v2  causal activity policy: ``diagnostic_probe`` and any ``primed`` attempt
#       count as assisted, so historical probe/primed attempts stop minting
#       certification credit and independent surface groups on rebuild.
#   v3  open cause-set UNION: when a diagnosis names exactly one candidate
#       cause, the synthesized facet-target arms are unioned with it instead of
#       REPLACING it. Before v3 the model's own asserted cause was minted as a
#       hypothesis but left out of the factor's arms, so the locked probe set
#       excluded the very cause under test. Rebuilding an affected vault changes
#       the projected cause set (one extra arm per affected factor), which is
#       why it is a versioned boundary rather than a silent correction.
#   v4  compiled criterion targets follow the ITEM's declared capability instead
#       of the practice-mode default (``capability_mapping._observed_capability``).
#       Before v4 every rung-targeted ``constructed_response`` item filed its
#       evidence under ``procedure_execution`` whatever capability it was
#       authored at, so blueprint components declared at other capabilities could
#       never be retired. Rebuilding moves mass between (facet, capability) cells.
# v5 (Meas §3.A1, plan 6.1): supporting targets confer credit only where A6
# trace evidence shows the facet exercised, and each cell's certification credit
# is capped at `max_embedded_credit_share` embedded. Both change stored belief
# with no new learner evidence, so the version bump is what routes it through
# 1.4's "estimates recomputed, your evidence unchanged" recalibration entry
# instead of the numbers silently moving under the learner.
# v6 (stabilization A3): a criterion with NO grading-evidence row produces NO
#     outcome. Before v6 a missing row read as fraction 0.0 -> passed=False, so
#     absent data banked negative mass, advanced consecutive-failure runs, and
#     could open unresolved-cause factors — confident wrongness manufactured
#     from nothing (an ungraded attempt "failed" its whole rubric). A PRESENT
#     row with zero points is unchanged: that is a real observed failure.
#     Rebuilding an affected vault removes phantom negative mass, which is why
#     it is a versioned boundary rather than a silent correction.
# v7 (pipeline audit): ``primed`` is part of the canonical observation ledger.
#     The policy has classified a primed redo as assisted since v2, but the
#     repository projection omitted that column, so every replay supplied the
#     policy's false default and a successful repair-assisted retry could mint
#     certification credit.  Rebuilding removes that ineligible credit without
#     changing the immutable attempt, hence the explicit recalibration boundary.
# v8 (pipeline audit): certification eligibility is distinct from assistance.
#     A pure diagnostic is deliberately displayed as unassisted, but the causal
#     activity policy has always declared it ineligible to certify. Before v8
#     the projection used ``not assisted`` as a proxy for eligibility and could
#     therefore bank diagnostic credit. Recorded near-clone classifications are
#     also consumed in bulk, so a later auditable disqualification survives
#     replay. Rebuilding withdraws only the ineligible certification credit.
CANONICAL_PROJECTION_VERSION = "canonical_projection_v8_activity_eligibility"


def p0_effective_evidence_mass(
    repository: Repository,
    *,
    interpretation: Mapping[str, Any] | None,
    attempt_type_mass: float,
    references: EffectiveObservationReferences | None = None,
) -> float:
    """THE mvp-0.8 response-level evidence-mass discount (P0.3 §4.3), shared by
    both evidence folds.

    The calibrated channel scales evidence authority/mass only — direction is
    owned by the non-superseded ``grading_evidence`` revisions (ruling A,
    2026-07-27): the ledger is the single directional authority, and the
    interpretation channel carries confidence, never direction. A correction
    that changes what happened (regrade, A8 clarification, grade-points
    adjudication) enters as a superseding evidence revision; the interpretation
    chain may only change how much the observation weighs. Direction no longer
    comes from the response posterior, so its aleatoric certainty moves to the
    authority term: combined with ``EffectiveObservation``'s epistemic factor
    this yields the shared certainty LCB as the total response-level mass
    discount. An attempt with no active interpretation (legacy, pre-P0.2)
    contributes zero reliable mass — never a silent full-credit.

    The canonical projection and the facet evidence timeline both call this
    helper so the banked ledger and the learner-facing Demonstrated curve can
    never disagree about the discount (`test_receipt_exactness` holds them to
    float agreement under mvp-0.8 as well as mvp-0.7).
    """

    from learnloop.attempts.effective_observation import build_effective_observation

    effective_obs = build_effective_observation(
        repository,
        interpretation=interpretation,
        # score_fraction shapes only the (unused-here) expected true-score
        # fraction; the mass product below is independent of it.
        score_fraction={},
        attempt_type_mass=attempt_type_mass,
        references=references,
    )
    return effective_obs.effective_mass * effective_obs.certainty


def surface_group_id(item: PracticeItem) -> str:
    """The correlation/surface group an item's evidence belongs to (§6).

    Vault-wide: a shared stimulus/testlet, source-example family, or
    solution-template family collapses near-clones (even under different LOs)
    into one group, so a clone cannot mint a fresh independent surface group.
    Falls back to the legacy surface_family, then the item id.
    """

    fp = item.evidence_fingerprint
    for candidate in (
        fp.shared_stimulus_id,
        fp.source_family,
        fp.solution_recipe_family,
        item.surface_family,
    ):
        if candidate:
            return str(candidate)
    return f"item:{item.id}"


@dataclass
class _RecallAcc:
    alpha: float = 1.0
    beta: float = 1.0
    independent_mass: float = 0.0
    raw_mass: float = 0.0
    last_observed_at: str | None = None
    last_error_at: str | None = None
    consecutive_failures: int = 0
    created_at: str | None = None


@dataclass
class _CapAcc:
    direct_positive_mass: float = 0.0
    direct_negative_mass: float = 0.0
    embedded_positive_mass: float = 0.0
    embedded_negative_mass: float = 0.0
    # Meas §3.A1 guard 2 (migration 141): certification credit is banked split by
    # relationship so the embedded-share cap can be applied per cell at the end.
    # ``certification_credit`` remains the one number Demonstrated reads; it is
    # computed from these two, never accumulated directly.
    direct_certification_credit: float = 0.0
    embedded_certification_credit: float = 0.0
    # Guard 1: mass a supporting target would have earned had the trace shown
    # its facet exercised. "Recorded, not silent."
    unexercised_supporting_mass: float = 0.0
    groups: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class _HistoricalCriterion:
    id: str
    points: float
    depends_on: tuple[str, ...]
    correlation_group: str | None
    targets: tuple[CriterionTarget, ...]


@dataclass(frozen=True)
class CanonicalProjectionSnapshot:
    """Bulk-loaded, immutable inputs for one canonical evidence replay."""

    ledger_rows: tuple[dict[str, Any], ...]
    contracts_by_source_version: dict[str, dict[str, Any]]
    exercised_by_attempt: dict[str, list[dict[str, Any]]]
    merge_map: dict[str, str]
    error_events_by_attempt: dict[str, list[dict[str, Any]]]
    activity_by_attempt: dict[str, dict[str, Any]]
    p0_references: EffectiveObservationReferences | None


def load_canonical_projection_snapshot(
    repository: Repository,
    *,
    algorithm_version: str,
) -> CanonicalProjectionSnapshot:
    """Read replay inputs once, before the pure attempt fold begins.

    In particular, immutable assessment contracts and their authorized
    correction edges are resolved in bulk.  Keeping repository calls out of the
    fold prevents a projection over N attempts from doing O(N) contract reads.
    """

    ledger_rows = tuple(
        repository.canonical_observation_ledger_v2()
        if algorithm_version in P0_PROJECTION_VERSIONS
        else repository.canonical_observation_ledger()
    )
    contract_ids = {
        str(row["assessment_contract_version_id"])
        for attempt in ledger_rows
        for row in attempt["evidence"]
        if row.get("assessment_contract_version_id")
    }
    p0_references = None
    if algorithm_version in P0_PROJECTION_VERSIONS:
        from learnloop.attempts.effective_observation import (
            load_effective_observation_references,
        )

        p0_references = load_effective_observation_references(
            repository,
            (row.get("active_interpretation") for row in ledger_rows),
        )
    return CanonicalProjectionSnapshot(
        ledger_rows=ledger_rows,
        contracts_by_source_version=repository.effective_assessment_contract_versions(
            contract_ids,
            projection_version=algorithm_version,
        ),
        exercised_by_attempt=repository.all_trace_exercised_facets(),
        merge_map=repository.facet_merge_map(),
        error_events_by_attempt=repository.all_error_events_by_attempt(),
        activity_by_attempt=repository.all_causal_activity_classifications(),
        p0_references=p0_references,
    )


def _historical_contract(
    evidence: list[dict[str, Any]],
    *,
    contracts_by_source_version: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    """Resolve the immutable assessment contract attached to this grading.

    A grading revision is expected to use one contract version across all of its
    criterion observations. Mixed/missing lineage is treated as legacy data and
    falls back to the live item below; new writes require lineage in attempts.py.
    A later authoring correction is consumed only when it explicitly names this
    projection version and authorizes historical measurement reinterpretation.
    """

    version_ids = {
        str(row["assessment_contract_version_id"])
        for row in evidence
        if row.get("assessment_contract_version_id")
    }
    if len(version_ids) != 1:
        return None
    stored = contracts_by_source_version.get(next(iter(version_ids)))
    return stored.get("contract") if stored is not None else None


def _contract_criteria(contract: Mapping[str, Any]) -> list[_HistoricalCriterion]:
    criteria: list[_HistoricalCriterion] = []
    for raw in contract.get("criteria") or []:
        targets = tuple(
            CriterionTarget(
                facet=str(target["facet"]),
                capability=str(target["capability"]),
                role=str(target.get("role") or "primary"),
            )
            for target in raw.get("targets") or []
        )
        criteria.append(
            _HistoricalCriterion(
                id=str(raw["id"]),
                points=float(raw.get("max_points") or 0.0),
                depends_on=tuple(str(value) for value in raw.get("depends_on") or []),
                correlation_group=(
                    str(raw["correlation_group"])
                    if raw.get("correlation_group") is not None
                    else None
                ),
                targets=targets,
            )
        )
    return criteria


def _contract_surface_group(contract: Mapping[str, Any], practice_item_id: str) -> str:
    fingerprint = contract.get("evidence_fingerprint") or {}
    for key in ("shared_stimulus_id", "source_family", "solution_recipe_family"):
        if fingerprint.get(key):
            return str(fingerprint[key])
    if contract.get("surface_family"):
        return str(contract["surface_family"])
    return f"item:{practice_item_id}"


def attribution_weights(
    raw: object, targets: list[CriterionTarget]
) -> dict[tuple[str, str], float]:
    """Normalize persisted failure attribution over the criterion targets."""

    if isinstance(raw, Mapping):
        entries = raw.get("targets") or raw.get("distribution") or []
    else:
        entries = raw if isinstance(raw, list) else []
    allowed = {(target.facet, target.capability) for target in targets}
    weights: dict[tuple[str, str], float] = defaultdict(float)
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        facet = str(entry.get("facet") or "")
        capability = str(entry.get("capability") or "")
        key = (facet, capability)
        if key not in allowed:
            continue
        try:
            weight = max(0.0, float(entry.get("weight", entry.get("probability", 0.0))))
        except (TypeError, ValueError):
            continue
        weights[key] += weight
    total = sum(weights.values())
    if total <= 0:
        return {}
    return {key: weight / total for key, weight in weights.items()}


def observed_unresolved_failure(
    observed_fraction: float,
    targets: Sequence[CriterionTarget],
    attribution: Mapping[tuple[str, str], float],
) -> bool:
    """True when an OBSERVED failure has multiple candidate causes and no
    resolving attribution (§5.3) — the condition that opens an
    unresolved-cause factor.

    The gate reads the observed/authoritative outcome, never the calibrated
    negative fraction: shrinkage under a cold grader-calibration model is
    epistemic uncertainty about the measurement, not evidence that a failure
    occurred. It may discount credit and belief mass, but it cannot fabricate
    a failure-to-diagnose event on a correct answer.
    """

    return observed_fraction < 1.0 and len(targets) > 1 and not attribution


def _target_ref_key(target_ref: Any) -> str:
    """Identity of a candidate cause's declared target, for union de-duplication."""

    if not isinstance(target_ref, Mapping):
        return ""
    kind = str(target_ref.get("kind") or "")
    if kind == "facet_capability":
        return (
            f"facet_capability:{target_ref.get('facet_id')}"
            f":{target_ref.get('capability')}"
        )
    if kind in ("", "none"):
        return ""
    return json.dumps(dict(target_ref), sort_keys=True, default=str)


def _facet_target_cause(target: CriterionTarget) -> dict[str, Any] | None:
    """One synthesized open-world arm for a criterion target."""

    if not target.facet:
        return None
    return {
        "statement": f"Failure of {target.facet} at {target.capability}",
        # A synthesized arm names a facet THIS LEARNER failed — a learner-state
        # claim.  "unknown" silently excluded the materialized hypothesis from
        # `_projected_causal_candidates` (learner_state heads only), which
        # killed the repair offer for every open-world arm.  The open-set arm
        # below stays "unknown": "another cause not represented" may genuinely
        # be content- or instrument-side.
        "cause_scope": "learner_state",
        "target_ref": {
            "kind": "facet_capability",
            "facet_id": target.facet,
            "capability": target.capability,
        },
        # Compatibility keys for existing cause-set selectors.
        "facet": target.facet,
        "capability": target.capability,
    }


def _open_candidate_causes(
    error_events: Sequence[Mapping[str, Any]],
    targets: Sequence[CriterionTarget],
) -> list[dict[str, Any]]:
    """Thin candidate set for an unresolved factor, always open-world."""

    candidates: list[dict[str, Any]] = []
    for event in error_events:
        repair_plan = event.get("repair_plan")
        if not isinstance(repair_plan, Mapping):
            continue
        if repair_plan.get("resolution_status") == "resolved":
            continue
        for raw in repair_plan.get("candidate_causes") or []:
            if not isinstance(raw, Mapping):
                continue
            candidate = dict(raw)
            target_ref = candidate.get("target_ref")
            if isinstance(target_ref, Mapping) and target_ref.get("kind") == "facet_capability":
                candidate.setdefault("facet", target_ref.get("facet_id"))
                candidate.setdefault("capability", target_ref.get("capability"))
            candidates.append(candidate)
    if len(candidates) < 2:
        # UNION, not replace (projection v3).  Replacing dropped the model's
        # own asserted cause from the factor's arms whenever the diagnosis named
        # exactly one: the cause was still minted as a `causal_hypotheses` row,
        # but `build_causal_hypothesis_set` reads the FACTOR's arms, so it
        # locked a probe set that excluded the one cause the diagnosis actually
        # claimed -- and no administered probe could ever confirm or refute it.
        #
        # A synthesized arm for a target the authored cause already names is
        # suppressed: it would restate that cause in the facet vocabulary under
        # indictment (§5.3) and add an arm no instrument can separate from it.
        claimed = {
            _target_ref_key(candidate.get("target_ref")) for candidate in candidates
        }
        candidates = [
            *candidates,
            *(
                synthesized
                for target in targets
                if (synthesized := _facet_target_cause(target)) is not None
                and _target_ref_key(synthesized["target_ref"]) not in claimed
            ),
        ]
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = json.dumps(candidate, sort_keys=True, default=str)
        if key not in seen:
            deduped.append(candidate)
            seen.add(key)
    deduped.append(
        {
            # The `open_set` flag is what actually carries the arm through every
            # consumer; the id is the human-readable placeholder P1 replaces with
            # a materialized hypothesis. One named constant so the readers in
            # `failure_triage` / `probe_targeting` / `causal_probe_coherence`
            # compare against the value that is genuinely written here.
            "hypothesis_id": OPEN_SET_CAUSE_ID,
            "statement": "Another cause not represented by the listed hypotheses",
            "cause_scope": "unknown",
            "target_ref": {"kind": "none"},
            "open_set": True,
        }
    )
    return deduped


def _adjudicated_score_fraction(
    adjudication: Mapping[str, Any] | None,
    interpretation: Mapping[str, Any] | None,
    score_fraction: Mapping[str, float],
) -> float | None:
    """Observed-outcome override when an adjudication heads the interpretation
    chain.

    Under ruling A (2026-07-27) a direction-flipping adjudication ALSO writes a
    superseding ``grading_evidence`` revision, so for post-ruling adjudications
    this override agrees with the ledger by construction. It is kept for the
    adjudications recorded BEFORE the ruling, whose direction lives only in the
    interpretation chain: the observed-failure gate reads the adjudicated class
    (the argmax of the head posterior, so a bounded-trust blend that fails to
    flip the leading class also leaves the observed outcome unchanged). Returns
    None when no adjudication heads the active chain — the ledger fraction
    stands.
    """

    if not adjudication or not interpretation:
        return None
    if adjudication.get("resulting_interpretation_id") != interpretation.get("id"):
        return None
    try:
        posterior = json.loads(interpretation.get("response_posterior_json") or "{}")
    except (TypeError, ValueError):
        posterior = {}
    resolved = (
        max(posterior, key=posterior.get) if posterior else adjudication.get("resolved_class")
    )
    if resolved is None:
        return None
    fraction = score_fraction.get(str(resolved))
    return float(fraction) if fraction is not None else None


def configured_repeat_discount(vault: LoadedVault) -> float:
    extra = getattr(vault.config.evidence.correlation, "__pydantic_extra__", None) or {}
    value = extra.get("repeat_surface_discount")
    if value is None:
        return DEFAULT_REPEAT_SURFACE_DISCOUNT
    return float(value)


def project_canonical_facet_state(
    vault: LoadedVault, repository: Repository, *, clock: Clock | None = None
) -> None:
    """Recompute and persist the canonical belief cache.

    mvp-0.7 (``KM_ALGORITHM_VERSION``) is the byte-identical legacy compatibility
    projection: raw ``points_awarded/points`` score fractions, attempt-type mass
    only. mvp-0.8 (``P0_ALGORITHM_VERSION``, P0.3 §4.3) reads the authoritative
    events ledger and feeds a reliability-discounted EffectiveObservation: the
    calibrated ``E[true_score_fraction]`` replaces the raw fraction and the
    certainty LCB multiplies the evidence mass BEFORE the existing caps /
    localization / assistance discounts bind. Reliability never creates mass."""

    algorithm_version = vault.config.algorithms.algorithm_version
    if algorithm_version not in CANONICAL_STATE_VERSIONS:
        return
    use_p0 = algorithm_version in P0_PROJECTION_VERSIONS
    p0_score_fraction: dict[str, float] = {}
    if use_p0:
        from learnloop.attempts.outcome_schemas import (
            COARSE_RESPONSE_SLUG,
            ensure_builtin_schemas,
        )

        ensure_builtin_schemas(repository, clock=clock)
        schema_row = repository.fetch_outcome_schema_version(slug=COARSE_RESPONSE_SLUG)
        if schema_row is not None:
            import json as _json_mod

            p0_score_fraction = _json_mod.loads(schema_row["score_fraction_json"])

    snapshot = load_canonical_projection_snapshot(
        repository,
        algorithm_version=algorithm_version,
    )
    merge_map = snapshot.merge_map
    repeat_discount = configured_repeat_discount(vault)
    cert_cfg = vault.config.evidence.certification
    overrides = dict(cert_cfg.group_budgets)
    max_groups = cert_cfg.max_groups_per_attempt

    recall: dict[tuple[str, str, str | None], _RecallAcc] = defaultdict(_RecallAcc)
    cap: dict[tuple[str, str], _CapAcc] = defaultdict(_CapAcc)
    unresolved: list[dict[str, object]] = []

    def resolve(facet_id: str) -> str:
        canonical = vault.canonical_facet_id(facet_id)
        # Transitive merge resolution over aliases (§7.1); no beta mass copied.
        current = canonical
        seen: set[str] = set()
        while current in merge_map and current not in seen:
            seen.add(current)
            current = merge_map[current]
        return current

    # Meas §3.A1 guard 1 / §3.A6: the trace observations that license supporting
    # credit. Read once for the whole fold — this is a raw log, so a rebuild sees
    # exactly what the grader reported at attempt time and never re-derives it
    # (the replay path makes no provider call, so a recompute would silently drop
    # every observation).
    exercised_by_attempt = snapshot.exercised_by_attempt
    max_embedded_share = float(getattr(cert_cfg, "max_embedded_credit_share", 1.0))
    for attempt in snapshot.ledger_rows:
        item = vault.practice_items.get(attempt["practice_item_id"])
        contract = _historical_contract(
            attempt["evidence"],
            contracts_by_source_version=snapshot.contracts_by_source_version,
        )
        if contract is not None:
            criteria = _contract_criteria(contract)
            rubric_total = float(contract.get("rubric_total") or 0.0)
            group_key = _contract_surface_group(contract, attempt["practice_item_id"])
        else:
            # Frozen legacy/compatibility observations predate assessment-contract
            # lineage. New mvp-0.7 observations never take this branch.
            if item is None:
                continue
            rubric = vault.rubric_for_item(item)
            if rubric is None or not rubric.criteria:
                continue
            criteria = [
                _HistoricalCriterion(
                    id=criterion.id,
                    points=criterion.points,
                    depends_on=tuple(criterion.depends_on),
                    correlation_group=criterion.correlation_group,
                    targets=tuple(
                        compile_criterion_targets(item, criterion, resolved_rubric=rubric)
                    ),
                )
                for criterion in rubric.criteria
            ]
            rubric_total = sum(max(criterion.points, 0.0) for criterion in criteria)
            group_key = surface_group_id(item)
        if not criteria:
            continue
        evidence_by_criterion = {
            row["criterion_id"]: row for row in attempt["evidence"]
        }
        rubric_total = rubric_total or 1.0
        emass = attempt_evidence_mass(attempt["attempt_type"], vault.config.evidence)
        # The response-level calibrated channel scales evidence authority/mass
        # only. Direction reads the non-superseded grading_evidence revisions —
        # the ledger is the directional authority (ruling A; rationale in the
        # shared helper's docstring). Corrections arrive as superseding
        # revisions, so the fraction below is always the corrected direction.
        if use_p0:
            emass = p0_effective_evidence_mass(
                repository,
                interpretation=attempt.get("active_interpretation"),
                attempt_type_mass=emass,
                references=snapshot.p0_references,
            )
        # Observed-outcome override for the unresolved-cause gate: adjudication
        # is observation-scoped (one activity observation per attempt), so it
        # applies to every criterion of this attempt.
        adjudicated_fraction = (
            _adjudicated_score_fraction(
                attempt.get("active_adjudication"),
                attempt.get("active_interpretation"),
                p0_score_fraction,
            )
            if use_p0
            else None
        )
        activity = resolve_attempt_activity_policy(
            attempt_type=attempt["attempt_type"],
            hints_used=int(attempt["hints_used"]),
            primed=bool(attempt.get("primed")),
            recorded=snapshot.activity_by_attempt.get(str(attempt["attempt_id"])),
        )
        assisted = activity.counts_as_assisted
        certification_eligible = activity.eligible_for_certification
        assistance = "hinted" if assisted else "unassisted"
        created_at = attempt["created_at"]

        outcomes: list[CriterionOutcome] = []
        for criterion in criteria:
            row = evidence_by_criterion.get(criterion.id)
            if row is None:
                # Projection v6: absent evidence is not an observation. A
                # criterion nobody graded produces NO outcome — neither positive
                # nor negative — rather than reading as fraction 0.0 and banking
                # a failure that never happened. A PRESENT row with zero points
                # is the observed-failure case and is unchanged below.
                # ``localize_criterion_outcomes`` treats a dependency missing
                # from the outcome list as passed, so an ungraded parent neither
                # manufactures its own failure nor suppresses its descendants'
                # observed evidence.
                continue
            fraction = 0.0
            if criterion.points > 0:
                fraction = max(0.0, min(1.0, float(row["points_awarded"]) / criterion.points))
            outcomes.append(
                CriterionOutcome(
                    criterion_id=criterion.id,
                    passed=fraction >= FAILURE_THRESHOLD,
                    depends_on=tuple(criterion.depends_on),
                )
            )
        localized = {c.criterion_id: c for c in localize_criterion_outcomes(outcomes)}
        criteria_by_id = {c.id: c for c in criteria}

        # certification credit staged per (facet, capability, correlation group)
        # so the per-group cap and attempt ceiling can be applied jointly.
        staged_credit: dict[str, dict[tuple[str, str], float]] = defaultdict(
            lambda: defaultdict(float)
        )
        # The embedded half of the same staging, so the per-group cap and the
        # attempt ceiling can stay one calculation while guard 2 still knows how
        # much of what survived them was embedded.
        staged_embedded: dict[str, dict[tuple[str, str], float]] = defaultdict(
            lambda: defaultdict(float)
        )
        # Guard 1: facets this attempt's trace actually showed exercised (A6).
        # An attempt with no A6 observations yields an empty set, which is the
        # correct reading of "no evidence the facet was exercised" — so before
        # A6 has a producer every supporting target is unexercised and confers
        # nothing, which is the direction the guard exists to fail in.
        exercised_facets = {
            resolve(str(row["facet_id"]))
            for row in exercised_by_attempt.get(str(attempt["attempt_id"]), ())
        }
        # Matching is on the facet, never the ``(facet, capability)`` cell: A6
        # reports "the trace shows this facet being used", and which capability
        # that use counts at is decided by the criterion's authored target — a
        # deterministic quantity — not by the grader's report. Deciding the cell
        # from a model-reported field would invert standing constraint 8.

        for outcome in outcomes:
            local = localized[outcome.criterion_id]
            if not local.assessable:
                continue  # descendant of a first error: evidence share 0 (§5.3)
            criterion = criteria_by_id[outcome.criterion_id]
            row = evidence_by_criterion.get(criterion.id)
            raw_fraction = 0.0
            if row is not None and criterion.points > 0:
                raw_fraction = max(
                    0.0, min(1.0, float(row["points_awarded"]) / criterion.points)
                )
            fraction = raw_fraction
            authored_targets = list(criterion.targets)
            if not authored_targets:
                continue
            # Meas §3.A1 guard 1: an unexercised supporting claim is not part of
            # this criterion's observation contract for THIS attempt. Splitting
            # the list here rather than filtering at each write site is what
            # keeps the guard from *costing* measurement: `allocate_success_mass`
            # normalizes across the targets it is given, so leaving a discarded
            # supporting target in would dilute the primary's mass to 1/1.3 and
            # authoring an honest supporting target would strictly reduce the
            # evidence the item produces. Same argument for the unresolved-cause
            # gate below, which counts candidate causes.
            targets = [
                target
                for target in authored_targets
                if not supporting_unexercised(target, exercised_facets, resolve=resolve)
            ]
            pmass = criterion_pseudo_mass(criterion.points, rubric_total, emass)
            corr_group = criterion.correlation_group or group_key
            # The record guard 1 owes: what the discarded claims WOULD have
            # earned, computed against the contract as authored. Written BEFORE
            # the empty-target bail-out below, because a criterion whose targets
            # are ALL unexercised supporting claims is precisely the case an
            # author most needs to see — it measured nothing at all.
            if len(targets) != len(authored_targets):
                for alloc in allocate_success_mass(authored_targets, pmass):
                    if not supporting_unexercised(alloc, exercised_facets, resolve=resolve):
                        continue
                    cap[(resolve(alloc.facet), alloc.capability)].unexercised_supporting_mass += (
                        alloc.pseudo_mass * fraction
                    )
            if not targets:
                continue

            raw_attribution = (
                row.get("attribution_json") if row is not None else None
            )
            attribution = attribution_weights(raw_attribution, targets)
            # Direction comes from the raw criterion vector. The calibrated
            # response channel has already scaled ``emass`` above.
            negative_fraction = 1.0 - fraction
            observed_fraction = (
                adjudicated_fraction if adjudicated_fraction is not None else raw_fraction
            )
            unresolved_negative = observed_unresolved_failure(
                observed_fraction, targets, attribution
            )
            if unresolved_negative:
                unresolved.append(
                    {
                        "attempt_id": attempt["attempt_id"],
                        "observation_id": (
                            row.get("observation_id")
                            if row is not None and row.get("observation_id")
                            else f"{attempt['attempt_id']}:{criterion.id}:0"
                        ),
                        "candidate_causes": _open_candidate_causes(
                            snapshot.error_events_by_attempt.get(
                                str(attempt["attempt_id"]), ()
                            ),
                            [
                                CriterionTarget(
                                    facet=resolve(target.facet),
                                    capability=target.capability,
                                    role=target.role,
                                )
                                for target in targets
                            ],
                        ),
                    }
                )
            # Success mass follows authored role weights. Failure mass is handled
            # separately below from the persisted attribution distribution.
            allocations = allocate_success_mass(targets, pmass)
            criterion_discounts: dict[tuple[str, str], tuple[float, bool]] = {}
            for alloc in allocations:
                facet = resolve(alloc.facet)
                capability = alloc.capability
                key = (facet, capability)
                is_new_group = group_key not in cap[key].groups
                discount = 1.0 if is_new_group else repeat_discount
                criterion_discounts[key] = (discount, is_new_group)
                w = alloc.pseudo_mass * discount
                positive = w * fraction
                if positive <= 0:
                    continue
                relationship = "embedded" if alloc.role == "supporting" else "direct"
                if relationship == "embedded":
                    cap[key].embedded_positive_mass += positive
                else:
                    cap[key].direct_positive_mass += positive
                if is_new_group:
                    cap[key].groups.add(group_key)
                credit = (
                    certification_credit(
                        positive,
                        relationship=relationship,
                        assistance=assistance,
                    )
                    if certification_eligible
                    else 0.0
                )
                staged_credit[corr_group][key] += credit
                if relationship == "embedded":
                    staged_embedded[corr_group][key] += credit

                for scope in (None, attempt["practice_item_id"]):
                    acc = recall[(facet, capability, scope)]
                    if acc.created_at is None:
                        acc.created_at = created_at
                    acc.alpha += positive
                    acc.independent_mass += w if is_new_group else 0.0
                    acc.raw_mass += alloc.pseudo_mass
                    acc.last_observed_at = created_at

            if negative_fraction <= 0 or unresolved_negative:
                continue
            if (
                not attribution
                and len(targets) == 1
                and raw_attribution is None
            ):
                attribution = {(targets[0].facet, targets[0].capability): 1.0}
            for target in targets:
                share = attribution.get((target.facet, target.capability), 0.0)
                if share <= 0:
                    continue
                facet = resolve(target.facet)
                key = (facet, target.capability)
                discount, is_new_group = criterion_discounts.get(
                    key,
                    (
                        1.0 if group_key not in cap[key].groups else repeat_discount,
                        group_key not in cap[key].groups,
                    ),
                )
                negative = pmass * negative_fraction * share * discount
                relationship = "embedded" if target.role == "supporting" else "direct"
                if relationship == "embedded":
                    cap[key].embedded_negative_mass += negative
                else:
                    cap[key].direct_negative_mass += negative
                if is_new_group:
                    cap[key].groups.add(group_key)
                for scope in (None, attempt["practice_item_id"]):
                    acc = recall[(facet, target.capability, scope)]
                    if acc.created_at is None:
                        acc.created_at = created_at
                    acc.beta += negative
                    acc.last_observed_at = created_at
                    if fraction < FAILURE_THRESHOLD:
                        acc.last_error_at = created_at
                        acc.consecutive_failures += 1
                    else:
                        acc.consecutive_failures = 0

        # Apply the shared receipt/projection caps, then bank the credit.
        # The itemizing form is used rather than the plain one because guard 2
        # needs the direct/embedded split of what SURVIVED the caps, and the caps
        # scale per correlation group: a cell staged in two groups with different
        # embedded shares, only one of which is trimmed, would get the wrong
        # split from an attempt-wide ratio. `group_scale` is the exact per-group
        # survival factor, and it is the same calculation the receipts use, so
        # the two cannot drift.
        capped_cells, itemization = itemize_observation_contributions(
            staged_credit,
            attempt_type=attempt["attempt_type"],
            evidence_mass=emass,
            group_budget_overrides=overrides,
            max_groups_per_attempt=max_groups,
        )
        embedded_banked: dict[tuple[str, str], float] = defaultdict(float)
        for contribution in itemization:
            staged_here = staged_embedded[contribution.group].get(contribution.cell, 0.0)
            if staged_here > 0:
                embedded_banked[contribution.cell] += staged_here * contribution.group_scale
        for key, credit in capped_cells.items():
            embedded_credit = min(embedded_banked.get(key, 0.0), credit)
            cap[key].embedded_certification_credit += embedded_credit
            cap[key].direct_certification_credit += credit - embedded_credit

    recall_rows = []
    for (facet, capability, scope), acc in recall.items():
        total = acc.alpha + acc.beta
        mean = acc.alpha / total
        variance = acc.alpha * acc.beta / (total**2 * (total + 1.0))
        recall_rows.append(
            {
                "facet_id": facet,
                "capability_key": capability,
                "practice_item_id": scope,
                "recall_alpha": acc.alpha,
                "recall_beta": acc.beta,
                "recall_mean": mean,
                "recall_variance": variance,
                "independent_evidence_mass": acc.independent_mass,
                "raw_coverage_mass": acc.raw_mass,
                "last_observed_at": acc.last_observed_at,
                "last_error_at": acc.last_error_at,
                "consecutive_failures": acc.consecutive_failures,
                "created_at": acc.created_at,
            }
        )
    capability_rows = [
        {
            "facet_id": facet,
            "capability": capability,
            "direct_positive_mass": acc.direct_positive_mass,
            "direct_negative_mass": acc.direct_negative_mass,
            "embedded_positive_mass": acc.embedded_positive_mass,
            "embedded_negative_mass": acc.embedded_negative_mass,
            # Guard 2 (§3.A1): applied once, per cell, over the whole history —
            # not per attempt, because "what fraction of this cell came from
            # embedded evidence" is a statement about the cell, and an
            # attempt-local cap could pass every attempt while the cell still
            # ends up entirely embedded.
            "certification_credit": cap_embedded_credit(
                acc.direct_certification_credit,
                acc.embedded_certification_credit,
                max_embedded_share=max_embedded_share,
            ),
            "direct_certification_credit": acc.direct_certification_credit,
            "embedded_certification_credit": acc.embedded_certification_credit,
            "unexercised_supporting_mass": acc.unexercised_supporting_mass,
            "independent_surface_groups": sorted(acc.groups),
        }
        for (facet, capability), acc in cap.items()
    ]
    repository.replace_canonical_facet_state(
        recall_rows=recall_rows,
        capability_rows=capability_rows,
        algorithm_version=algorithm_version,
        clock=clock,
    )
    _sync_unresolved_cause_factors(repository, unresolved, clock=clock)
    # KM5 §4.2: lazy capability-residual activation is derived from the same
    # just-written ledgers (a no-op unless [capabilities].residual_activation_enabled),
    # so it runs on every path that recomputes canonical state — live attempts and
    # replay alike — and a rebuild reproduces activation deterministically.
    project_capability_residuals(vault, repository, clock=clock)


def project_capability_residuals(
    vault: LoadedVault, repository: Repository, *, clock: Clock | None = None
) -> None:
    """Derive lazy capability-residual activation state (§4.2, KM5; DEFAULT OFF).

    A pure fold over the just-written canonical ledgers (``facet_capability_evidence``
    for the capability slices, pooled into a per-facet shared parent) plus the set
    of closed diagnostic episodes. For each ``(facet, capability)`` cell it decides
    activation deterministically:

    * **persistent capability-sliced residual disagreement** — the slice diverges
      from the pooled parent by ``residual_divergence_threshold`` with at least
      ``residual_min_independent_groups`` surface groups and
      ``residual_min_independent_mass`` independent mass; or
    * a **closed diagnostic episode** on the facet demonstrated divergence (the
      episode already paid for the evidence, so a lower
      ``residual_episode_divergence_threshold`` applies).

    Activation writes learner-model state only — a row per activated
    ``(facet, capability)`` — never a curriculum mutation or lock event. The
    residual belief uses the shared parent as a shrinkage prior; genuinely
    ambiguous (no-capability) observations never reach a slice and so stay pooled
    at the parent. Because it is derived here in the projection fold (replace on
    rebuild), replay reproduces activation byte-identically.

    With the feature disabled (the default) this is a complete no-op: the table is
    never touched, so rebuild determinism is identical with the feature on OR off.
    """

    if vault.config.algorithms.algorithm_version not in CANONICAL_STATE_VERSIONS:
        return
    cfg = vault.config.capabilities
    if not getattr(cfg, "residual_activation_enabled", False):
        return

    divergence_threshold = float(getattr(cfg, "residual_divergence_threshold", 0.20))
    min_mass = float(getattr(cfg, "residual_min_independent_mass", 2.0))
    min_groups = int(getattr(cfg, "residual_min_independent_groups", 2))
    episode_threshold = float(getattr(cfg, "residual_episode_divergence_threshold", 0.12))
    shrinkage = float(getattr(cfg, "residual_shrinkage_pseudo_count", 4.0))

    merge_map = repository.facet_merge_map()

    def resolve(facet_id: str) -> str:
        canonical = vault.canonical_facet_id(facet_id)
        current = canonical
        seen: set[str] = set()
        while current in merge_map and current not in seen:
            seen.add(current)
            current = merge_map[current]
        return current

    # Facets with at least one closed diagnostic episode (lower activation bar).
    episode_facets: set[str] = set()
    for episode in repository.list_probe_episodes(statuses=("complete",)):
        for facet_id in episode.required_facets:
            episode_facets.add(resolve(facet_id))

    # Capability slices + pooled shared parent per facet.
    cells = repository.facet_capability_evidence_all()
    parent_pos: dict[str, float] = defaultdict(float)
    parent_neg: dict[str, float] = defaultdict(float)
    for cell in cells:
        parent_pos[cell.facet_id] += cell.direct_positive_mass + cell.embedded_positive_mass
        parent_neg[cell.facet_id] += cell.direct_negative_mass + cell.embedded_negative_mass

    rows: list[dict[str, object]] = []
    for cell in cells:
        facet = cell.facet_id
        capability = cell.capability
        p_alpha = 1.0 + parent_pos[facet]
        p_beta = 1.0 + parent_neg[facet]
        parent_mean = p_alpha / (p_alpha + p_beta)

        cap_pos = cell.direct_positive_mass + cell.embedded_positive_mass
        cap_neg = cell.direct_negative_mass + cell.embedded_negative_mass
        independent_mass = cap_pos + cap_neg
        independent_groups = len(cell.independent_surface_groups)
        cap_alpha = 1.0 + cap_pos
        cap_beta = 1.0 + cap_neg
        cap_mean = cap_alpha / (cap_alpha + cap_beta)
        divergence = abs(cap_mean - parent_mean)

        has_episode = facet in episode_facets
        persistent = (
            independent_groups >= min_groups
            and independent_mass >= min_mass
            and divergence >= divergence_threshold
        )
        episode_trigger = (
            has_episode and independent_mass > 0.0 and divergence >= episode_threshold
        )
        if not (persistent or episode_trigger):
            continue

        # Shared parent as a shrinkage prior over the capability slice.
        prior_alpha = shrinkage * parent_mean
        prior_beta = shrinkage * (1.0 - parent_mean)
        residual_alpha = prior_alpha + cap_pos
        residual_beta = prior_beta + cap_neg
        residual_mean = residual_alpha / (residual_alpha + residual_beta)
        reason = "persistent_residual_disagreement" if persistent else "closed_diagnostic_episode"
        rows.append(
            {
                "facet_id": facet,
                "capability": capability,
                "active": True,
                "activation_reason": reason,
                "residual_alpha": residual_alpha,
                "residual_beta": residual_beta,
                "residual_mean": residual_mean,
                "parent_alpha": p_alpha,
                "parent_beta": p_beta,
                "parent_mean": parent_mean,
                "divergence": divergence,
                "independent_groups": independent_groups,
                "independent_mass": independent_mass,
            }
        )

    repository.replace_capability_residual_state(
        rows=rows, algorithm_version=KM_ALGORITHM_VERSION, clock=clock
    )


def _sync_unresolved_cause_factors(
    repository: Repository, unresolved: list[dict[str, object]], *, clock: Clock | None
) -> None:
    """Idempotently reconcile open unresolved-cause factors with the projection.

    Keyed by observation_id (stable per grading revision), so a re-run neither
    duplicates nor loses an open cause set. Factors whose failure no longer
    appears are retired; new ambiguous failures are inserted (§5.3).

    Coexistence with the bounded-deferral exits (G15): an observation-keyed
    factor the deferral machinery closed with a ``resolution_kind``
    (repair_confirmed / escalated_unrepaired / expired_unengaged) must stay
    closed even while its failure still appears in the projection —
    ``unresolved_cause_observation_ids`` therefore includes deferral-labeled
    rows of ANY status, so the insert below cannot resurrect one.  The
    retirement path is already safe: ``retire_unresolved_cause_factor``
    touches only OPEN rows, so it can neither stomp a ``resolution_kind`` nor
    re-open a closed factor."""

    existing = repository.unresolved_cause_observation_ids()
    existing_open = repository.open_unresolved_cause_observation_ids()
    wanted = {str(u["observation_id"]): u for u in unresolved}
    for observation_id, record in wanted.items():
        if observation_id not in existing:
            repository.insert_unresolved_cause_factor(
                attempt_id=str(record["attempt_id"]),
                candidate_causes=record["candidate_causes"],
                algorithm_version=KM_ALGORITHM_VERSION,
                observation_id=observation_id,
                clock=clock,
            )
    for observation_id in existing_open - set(wanted):
        repository.retire_unresolved_cause_factor(observation_id, clock=clock)
