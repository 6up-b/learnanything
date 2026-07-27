"""Facet evidence timeline — the Demonstrated curve (KM §9.6 phase 1, §16).

A deterministic, replayable fold over the immutable observation ledger,
*including* grading supersessions, retired observations and corrected
attribution, producing a **non-monotone** Demonstrated curve for one canonical
facet. A regrade that retires/replaces an observation renders as a visible
annotated correction event — the curve may step down — rather than being
smoothed away.

The fold is a pure function (:func:`fold_demonstrated_timeline`): recomputing the
series from scratch is byte-identical to rendering it incrementally (§16), which
its unit test asserts directly. No snapshot tables, no replay — the sidecar
extracts observation events from the persisted rows and folds them.

Design notes (deliberate phase-1 simplifications, documented):

* The plotted quantity is cumulative **certification credit** for the facet: the
  direct, unassisted, capability-matched positive pseudo-mass accrued so far —
  the same primitive the KM2 canonical projection banks (``certification_credit``
  over ``allocate_success_mass``). Assisted attempts earn zero credit (§5.4), so
  a hinted attempt is a flat point, not a rise.
* Independence, correlation-group budgets, and the attempt-wide ceiling use the
  same shared contribution calculator as the canonical projection. The final
  timeline value therefore equals the banked ledger credit exactly.
* Each graded attempt contributes exactly its *latest grading epoch*'s credit.
  A regrade replaces the attempt's previous contribution (not adds to it), so the
  running total is always ``Σ latest-epoch-credit`` — the "as-of" invariant that
  makes from-scratch == incremental.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field, replace
from typing import Any, Iterable

from learnloop.clock import Clock, SystemClock, parse_utc
from learnloop.db.repositories import GradingEvidenceRecord, Repository
from learnloop.services.assessment_contracts import P0_ALGORITHM_VERSION
from learnloop.services.conjunctive_items import (
    cap_embedded_credit,
    supporting_unexercised,
)
from learnloop.services.capability_mapping import (
    CriterionOutcome,
    allocate_success_mass,
    certification_credit,
    compile_criterion_targets,
    criterion_pseudo_mass,
    localize_criterion_outcomes,
)
from learnloop.services.causal_activity_policy import attempt_counts_as_assisted
from learnloop.services.canonical_projection import (
    DEFAULT_REPEAT_SURFACE_DISCOUNT,
    FAILURE_THRESHOLD,
    _attribution_weights,
    _repeat_discount,
    observed_unresolved_failure,
    p0_effective_evidence_mass,
    surface_group_id,
)
from learnloop.services.evidence import attempt_evidence_mass
from learnloop.services.receipt_contributions import itemize_observation_contributions
from learnloop.vault.models import LoadedVault


@dataclass(frozen=True)
class ObservationDerivation:
    """Per-observation §5.1 receipt line for one (facet, capability) cell.

    Template-renderable, deterministic ingredients of one evidence tick: which
    channel it flowed through, the staged (raw) certification credit vs. what
    actually banked after the coupled caps, and which cap rule bound it (if any).
    """

    capability: str
    channel: str  # "direct" | "embedded" | "assisted"
    raw_credit: float
    capped_credit: float
    bound_by: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "capability": self.capability,
            "channel": self.channel,
            "raw_credit": self.raw_credit,
            "capped_credit": self.capped_credit,
            "bound_by": list(self.bound_by),
        }


@dataclass(frozen=True)
class ObservationEvent:
    """One grading epoch of one attempt, as it bears on a single facet.

    Pure/DB-free so the fold can be unit-tested without a repository. ``kind`` is
    ``observation`` for an attempt's first grading and ``correction`` for every
    later regrade epoch (which supersedes the previous one).
    """

    attempt_id: str
    event_at: str
    kind: str  # "observation" | "correction"
    surface_group: str
    assisted: bool
    # positive pseudo-mass allocated to the facet in this epoch, per capability
    per_capability_positive: dict[str, float] = field(default_factory=dict)
    # Meas §3.A1 guard 2: how much of this epoch's banked credit came through the
    # embedded (supporting-role) channel, per capability. The fold needs the split
    # because the cap is a statement about the CELL's whole history — an
    # attempt-local cap could pass on every attempt while the cell still ends up
    # entirely embedded.
    per_capability_embedded: dict[str, float] = field(default_factory=dict)
    # Repository-derived events already contain final capped credit. The false
    # default preserves the small DB-free fold fixture API.
    authoritative: bool = False
    primed: bool = False
    # Per-capability §5.1 receipt itemization for this epoch's cells. Empty on the
    # DB-free fold fixture path.
    derivation: tuple[ObservationDerivation, ...] = ()

    @property
    def raw_positive(self) -> float:
        return sum(self.per_capability_positive.values())


@dataclass(frozen=True)
class TimelinePoint:
    t: str
    demonstrated: float          # cumulative certification credit (non-monotone)
    delta: float                 # signed change at this event
    kind: str                    # "observation" | "correction"
    is_correction: bool
    attempt_id: str
    surface_group: str
    assisted: bool
    # capabilities with cumulative positive credit after this event
    demonstrated_capabilities: tuple[str, ...]
    primed: bool = False
    # per-capability §5.1 receipt itemization for this observation's own epoch
    derivation: tuple[ObservationDerivation, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "t": self.t,
            "demonstrated": self.demonstrated,
            "delta": self.delta,
            "kind": self.kind,
            "is_correction": self.is_correction,
            "attempt_id": self.attempt_id,
            "surface_group": self.surface_group,
            "assisted": self.assisted,
            "primed": self.primed,
            "demonstrated_capabilities": list(self.demonstrated_capabilities),
            "derivation": [item.as_dict() for item in self.derivation],
        }


@dataclass(frozen=True)
class FacetTimelineSnapshot:
    """Bulk-loaded immutable inputs for one evidence-ledger replay."""

    attempts: tuple[dict[str, Any], ...]
    grading_by_attempt: dict[str, tuple[GradingEvidenceRecord, ...]]
    contracts_by_id: dict[str, dict[str, Any]]
    merge_map: dict[str, str]
    # Meas §3.A1 guard 1 / §3.A6: the trace observations that license supporting
    # credit, per attempt. The timeline is a SECOND fold over the same ledger the
    # canonical projection banks, and the receipt-exactness invariant
    # (`test_receipt_exactness`) is that the two agree to the float — so any input
    # the projection reads, this one must read too.
    exercised_by_attempt: dict[str, frozenset[str]] = field(default_factory=dict)
    # mvp-0.8 (P0.3 §4.3): the response-level reliability-discounted evidence mass
    # per attempt, computed through the SAME shared helper the canonical
    # projection uses (`p0_effective_evidence_mass`). ``None`` means the P0 lane
    # was not loaded — the mvp-0.7 byte-identical path. Same argument as
    # ``exercised_by_attempt`` above: any input the projection reads, this fold
    # must read too, or the Demonstrated curve over-reports the banked ledger
    # (a legacy attempt with no active interpretation banks ZERO under mvp-0.8).
    p0_evidence_mass_by_attempt: dict[str, float] | None = None


def load_facet_timeline_snapshot(repository: Repository) -> FacetTimelineSnapshot:
    """Load the complete timeline ledger with a bounded number of DB reads."""

    grading_by_attempt: dict[str, list[GradingEvidenceRecord]] = defaultdict(list)
    contract_ids: set[str] = set()
    merge_map = repository.facet_merge_map()
    for record in repository.list_grading_evidence_history(include_superseded=True):
        grading_by_attempt[record.attempt_id].append(record)
        if record.assessment_contract_version_id:
            contract_ids.add(record.assessment_contract_version_id)
    return FacetTimelineSnapshot(
        attempts=tuple(repository.list_attempt_history()),
        grading_by_attempt={
            attempt_id: tuple(records)
            for attempt_id, records in grading_by_attempt.items()
        },
        contracts_by_id=repository.fetch_assessment_contract_versions(contract_ids),
        merge_map=merge_map,
        exercised_by_attempt=_resolved_exercised_facets(
            repository.all_trace_exercised_facets(), merge_map
        ),
    )


def _resolved_exercised_facets(
    observations: dict[str, list[dict[str, Any]]], merge_map: dict[str, str]
) -> dict[str, frozenset[str]]:
    """A6 observations with their facet ids merge-resolved (Meas §3.A1 guard 1).

    The projection resolves these ids through the same transitive merge map
    before comparing them against a target's facet; reading them RAW here would
    make the two folds disagree the moment a facet is merged — an observation
    recorded under a retired id would read as exercised in the projection and
    unexercised in the timeline, so the guard would confer credit in one fold and
    withhold it in the other, and `test_receipt_exactness`'s float-exact
    invariant would break with the learner-facing curve understating the ledger.
    Sharing the predicate is not enough; the two folds have to share its INPUT.
    """

    def resolve(facet_id: str) -> str:
        current = str(facet_id)
        seen: set[str] = set()
        while current in merge_map and current not in seen:
            seen.add(current)
            current = merge_map[current]
        return current

    return {
        attempt_id: frozenset(resolve(str(row["facet_id"])) for row in rows)
        for attempt_id, rows in observations.items()
    }


def p0_evidence_mass_by_attempt(
    vault: LoadedVault, repository: Repository
) -> dict[str, float]:
    """Per-attempt mvp-0.8 evidence mass, byte-matched to the projection.

    Walks the same authoritative-events ledger the canonical projection folds
    (``canonical_observation_ledger_v2``) and applies the identical response-
    level reliability discount through the one shared helper, in the same
    association order (attempt-type mass first, then the discount), so the two
    folds cannot drift by even a ulp.
    """

    return {
        str(row["attempt_id"]): p0_effective_evidence_mass(
            repository,
            interpretation=row.get("active_interpretation"),
            attempt_type_mass=attempt_evidence_mass(
                row["attempt_type"], vault.config.evidence
            ),
        )
        for row in repository.canonical_observation_ledger_v2()
    }


def _with_p0_masses(
    vault: LoadedVault, repository: Repository, snapshot: FacetTimelineSnapshot
) -> FacetTimelineSnapshot:
    """Attach the P0 mass map to a snapshot when the vault runs mvp-0.8.

    On an mvp-0.7 vault (or a snapshot that already carries the map) this is a
    no-op, keeping the legacy path byte-identical.
    """

    if vault.config.algorithms.algorithm_version != P0_ALGORITHM_VERSION:
        return snapshot
    if snapshot.p0_evidence_mass_by_attempt is not None:
        return snapshot
    return replace(
        snapshot,
        p0_evidence_mass_by_attempt=p0_evidence_mass_by_attempt(vault, repository),
    )


def fold_demonstrated_timeline(
    events: list[ObservationEvent],
    *,
    repeat_surface_discount: float = DEFAULT_REPEAT_SURFACE_DISCOUNT,
    max_embedded_credit_share: float = 1.0,
) -> list[TimelinePoint]:
    """Fold ordered observation events into the Demonstrated curve (pure).

    Events MUST already be in stable chronological order. The result is a
    deterministic function of the input alone — folding prefixes incrementally
    yields the identical series (the §16 replay invariant).

    ``max_embedded_credit_share`` is A1 guard 2 (Meas §3.A1), applied here rather
    than per event because the cap is a statement about a CELL's whole history:
    an attempt-local cap could pass on every attempt while the cell still ends up
    entirely embedded. The plotted number therefore stays exactly what the ledger
    banks — which is the invariant ``test_receipt_exactness`` exists to hold. The
    1.0 default keeps the DB-free fold fixture API (and any caller predating A1)
    byte-identical.
    """

    seen_groups: set[str] = set()
    contribution_by_attempt: dict[str, float] = {}
    per_capability_total: dict[str, float] = {}
    per_capability_embedded_total: dict[str, float] = {}
    # per-attempt latest epoch's per-capability contribution, so a correction
    # replaces (not stacks on) the attempt's previous capability credit.
    attempt_capability: dict[str, dict[str, float]] = {}
    attempt_capability_embedded: dict[str, dict[str, float]] = {}
    cumulative = 0.0
    series: list[TimelinePoint] = []

    def _capped_total() -> float:
        return sum(
            cap_embedded_credit(
                total - per_capability_embedded_total.get(capability, 0.0),
                per_capability_embedded_total.get(capability, 0.0),
                max_embedded_share=max_embedded_credit_share,
            )
            for capability, total in per_capability_total.items()
        )

    for event in events:
        is_new_group = event.surface_group not in seen_groups
        discount = 1.0 if is_new_group else repeat_surface_discount
        seen_groups.add(event.surface_group)

        new_caps: dict[str, float] = {}
        if event.authoritative:
            new_caps = {
                capability: max(float(credit), 0.0)
                for capability, credit in event.per_capability_positive.items()
                if credit > 0.0
            }
        elif not event.assisted:
            for capability, positive in event.per_capability_positive.items():
                credit = certification_credit(
                    positive * discount, relationship="direct", assistance="unassisted"
                )
                if credit > 0.0:
                    new_caps[capability] = credit
        new_contrib = sum(new_caps.values())
        new_embedded = (
            {
                capability: max(float(credit), 0.0)
                for capability, credit in event.per_capability_embedded.items()
                if credit > 0.0 and capability in new_caps
            }
            if event.authoritative
            else {}
        )

        old_contrib = contribution_by_attempt.get(event.attempt_id, 0.0)
        old_caps = attempt_capability.get(event.attempt_id, {})
        old_embedded = attempt_capability_embedded.get(event.attempt_id, {})
        # Replace this attempt's capability credit with the latest epoch's.
        for capability, value in old_caps.items():
            per_capability_total[capability] = per_capability_total.get(capability, 0.0) - value
        for capability, value in new_caps.items():
            per_capability_total[capability] = per_capability_total.get(capability, 0.0) + value
        for capability, value in old_embedded.items():
            per_capability_embedded_total[capability] = (
                per_capability_embedded_total.get(capability, 0.0) - value
            )
        for capability, value in new_embedded.items():
            per_capability_embedded_total[capability] = (
                per_capability_embedded_total.get(capability, 0.0) + value
            )
        attempt_capability[event.attempt_id] = new_caps
        attempt_capability_embedded[event.attempt_id] = new_embedded
        contribution_by_attempt[event.attempt_id] = new_contrib

        # `delta` stays the signed change in the PLOTTED quantity, so guard 2's
        # cap moves the curve rather than sitting beside it. Uncapped, the two
        # agree exactly, and `old_contrib`/`new_contrib` remain the per-attempt
        # bookkeeping the correction logic needs.
        previous = cumulative
        cumulative = _capped_total() if max_embedded_credit_share < 1.0 else (
            cumulative + new_contrib - old_contrib
        )
        delta = cumulative - previous
        demonstrated_caps = tuple(
            sorted(cap for cap, value in per_capability_total.items() if value > 1e-9)
        )
        series.append(
            TimelinePoint(
                t=event.event_at,
                demonstrated=cumulative,
                delta=delta,
                kind=event.kind,
                is_correction=event.kind == "correction",
                attempt_id=event.attempt_id,
                surface_group=event.surface_group,
                assisted=event.assisted,
                demonstrated_capabilities=demonstrated_caps,
                primed=event.primed,
                derivation=event.derivation,
            )
        )
    return series


def _epoch_certification_credit(
    vault: LoadedVault,
    item,
    rubric,
    *,
    rows_by_criterion: dict[str, dict],
    attempt_type: str,
    surface_group: str,
    assisted: bool,
    seen_groups_by_cell: dict[tuple[str, str], set[str]],
    resolve,
    exercised_facets: frozenset[str] = frozenset(),
    evidence_mass_override: float | None = None,
) -> tuple[
    dict[tuple[str, str], float],
    dict[tuple[str, str], set[str]],
    list,
    dict[tuple[str, str], str],
    dict[tuple[str, str], float],
]:
    """Final capped certification credit for every cell in one grading epoch.

    Mirrors the KM2 canonical projection's per-attempt accumulation exactly —
    localize the criterion DAG, drop unassessable descendants of a first error
    (share 0, §5.3), allocate each assessable criterion's success pseudo-mass
    across its targets, and replicate the projection's *sequential* surface-group
    marking: a later criterion landing on an already-marked (cell, group) inside
    the same grading state takes the repeat discount, groups are marked only
    where positive or attributed negative mass actually lands, and the marks are
    returned so the caller can advance the cross-attempt novelty state the same
    way the projection's ``cap[key].groups`` evolves.
    """

    rubric_total = sum(max(c.points, 0.0) for c in rubric.criteria) or 1.0
    # ``evidence_mass_override`` is the mvp-0.8 reliability-discounted mass the
    # caller precomputed per attempt through the shared projection helper; this
    # function stays DB-free, so the discount cannot be computed here.
    emass = (
        evidence_mass_override
        if evidence_mass_override is not None
        else attempt_evidence_mass(attempt_type, vault.config.evidence)
    )
    outcomes: list[CriterionOutcome] = []
    for criterion in rubric.criteria:
        row = rows_by_criterion.get(criterion.id)
        if row is None:
            # Projection v6 mirror: absent evidence is not an observation.
            # Identical skip to the canonical projection, or the two folds
            # would disagree the moment an attempt is partially graded.
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
    criteria_by_id = {c.id: c for c in rubric.criteria}

    staged: dict[str, dict[tuple[str, str], float]] = defaultdict(
        lambda: defaultdict(float)
    )
    staged_embedded: dict[str, dict[tuple[str, str], float]] = defaultdict(
        lambda: defaultdict(float)
    )
    marked: dict[tuple[str, str], set[str]] = defaultdict(set)
    # Channel per cell for the §5.1 receipt: a cell that ever earns primary
    # (direct) credit renders as direct; supporting-only credit as embedded.
    relationship_by_cell: dict[tuple[str, str], str] = {}

    def _is_new_group(cell: tuple[str, str]) -> bool:
        return (
            surface_group not in seen_groups_by_cell.get(cell, set())
            and surface_group not in marked[cell]
        )

    repeat_discount = _repeat_discount(vault)
    assistance = "hinted" if assisted else "unassisted"
    for outcome in outcomes:
        local = localized[outcome.criterion_id]
        if not local.assessable:
            continue
        criterion = criteria_by_id[outcome.criterion_id]
        row = rows_by_criterion.get(criterion.id)
        fraction = 0.0
        if row is not None and criterion.points > 0:
            fraction = max(0.0, min(1.0, float(row["points_awarded"]) / criterion.points))
        # Assessment contracts always carry compiled targets. `item` is only
        # needed for pre-contract legacy evidence whose criterion had none.
        authored_targets = (
            list(criterion.targets)
            if criterion.targets
            else compile_criterion_targets(item, criterion, resolved_rubric=rubric)
            if item is not None
            else []
        )
        # Meas §3.A1 guard 1, identical to the projection's split (see there for
        # why it is a split rather than a filter at each write site).
        targets = [
            target
            for target in authored_targets
            if not supporting_unexercised(target, exercised_facets, resolve=resolve)
        ]
        if not targets:
            continue
        pmass = criterion_pseudo_mass(criterion.points, rubric_total, emass)
        correlation_group = criterion.correlation_group or surface_group
        attribution = _attribution_weights(
            row.get("attribution") if row is not None else None, targets
        )
        negative_fraction = 1.0 - fraction
        # `fraction` here is the raw criterion fraction (the timeline never
        # substitutes the calibrated p0 fraction), so it is the observed outcome
        # the shared unresolved-failure gate expects.
        unresolved_negative = observed_unresolved_failure(fraction, targets, attribution)
        criterion_discounts: dict[tuple[str, str], tuple[float, bool]] = {}
        for alloc in allocate_success_mass(targets, pmass):
            cell = (resolve(alloc.facet), alloc.capability)
            is_new_group = _is_new_group(cell)
            discount = 1.0 if is_new_group else repeat_discount
            criterion_discounts[cell] = (discount, is_new_group)
            positive = alloc.pseudo_mass * discount * fraction
            if positive <= 0:
                continue
            relationship = "embedded" if alloc.role == "supporting" else "direct"
            if is_new_group:
                marked[cell].add(surface_group)
            credit = certification_credit(
                positive, relationship=relationship, assistance=assistance
            )
            staged[correlation_group][cell] += credit
            if relationship == "embedded":
                staged_embedded[correlation_group][cell] += credit
            if relationship == "direct" or cell not in relationship_by_cell:
                relationship_by_cell[cell] = relationship
        # Negative mass certifies nothing, but the projection marks the surface
        # group where an attributed failure lands; replicate that marking so
        # later attempts' novelty discounts stay identical to the banked fold.
        if negative_fraction <= 0 or unresolved_negative:
            continue
        if not attribution and len(targets) == 1:
            attribution = {(targets[0].facet, targets[0].capability): 1.0}
        for target in targets:
            share = attribution.get((target.facet, target.capability), 0.0)
            if share <= 0:
                continue
            cell = (resolve(target.facet), target.capability)
            _, is_new_group = criterion_discounts.get(
                cell, (1.0, _is_new_group(cell))
            )
            if is_new_group:
                marked[cell].add(surface_group)
    cert_cfg = vault.config.evidence.certification
    capped, itemization = itemize_observation_contributions(
        staged,
        attempt_type=attempt_type,
        evidence_mass=emass,
        group_budget_overrides=dict(cert_cfg.group_budgets),
        max_groups_per_attempt=cert_cfg.max_groups_per_attempt,
    )
    # Guard 2 is a per-CELL cap over the whole history, so it cannot be applied
    # here; what this epoch owes the fold is how much of its banked credit was
    # embedded, using the same exact `group_scale` the projection uses.
    embedded_banked: dict[tuple[str, str], float] = defaultdict(float)
    for contribution in itemization:
        staged_here = staged_embedded[contribution.group].get(contribution.cell, 0.0)
        if staged_here > 0:
            embedded_banked[contribution.cell] += staged_here * contribution.group_scale
    return capped, dict(marked), itemization, dict(relationship_by_cell), dict(embedded_banked)


def _decoded_attribution(raw: str | None) -> object:
    """Decode a persisted failure-attribution payload (None on legacy rows)."""

    if not raw:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


def _observation_events_by_facet(
    vault: LoadedVault,
    snapshot: FacetTimelineSnapshot,
    canonical_facets: Iterable[str],
) -> dict[str, list[ObservationEvent]]:
    """Extract events for every requested facet in one grading-ledger walk.

    Reads the full grading history (``include_superseded=True``) so regrades
    surface as later epochs; attempts are ordered chronologically and epochs
    within an attempt by grading time.
    """

    requested = {
        vault.canonical_facet_id(str(facet_id)) for facet_id in canonical_facets
    }
    events_by_facet: dict[str, list[ObservationEvent]] = {
        facet_id: [] for facet_id in requested
    }
    seen_groups_by_cell: dict[tuple[str, str], set[str]] = defaultdict(set)
    merge_map = snapshot.merge_map

    def resolve(facet_id: str) -> str:
        current = vault.canonical_facet_id(facet_id)
        seen: set[str] = set()
        while current in merge_map and current not in seen:
            seen.add(current)
            current = merge_map[current]
        return current

    p0_masses = snapshot.p0_evidence_mass_by_attempt
    for attempt in snapshot.attempts:
        item = vault.practice_items.get(attempt["practice_item_id"])
        rows = snapshot.grading_by_attempt.get(str(attempt["id"]), ())
        # mvp-0.8: the reliability-discounted mass precomputed through the shared
        # projection helper. The 0.0 fallback is fail-closed — the v2 ledger
        # covers every attempt by construction, so a miss can only mean a stale
        # snapshot, and absent data must not create mass.
        evidence_mass_override = (
            p0_masses.get(str(attempt["id"]), 0.0) if p0_masses is not None else None
        )
        # Group by immutable grading revision when present. Timestamp remains the
        # compatibility key for legacy/manual regrades; a FrozenClock can give
        # revisions the same timestamp, so it cannot be the primary new-data key.
        epochs: dict[tuple[str, str], list] = {}
        for record in rows:
            revision_key = (
                f"revision:{record.grading_revision}"
                if record.grading_revision is not None
                else f"legacy:{record.created_at}"
            )
            epochs.setdefault((record.created_at, revision_key), []).append(record)
        # P2 §4.4: one authority, shared with the canonical projection.
        assisted = attempt_counts_as_assisted(
            attempt_type=attempt["attempt_type"],
            hints_used=int(attempt.get("hints_used") or 0),
            primed=bool(attempt.get("primed")),
        )
        # A correction replaces this attempt's contribution; it must keep the
        # attempt's original novelty position rather than becoming a repeat.
        # Every epoch is therefore evaluated against the pre-attempt novelty
        # state, and only the *latest* epoch (the attempt's effective grading
        # state — what the canonical projection consumes) advances it.
        prior_seen = {cell: set(groups) for cell, groups in seen_groups_by_cell.items()}
        marked_by_latest_epoch: dict[tuple[str, str], set[str]] = {}
        # Later grading epochs may restate only part of an attempt's criteria
        # (a partial supersession); the effective state at each epoch is the
        # cumulative latest row per criterion, matching the projection's
        # non-superseded view at the final epoch.
        cumulative_rows: dict[str, dict] = {}
        epoch_items = sorted(epochs.items())
        # An attempt with no grading evidence marks nothing under projection v6:
        # absent evidence produces no criterion outcomes, so it can neither bank
        # mass nor advance surface-group novelty in either fold. (Pre-v6 this
        # branch ran a marking-only pass because the projection treated every
        # ungraded criterion as a failure.)
        for index, ((epoch_at, _revision_key), records) in enumerate(epoch_items):
            version_ids = {
                record.assessment_contract_version_id
                for record in records
                if record.assessment_contract_version_id
            }
            contract = None
            if len(version_ids) == 1:
                stored = snapshot.contracts_by_id.get(next(iter(version_ids)))
                contract = stored.get("contract") if stored is not None else None
            if contract is not None:
                from learnloop.services.assessment_contracts import rubric_from_contract

                rubric = rubric_from_contract(contract)
                fingerprint = contract.get("evidence_fingerprint") or {}
                group = next(
                    (
                        str(fingerprint[key])
                        for key in ("shared_stimulus_id", "source_family", "solution_recipe_family")
                        if fingerprint.get(key)
                    ),
                    str(contract.get("surface_family") or f"item:{attempt['practice_item_id']}"),
                )
            else:
                rubric = vault.rubric_for_item(item) if item is not None else None
                group = surface_group_id(item) if item is not None else f"item:{attempt['practice_item_id']}"
            if rubric is None or not rubric.criteria:
                continue
            for record in records:
                cumulative_rows[record.criterion_id] = {
                    "points_awarded": record.points_awarded,
                    "attribution": _decoded_attribution(record.attribution_json),
                }
            (
                credits,
                marked,
                itemization,
                relationship_by_cell,
                embedded_banked,
            ) = _epoch_certification_credit(
                vault,
                item,
                rubric,
                rows_by_criterion=dict(cumulative_rows),
                attempt_type=attempt["attempt_type"],
                surface_group=group,
                assisted=assisted,
                seen_groups_by_cell=prior_seen,
                resolve=resolve,
                exercised_facets=snapshot.exercised_by_attempt.get(
                    str(attempt["id"]), frozenset()
                ),
                evidence_mass_override=evidence_mass_override,
            )
            marked_by_latest_epoch = marked
            # Avoid an event for a facet this historical epoch never targeted.
            historical_facets = {
                resolve(target.facet)
                for criterion in rubric.criteria
                for target in criterion.targets
            }
            credited_facets = {facet for facet, _capability in credits}
            for canonical_facet in requested & (historical_facets | credited_facets):
                per_capability = {
                    capability: credit
                    for (facet, capability), credit in credits.items()
                    if facet == canonical_facet
                }
                per_capability_embedded = {
                    capability: credit
                    for (facet, capability), credit in embedded_banked.items()
                    if facet == canonical_facet and credit > 0.0
                }
                # §5.1 per-observation receipt for this facet's cells: raw vs
                # capped credit and the binding cap rule, one entry per
                # capability. Assisted epochs certify nothing, so the channel
                # is "assisted" (zero credit).
                derivation = tuple(
                    ObservationDerivation(
                        capability=capability,
                        channel=(
                            "assisted"
                            if assisted
                            else relationship_by_cell.get(
                                (canonical_facet, capability), "direct"
                            )
                        ),
                        raw_credit=contribution.raw_credit,
                        capped_credit=contribution.capped_credit,
                        bound_by=contribution.bound_by,
                    )
                    for contribution in itemization
                    if contribution.cell[0] == canonical_facet
                    for capability in (contribution.cell[1],)
                )
                events_by_facet[canonical_facet].append(
                    ObservationEvent(
                        attempt_id=attempt["id"],
                        event_at=epoch_at,
                        kind="observation" if index == 0 else "correction",
                        surface_group=group,
                        assisted=assisted,
                        per_capability_positive=per_capability,
                        per_capability_embedded=per_capability_embedded,
                        authoritative=True,
                        primed=bool(attempt.get("primed")),
                        derivation=derivation,
                    )
                )
        for cell, groups in marked_by_latest_epoch.items():
            seen_groups_by_cell[cell].update(groups)
    # Stable global order: by event time, then attempt id, then original order.
    for events in events_by_facet.values():
        events.sort(key=lambda event: (event.event_at, event.attempt_id))
    return events_by_facet


def _observation_events(
    vault: LoadedVault,
    repository: Repository,
    canonical_facet: str,
) -> list[FacetEvidenceEvent]:
    """Compatibility wrapper for callers that inspect one facet's events."""
    snapshot = _with_p0_masses(
        vault, repository, load_facet_timeline_snapshot(repository)
    )
    return _observation_events_by_facet(
        vault,
        snapshot,
        [canonical_facet],
    ).get(canonical_facet, [])


