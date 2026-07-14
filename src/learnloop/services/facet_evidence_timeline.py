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

from collections import defaultdict
from dataclasses import dataclass, field

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
    _repeat_discount,
    surface_group_id,
)
from learnloop.services.evidence import attempt_evidence_mass
from learnloop.services.receipt_contributions import cap_observation_contributions
from learnloop.vault.models import LoadedVault


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
            "demonstrated_capabilities": list(self.demonstrated_capabilities),
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
) -> tuple[dict[tuple[str, str], float], set[tuple[str, str]]]:
    """Final capped certification credit for every cell in one grading epoch.

    Mirrors the KM2 canonical projection's per-attempt accumulation: localize the
    criterion DAG, drop unassessable descendants of a first error (share 0, §5.3),
    then allocate each assessable criterion's success pseudo-mass across its
    targets and keep the share landing on this facet's capabilities.
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
    touched: set[tuple[str, str]] = set()
    repeat_discount = _repeat_discount(vault)
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
        for alloc in allocate_success_mass(targets, pmass):
            cell = (resolve(alloc.facet), alloc.capability)
            touched.add(cell)
            discount = (
                1.0
                if surface_group not in seen_groups_by_cell.get(cell, set())
                else repeat_discount
            )
            relationship = "embedded" if alloc.role == "supporting" else "direct"
            credit = certification_credit(
                alloc.pseudo_mass * fraction * discount,
                relationship=relationship,
                assistance="hinted" if assisted else "unassisted",
            )
            correlation_group = criterion.correlation_group or surface_group
            staged[correlation_group][cell] += credit
    cert_cfg = vault.config.evidence.certification
    return (
        cap_observation_contributions(
            staged,
            attempt_type=attempt_type,
            evidence_mass=emass,
            group_budget_overrides=dict(cert_cfg.group_budgets),
            max_groups_per_attempt=cert_cfg.max_groups_per_attempt,
        ),
        touched,
    )


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
        if not rows:
            continue
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
        prior_seen = {cell: set(groups) for cell, groups in seen_groups_by_cell.items()}
        touched_for_attempt: set[tuple[str, str]] = set()
        groups_for_attempt: set[str] = set()
        for index, ((epoch_at, _revision_key), records) in enumerate(sorted(epochs.items())):
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
            rows_by_criterion = {
                record.criterion_id: {"points_awarded": record.points_awarded}
                for record in records
            }
            credits, touched = _epoch_certification_credit(
                vault,
                item,
                rubric,
                rows_by_criterion=rows_by_criterion,
                attempt_type=attempt["attempt_type"],
                surface_group=group,
                assisted=assisted,
                seen_groups_by_cell=prior_seen,
                resolve=resolve,
            )
            touched_for_attempt.update(touched)
            groups_for_attempt.add(group)
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
            events.append(
                ObservationEvent(
                    attempt_id=attempt["id"],
                    event_at=epoch_at,
                    kind="observation" if index == 0 else "correction",
                    surface_group=group,
                    assisted=assisted,
                    per_capability_positive=per_capability,
                    authoritative=True,
                )
            )
        for cell in touched_for_attempt:
            seen_groups_by_cell[cell].update(groups_for_attempt)
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
