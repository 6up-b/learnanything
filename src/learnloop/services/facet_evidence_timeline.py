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
from dataclasses import dataclass, field

from learnloop.clock import Clock, SystemClock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.services.capability_mapping import (
    CriterionOutcome,
    allocate_success_mass,
    certification_credit,
    compile_criterion_targets,
    criterion_pseudo_mass,
    localize_criterion_outcomes,
)
from learnloop.services.canonical_projection import (
    ASSISTED_ATTEMPT_TYPES,
    DEFAULT_REPEAT_SURFACE_DISCOUNT,
    FAILURE_THRESHOLD,
    _attribution_weights,
    _repeat_discount,
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


def fold_demonstrated_timeline(
    events: list[ObservationEvent],
    *,
    repeat_surface_discount: float = DEFAULT_REPEAT_SURFACE_DISCOUNT,
) -> list[TimelinePoint]:
    """Fold ordered observation events into the Demonstrated curve (pure).

    Events MUST already be in stable chronological order. The result is a
    deterministic function of the input alone — folding prefixes incrementally
    yields the identical series (the §16 replay invariant).
    """

    seen_groups: set[str] = set()
    contribution_by_attempt: dict[str, float] = {}
    per_capability_total: dict[str, float] = {}
    # per-attempt latest epoch's per-capability contribution, so a correction
    # replaces (not stacks on) the attempt's previous capability credit.
    attempt_capability: dict[str, dict[str, float]] = {}
    cumulative = 0.0
    series: list[TimelinePoint] = []

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

        old_contrib = contribution_by_attempt.get(event.attempt_id, 0.0)
        old_caps = attempt_capability.get(event.attempt_id, {})
        # Replace this attempt's capability credit with the latest epoch's.
        for capability, value in old_caps.items():
            per_capability_total[capability] = per_capability_total.get(capability, 0.0) - value
        for capability, value in new_caps.items():
            per_capability_total[capability] = per_capability_total.get(capability, 0.0) + value
        attempt_capability[event.attempt_id] = new_caps
        contribution_by_attempt[event.attempt_id] = new_contrib

        delta = new_contrib - old_contrib
        cumulative += delta
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
) -> tuple[
    dict[tuple[str, str], float],
    dict[tuple[str, str], set[str]],
    list,
    dict[tuple[str, str], str],
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
    emass = attempt_evidence_mass(attempt_type, vault.config.evidence)
    outcomes: list[CriterionOutcome] = []
    for criterion in rubric.criteria:
        row = rows_by_criterion.get(criterion.id)
        fraction = 0.0
        if row is not None and criterion.points > 0:
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
        targets = (
            list(criterion.targets)
            if criterion.targets
            else compile_criterion_targets(item, criterion, resolved_rubric=rubric)
            if item is not None
            else []
        )
        if not targets:
            continue
        pmass = criterion_pseudo_mass(criterion.points, rubric_total, emass)
        correlation_group = criterion.correlation_group or surface_group
        attribution = _attribution_weights(
            row.get("attribution") if row is not None else None, targets
        )
        negative_fraction = 1.0 - fraction
        unresolved_negative = negative_fraction > 0 and len(targets) > 1 and not attribution
        criterion_discounts: dict[tuple[str, str], tuple[float, bool]] = {}
        for alloc in allocate_success_mass(targets, pmass):
            cell = (resolve(alloc.facet), alloc.capability)
            is_new_group = _is_new_group(cell)
            discount = 1.0 if is_new_group else repeat_discount
            criterion_discounts[cell] = (discount, is_new_group)
            positive = alloc.pseudo_mass * discount * fraction
            if positive <= 0:
                continue
            if is_new_group:
                marked[cell].add(surface_group)
            relationship = "embedded" if alloc.role == "supporting" else "direct"
            credit = certification_credit(
                positive, relationship=relationship, assistance=assistance
            )
            staged[correlation_group][cell] += credit
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
    return capped, dict(marked), itemization, dict(relationship_by_cell)


def _decoded_attribution(raw: str | None) -> object:
    """Decode a persisted failure-attribution payload (None on legacy rows)."""

    if not raw:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


def _observation_events(
    vault: LoadedVault, repository: Repository, canonical_facet: str
) -> list[ObservationEvent]:
    """Extract ordered observation events for a facet from persisted rows.

    Reads the full grading history (``include_superseded=True``) so regrades
    surface as later epochs; attempts are ordered chronologically and epochs
    within an attempt by grading time.
    """

    events: list[ObservationEvent] = []
    seen_groups_by_cell: dict[tuple[str, str], set[str]] = defaultdict(set)
    merge_map = repository.facet_merge_map()

    def resolve(facet_id: str) -> str:
        current = vault.canonical_facet_id(facet_id)
        seen: set[str] = set()
        while current in merge_map and current not in seen:
            seen.add(current)
            current = merge_map[current]
        return current

    for attempt in repository.list_attempt_history():
        item = vault.practice_items.get(attempt["practice_item_id"])
        rows = repository.fetch_grading_evidence(attempt["id"], include_superseded=True)
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
        assisted = (
            attempt["attempt_type"] in ASSISTED_ATTEMPT_TYPES
            or int(attempt.get("hints_used") or 0) > 0
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
        if not epoch_items:
            # No grading evidence: the attempt certifies nothing, but the
            # canonical projection still walks its criteria (all fractions 0)
            # and can mark surface groups through attributed failures. Run the
            # marking-only pass so later attempts see identical novelty.
            rubric = vault.rubric_for_item(item) if item is not None else None
            if rubric is not None and rubric.criteria:
                group = surface_group_id(item)
                _, marked, _items, _rel = _epoch_certification_credit(
                    vault,
                    item,
                    rubric,
                    rows_by_criterion={},
                    attempt_type=attempt["attempt_type"],
                    surface_group=group,
                    assisted=assisted,
                    seen_groups_by_cell=prior_seen,
                    resolve=resolve,
                )
                marked_by_latest_epoch = marked
        for index, ((epoch_at, _revision_key), records) in enumerate(epoch_items):
            version_ids = {
                record.assessment_contract_version_id
                for record in records
                if record.assessment_contract_version_id
            }
            contract = None
            if len(version_ids) == 1:
                stored = repository.fetch_assessment_contract_version(next(iter(version_ids)))
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
            credits, marked, itemization, relationship_by_cell = _epoch_certification_credit(
                vault,
                item,
                rubric,
                rows_by_criterion=dict(cumulative_rows),
                attempt_type=attempt["attempt_type"],
                surface_group=group,
                assisted=assisted,
                seen_groups_by_cell=prior_seen,
                resolve=resolve,
            )
            marked_by_latest_epoch = marked
            per_capability = {
                capability: credit
                for (facet, capability), credit in credits.items()
                if facet == canonical_facet
            }
            # Avoid an event for a facet this historical epoch never targeted.
            historical_facets = {
                resolve(target.facet)
                for criterion in rubric.criteria
                for target in criterion.targets
            }
            if not per_capability and canonical_facet not in historical_facets:
                continue
            # §5.1 per-observation receipt for this facet's cells: raw vs capped
            # credit and the binding cap rule, one entry per capability. Assisted
            # epochs certify nothing, so the channel is "assisted" (zero credit).
            derivation = tuple(
                ObservationDerivation(
                    capability=capability,
                    channel=(
                        "assisted"
                        if assisted
                        else relationship_by_cell.get((canonical_facet, capability), "direct")
                    ),
                    raw_credit=contribution.raw_credit,
                    capped_credit=contribution.capped_credit,
                    bound_by=contribution.bound_by,
                )
                for contribution in itemization
                if contribution.cell[0] == canonical_facet
                for capability in (contribution.cell[1],)
            )
            events.append(
                ObservationEvent(
                    attempt_id=attempt["id"],
                    event_at=epoch_at,
                    kind="observation" if index == 0 else "correction",
                    surface_group=group,
                    assisted=assisted,
                    per_capability_positive=per_capability,
                    authoritative=True,
                    primed=bool(attempt.get("primed")),
                    derivation=derivation,
                )
            )
        for cell, groups in marked_by_latest_epoch.items():
            seen_groups_by_cell[cell].update(groups)
    # Stable global order: by event time, then attempt id, then original order.
    events.sort(key=lambda event: (event.event_at, event.attempt_id))
    return events


def facet_evidence_timeline(
    vault: LoadedVault, repository: Repository, facet_id: str
) -> list[TimelinePoint]:
    """The Demonstrated curve for ``facet_id`` (canonicalized) — the §9.6 phase-1
    surface. Empty list when the facet has no graded evidence."""

    canonical = vault.canonical_facet_id(facet_id)
    events = _observation_events(vault, repository, canonical)
    return fold_demonstrated_timeline(
        events, repeat_surface_discount=_repeat_discount(vault)
    )


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