def facet_evidence_timelines(
    vault: LoadedVault,
    repository: Repository,
    facet_ids: Iterable[str],
    *,
    snapshot: FacetTimelineSnapshot | None = None,
) -> dict[str, list[TimelinePoint]]:
    """Build multiple Demonstrated curves from one bulk ledger replay."""

    canonical = {
        vault.canonical_facet_id(str(facet_id)) for facet_id in facet_ids
    }
    if not canonical:
        return {}
    loaded = _with_p0_masses(
        vault, repository, snapshot or load_facet_timeline_snapshot(repository)
    )
    events_by_facet = _observation_events_by_facet(vault, loaded, canonical)
    repeat_discount = _repeat_discount(vault)
    return {
        facet_id: fold_demonstrated_timeline(
            events_by_facet.get(facet_id, []),
            repeat_surface_discount=repeat_discount,
            max_embedded_credit_share=float(
                getattr(
                    vault.config.evidence.certification,
                    "max_embedded_credit_share",
                    1.0,
                )
            ),
        )
        for facet_id in canonical
    }


def facet_evidence_timeline(
    vault: LoadedVault, repository: Repository, facet_id: str
) -> list[TimelinePoint]:
    """The Demonstrated curve for ``facet_id`` (canonicalized) — the §9.6 phase-1
    surface. Empty list when the facet has no graded evidence."""

    canonical = vault.canonical_facet_id(facet_id)
    return facet_evidence_timelines(vault, repository, [canonical]).get(canonical, [])


# -- §5.1 Ready derivation (B5 phase 2) ---------------------------------------


@dataclass(frozen=True)
class ReadyCapabilitySlice:
    """One capability slice pooled into the facet's shared recall belief."""

    capability: str
    recall_alpha: float
    recall_beta: float
    recall_mean: float
    independent_evidence_mass: float

    def as_dict(self) -> dict[str, object]:
        return {
            "capability": self.capability,
            "recall_alpha": self.recall_alpha,
            "recall_beta": self.recall_beta,
            "recall_mean": self.recall_mean,
            "independent_evidence_mass": self.independent_evidence_mass,
        }


@dataclass(frozen=True)
class ReadyDerivation:
    """The §5.1 Ready-sentence ingredients, template-rendered from ledger state.

    ``pooled_recall_mean`` is the facet's shared beta belief — the exact
    capability-agnostic quantity the canonical projection banks and the capability
    grid feeds into ``predicted_facet_recall``. It is folded from the capability
    slices (``alpha = 1 + Σ(alpha_c - 1)``, likewise beta), matching the canonical
    state reader byte-for-byte. ``notes`` disclose the ingredients that are *not*
    folded into this facet-global number (report-not-fabricate, §1.5/§1.6).
    """

    supported: bool
    pooled_recall_mean: float
    recall_alpha: float
    recall_beta: float
    independent_evidence_mass: float
    direct_observation_count: int
    unassisted_observation_count: int
    pooled_capabilities: tuple[ReadyCapabilitySlice, ...]
    last_evidence_at: str | None
    days_since_last_evidence: int | None
    algorithm_version: str
    notes: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "supported": self.supported,
            "pooled_recall_mean": self.pooled_recall_mean,
            "recall_alpha": self.recall_alpha,
            "recall_beta": self.recall_beta,
            "independent_evidence_mass": self.independent_evidence_mass,
            "direct_observation_count": self.direct_observation_count,
            "unassisted_observation_count": self.unassisted_observation_count,
            "pooled_capabilities": [slice_.as_dict() for slice_ in self.pooled_capabilities],
            "last_evidence_at": self.last_evidence_at,
            "days_since_last_evidence": self.days_since_last_evidence,
            "algorithm_version": self.algorithm_version,
            "notes": list(self.notes),
        }


def facet_ready_derivation(
    vault: LoadedVault,
    repository: Repository,
    facet_id: str,
    series: list[TimelinePoint],
    *,
    clock: Clock | None = None,
) -> ReadyDerivation | None:
    """§5.1 Ready-derivation ingredients for a canonical facet, or ``None``.

    Reuses the canonical projection's persisted intermediates (the capability-
    sliced ``facet_recall_state`` rows) rather than recomputing an approximation:
    the pooled recall mean is folded from the same slices the projection wrote, so
    it equals the capability grid's facet-mean input exactly. Observation counts
    come from the already-folded Demonstrated ``series`` (one point per attempt
    epoch), so no history is re-walked.

    ``None`` on a legacy (mvp-0.6) vault with no capability ledger — the Ready
    receipt is a canonical-state surface.
    """

    from learnloop.services.facet_state_reader import (
        is_canonical_state_vault,
        resolve_canonical_facet,
    )

    if not is_canonical_state_vault(vault):
        return None

    merge_map = repository.facet_merge_map()
    canonical = resolve_canonical_facet(vault, merge_map, facet_id)

    # Shared (aggregate) capability slices for this facet — practice_item_id None.
    slices: list[ReadyCapabilitySlice] = []
    alpha = 1.0
    beta = 1.0
    independent_mass = 0.0
    last_evidence_at: str | None = None
    for row in repository.canonical_facet_recall_states():
        if row.practice_item_id is not None:
            continue
        if resolve_canonical_facet(vault, merge_map, row.facet_id) != canonical:
            continue
        alpha += row.recall_alpha - 1.0
        beta += row.recall_beta - 1.0
        independent_mass += row.independent_evidence_mass
        if last_evidence_at is None or (
            row.last_observed_at is not None and row.last_observed_at > last_evidence_at
        ):
            last_evidence_at = row.last_observed_at or last_evidence_at
        slices.append(
            ReadyCapabilitySlice(
                capability=row.capability_key,
                recall_alpha=row.recall_alpha,
                recall_beta=row.recall_beta,
                recall_mean=row.recall_mean,
                independent_evidence_mass=row.independent_evidence_mass,
            )
        )
    slices.sort(key=lambda slice_: slice_.capability)

    # Observation counts fold from the Demonstrated series: one attempt may carry
    # several epochs (a correction), but it is one direct observation of the facet.
    assisted_by_attempt: dict[str, bool] = {}
    for point in series:
        assisted_by_attempt[point.attempt_id] = point.assisted
    direct_observations = len(assisted_by_attempt)
    unassisted_observations = sum(
        1 for assisted in assisted_by_attempt.values() if not assisted
    )

    days_since: int | None = None
    parsed = parse_utc(last_evidence_at) if last_evidence_at is not None else None
    if parsed is not None:
        now = (clock or SystemClock()).now()
        days_since = max(0, (now - parsed).days)

    pooled_mean = alpha / (alpha + beta)
    version = vault.config.algorithms.algorithm_version

    notes: list[str] = []
    if slices:
        notes.append(
            f"Pooled from {len(slices)} capability slice"
            f"{'' if len(slices) == 1 else 's'}: "
            + ", ".join(slice_.capability for slice_ in slices)
            + "."
        )
    notes.append(
        "Per-learning-object Ready additionally blends that object's mastery "
        "backbone; this facet-level receipt shows the shared evidence only."
    )
    notes.append(
        "No decay factor is folded into this pooled quantity — facet-level FSRS "
        "decay is a separate goal-projection phase (§4.1)."
    )
    notes.append(f"Evidence spans one algorithm version ({version}).")

    return ReadyDerivation(
        supported=True,
        pooled_recall_mean=pooled_mean,
        recall_alpha=alpha,
        recall_beta=beta,
        independent_evidence_mass=independent_mass,
        direct_observation_count=direct_observations,
        unassisted_observation_count=unassisted_observations,
        pooled_capabilities=tuple(slices),
        last_evidence_at=last_evidence_at,
        days_since_last_evidence=days_since,
        algorithm_version=version,
        notes=tuple(notes),
    )
