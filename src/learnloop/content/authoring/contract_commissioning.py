"""Rung-correct commissioning: author at the capability the contract names.

(spec_measurement_efficiency_v1 §5.8.2 verdict / §5.8.3 / implementation_plan_v1
item 5.1.)

Step 0 measured the loss and located it precisely: of 43 attempts on
``fixtures/linear_algebra``, **100%** hit a facet the contract requires but only
**28%** hit a required ``(facet, capability)`` cell — "72% hit no contract cell at
all, *purely* because the item sits at the wrong rung. Every attempt was on-topic.
Nearly three quarters of the learner's practice was discarded by the capability
dimension alone." That is not a tuning loss; §5.4 makes it structural — "credit
accrues only to the ledger cell of the *observed* capability, so retrieval
evidence can never reach the (facet, method_selection) cell".

**The mechanism.** ``depth_rungs.select_rung`` picks the generation waypoint from
the learner's mastery band (or a probe hypothesis, or a commitment milestone) and
therefore *independently of the blueprint*, while ``_RungGate`` then hard-fails
any generated item whose capability differs from that waypoint. So the blueprint's
declared capability reached the authoring model only as prose
(``blueprint_components``), and the one deterministic gate in the path actively
rejected items authored at it. A cold learner on an LO whose contract asks for
``procedure_execution`` was gated *to* ``retrieval`` — the shortfall the report
calls ``MISMATCH_BELOW``, manufactured at generation time.

**The fix, which is not a policy.** For an LO that declares contract cells the
contract *is* the waypoint: commissioning walks 3.1's
``ContractReachabilityReport.commissioning_queue()`` in the order that queue
already encodes (``_queue_sort_key``: cheapest remedy first, then LO, then
capability rank, then facet) and hands generation the cells that need instruments,
each resolved to the rung that authors AT the contract's capability. There is no
threshold, no ratio and no flag: an LO with no contract cells keeps the mastery-band
rung it has today byte-for-byte, which is also why legacy vaults
(``fixtures/arxiv``: 0 contract cells over 15 LOs) are untouched.

**Integration cells are a distinct case, per §5.8.3.** 18 of 19 integration
components on that vault sit at ``coordination``, zero instruments observe it, and
D3 criterion 2 says ``coordination`` is observable "only behind a reviewed depth
envelope, because the default trajectory deliberately refuses to generate
whole-task work". So a coordination cell is **deferred with a typed reason**, never
quietly re-aimed one rung lower: lowering it would be a blueprint edit disguised
as generation (that edit is item 5.2's job, under D3's criterion, on the vault
content itself), and authoring it off the default trajectory would mint exactly
the whole-task work the trajectory refuses. An integration component at an
*authorable* rung (the one ``method_selection`` integration) is commissioned like
any other cell — its role does not change what a rung means.

:func:`contract_cell_hit_rate` is the falsifiable side: it recomputes Step 0's
28% from the attempt ledger against 3.1's cells, so item 5.1's stated hypothesis
("contract-cell hit rate of new attempts rises from 28%") is checkable rather than
asserted.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Iterable, Mapping

from learnloop.db.repositories import Repository
from learnloop.learner.capability_mapping import (
    compile_criterion_targets,
    default_capability_for,
    is_valid_capability,
)
from learnloop.learner.contract_reachability import (
    CAPABILITY_RANK,
    OBSERVING_ROLES,
    CellReachability,
    ContractReachabilityReport,
    ReachabilityVerdict,
    analyze_contract_reachability,
)
from learnloop.curriculum.depth_rungs import RungTarget, capability_rung
from learnloop.vault.models import LoadedVault, PracticeItem


class CommissionDisposition(StrEnum):
    """What generation may do about one unreachable contract cell.

    ``COMMISSION``
        Author an instrument at the capability the contract names. The cell is
        ``MISMATCH_BELOW`` or ``NO_INSTRUMENT`` and the required capability has a
        default-trajectory waypoint, so the item is authorable today.
    ``DEFER_DEPTH_ENVELOPE``
        The contract requires ``coordination``. Legitimate (§5.8.3 keeps and flags
        an explicit coordination integration) but not authorable by the default
        trajectory — it is owed a reviewed depth envelope or an A1 conjunctive
        capstone (plan item 6.1). Deferred, never re-aimed at a shallower rung.
    ``DEFER_DOMINANCE``
        ``MISMATCH_ABOVE``: instruments already observe this facet *above* the
        requirement, so the remedy is B1 downward dominance propagation, not
        authoring. Commissioning here would buy a duplicate observation.
    ``DEFER_BLUEPRINT_REPAIR``
        ``INDETERMINATE``: the contract names a capability outside the closed
        vocabulary. Nothing can be authored at an unplaceable rung; the blueprint
        is what needs fixing.
    """

    COMMISSION = "COMMISSION"
    DEFER_DEPTH_ENVELOPE = "DEFER_DEPTH_ENVELOPE"
    DEFER_DOMINANCE = "DEFER_DOMINANCE"
    DEFER_BLUEPRINT_REPAIR = "DEFER_BLUEPRINT_REPAIR"

    @property
    def authorable(self) -> bool:
        return self is CommissionDisposition.COMMISSION


#: Typed reason per non-commissionable disposition. Closed vocabulary: a deferral
#: always says *why*, so the backlog is reviewable instead of an unexplained gap
#: (the same discipline D2/D3 impose on rejected facets and components).
DEFERRAL_REASON: dict[CommissionDisposition, str] = {
    CommissionDisposition.DEFER_DEPTH_ENVELOPE: "coordination_requires_reviewed_depth_envelope",
    CommissionDisposition.DEFER_DOMINANCE: "instrument_above_requirement_propagate_dominance",
    CommissionDisposition.DEFER_BLUEPRINT_REPAIR: "required_capability_outside_vocabulary",
}


@dataclass(frozen=True)
class CommissionedCell:
    """One queue row plus the rung that authors AT its required capability."""

    #: 3.1's row, verbatim — the contract identity, verdict and instrument evidence.
    row: CellReachability
    disposition: CommissionDisposition
    #: Position in ``commissioning_queue()``. Carried so downstream ordering can
    #: honour 3.1's ``_queue_sort_key`` instead of re-deriving a second priority.
    queue_rank: int
    #: The waypoint an item for this cell must be authored at. ``None`` exactly
    #: when the disposition is not ``COMMISSION``.
    rung: RungTarget | None
    reason: str | None

    @property
    def learning_object_id(self) -> str:
        return self.row.cell.learning_object_id

    @property
    def facet_id(self) -> str:
        return self.row.cell.facet_id

    @property
    def capability(self) -> str:
        """The capability the CONTRACT names (never the learner's band)."""

        return self.row.cell.capability

    def as_dict(self) -> dict[str, Any]:
        """Payload handed to the authoring model — the cell, not the whole report.

        Deliberately narrow: facet + capability + the waypoint's task-feature
        vector are what "author at this cell" means, plus the contract provenance
        (``recipe_refs`` / ``component_roles``) so the item's rationale can name
        which blueprint component it discharges.
        """

        payload: dict[str, Any] = {
            "facet": self.facet_id,
            "capability": self.capability,
            "verdict": str(self.row.verdict),
            "component_roles": list(self.row.cell.component_roles),
            "recipe_refs": list(self.row.cell.recipe_refs),
            "integration": self.row.cell.integration,
            "disposition": str(self.disposition),
            "queue_rank": self.queue_rank,
            "observed_capabilities": list(self.row.observed_capabilities),
        }
        if self.reason is not None:
            payload["reason"] = self.reason
        if self.rung is not None:
            payload["waypoint_slug"] = self.rung.waypoint_slug
            payload["target_task_features"] = dict(self.rung.task_features)
        return payload


@dataclass(frozen=True)
class CommissionPlan:
    """The commissioning queue, resolved to rungs and grouped by learning object."""

    #: Every non-reachable cell, in ``commissioning_queue()`` order, with its
    #: disposition. Deferrals are kept in the same sequence rather than dropped —
    #: a queue that silently omits its uncommissionable rows is how §5.8.2's 18
    #: coordination obligations went unnoticed for 43 attempts.
    cells: tuple[CommissionedCell, ...]
    #: Every capability the LO's contract names, reachable cells included. This is
    #: the admission set for generated items: an item at a capability outside it is
    #: off-contract by construction.
    contract_capabilities: Mapping[str, tuple[str, ...]]
    #: The report the plan was derived from (aggregates for reporting).
    report: ContractReachabilityReport

    @property
    def commissioned(self) -> tuple[CommissionedCell, ...]:
        return tuple(cell for cell in self.cells if cell.disposition.authorable)

    @property
    def deferred(self) -> tuple[CommissionedCell, ...]:
        return tuple(cell for cell in self.cells if not cell.disposition.authorable)

    def for_learning_object(self, learning_object_id: str) -> tuple[CommissionedCell, ...]:
        """Commissionable cells for one LO, in queue order (best remedy first)."""

        return tuple(
            cell for cell in self.commissioned if cell.learning_object_id == learning_object_id
        )

    def deferred_for_learning_object(
        self, learning_object_id: str
    ) -> tuple[CommissionedCell, ...]:
        return tuple(
            cell for cell in self.deferred if cell.learning_object_id == learning_object_id
        )

    def learning_object_rank(self) -> dict[str, int]:
        """LO -> queue rank of its best commissionable cell.

        The whole point of consuming a *prioritized* queue: when generation can
        only take some LOs, it takes the ones the queue put first. LOs with
        nothing commissionable are absent (callers sort them last).
        """

        ranks: dict[str, int] = {}
        for cell in self.commissioned:
            ranks.setdefault(cell.learning_object_id, cell.queue_rank)
        return ranks

    def capabilities_for(self, learning_object_id: str) -> tuple[str, ...]:
        return tuple(self.contract_capabilities.get(learning_object_id, ()))

    def summary(self) -> dict[str, Any]:
        counts = {str(disposition): 0 for disposition in CommissionDisposition}
        for cell in self.cells:
            counts[str(cell.disposition)] += 1
        return {
            "queue_length": len(self.cells),
            "commissioned": len(self.commissioned),
            "deferred": len(self.deferred),
            "dispositions": counts,
            "learning_objects_commissioned": len(self.learning_object_rank()),
            "reachability": self.report.summary(),
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "summary": self.summary(),
            "cells": [
                {"learning_object_id": cell.learning_object_id, **cell.as_dict()}
                for cell in self.cells
            ],
        }


def _disposition_for(
    repository: Repository,
    row: CellReachability,
    rung_cache: dict[str, RungTarget | None],
) -> tuple[CommissionDisposition, RungTarget | None]:
    """Disposition + rung for one queue row. Total over the verdict vocabulary.

    ``rung_cache`` memoizes ``capability_rung`` across the queue: the closed
    vocabulary has five members, and each miss is a repository round-trip to
    ensure the task-feature schema version.
    """

    if row.verdict is ReachabilityVerdict.MISMATCH_ABOVE:
        return CommissionDisposition.DEFER_DOMINANCE, None
    if row.verdict is ReachabilityVerdict.INDETERMINATE:
        return CommissionDisposition.DEFER_BLUEPRINT_REPAIR, None
    # MISMATCH_BELOW / NO_INSTRUMENT: authoring is the remedy — *if* the contract's
    # capability has a waypoint. `capability_rung` returns None for `coordination`
    # (and for anything out of vocabulary, already handled above), which is D3
    # criterion 2 speaking: not authorable without a reviewed depth envelope.
    capability = row.cell.capability
    if capability not in rung_cache:
        rung_cache[capability] = capability_rung(repository, capability)
    rung = rung_cache[capability]
    if rung is None:
        return CommissionDisposition.DEFER_DEPTH_ENVELOPE, None
    return CommissionDisposition.COMMISSION, rung


def commission_plan(
    vault: LoadedVault,
    repository: Repository,
    *,
    report: ContractReachabilityReport | None = None,
    learning_object_ids: Iterable[str] | None = None,
) -> CommissionPlan:
    """Resolve 3.1's commissioning queue into rung-correct authoring targets.

    ``report`` is an injection seam so a caller that already computed the
    reachability report does not pay for a second vault scan. ``learning_object_ids``
    narrows the queue *without* reordering it — the queue's own priority survives
    filtering, which is the difference between consuming a prioritized queue and
    inventing a second one.
    """

    resolved = report if report is not None else analyze_contract_reachability(vault)
    wanted = set(learning_object_ids) if learning_object_ids is not None else None
    cells: list[CommissionedCell] = []
    rung_cache: dict[str, RungTarget | None] = {}
    for queue_rank, row in enumerate(resolved.commissioning_queue()):
        if wanted is not None and row.cell.learning_object_id not in wanted:
            continue
        disposition, rung = _disposition_for(repository, row, rung_cache)
        cells.append(
            CommissionedCell(
                row=row,
                disposition=disposition,
                queue_rank=queue_rank,
                rung=rung,
                reason=DEFERRAL_REASON.get(disposition),
            )
        )
    capabilities: dict[str, set[str]] = {}
    for row in resolved.cells:
        if wanted is not None and row.cell.learning_object_id not in wanted:
            continue
        capabilities.setdefault(row.cell.learning_object_id, set()).add(row.cell.capability)
    return CommissionPlan(
        cells=tuple(cells),
        contract_capabilities={
            learning_object_id: tuple(
                sorted(
                    values,
                    key=lambda capability: (
                        CAPABILITY_RANK.get(capability, len(CAPABILITY_RANK)),
                        capability,
                    ),
                )
            )
            for learning_object_id, values in sorted(capabilities.items())
        },
        report=resolved,
    )


# -- the falsifiable side: contract-cell hit rate -------------------------------


def item_observed_cells(vault: LoadedVault, item: PracticeItem) -> frozenset[tuple[str, str]] | None:
    """``(canonical facet, capability)`` cells ``item`` can put evidence into.

    ``None`` when the item has no resolvable rubric (it cannot be graded, so it
    observes nothing and must not be scored as a miss). Same authority the write
    path uses — ``compile_criterion_targets`` over the resolved rubric, with the
    criteria-less whole-item fallback — so a "hit" here is a cell an attempt
    really filled, not a proxy for one.
    """

    rubric = vault.rubric_for_item(item)
    if rubric is None:
        return None
    observed: set[tuple[str, str]] = set()
    if rubric.criteria:
        for criterion in rubric.criteria:
            for target in compile_criterion_targets(item, criterion, resolved_rubric=rubric):
                if target.role not in OBSERVING_ROLES:
                    continue
                observed.add(
                    (vault.canonical_facet_id(str(target.facet)), str(target.capability))
                )
        return frozenset(observed)
    declared = getattr(item, "capability", None)
    capability = (
        str(declared)
        if declared and is_valid_capability(str(declared))
        else default_capability_for(item.practice_mode, tier="core")
    )
    return frozenset(
        (vault.canonical_facet_id(str(facet)), capability) for facet in item.evidence_facets
    )


@dataclass(frozen=True)
class ContractHitRate:
    """Step 0's "28%" as a recomputable metric (plan item 5.1's hypothesis).

    The three outcome arms partition ``attempts_scored`` and are exactly §5.8.2's
    decomposition: a cell hit, a facet hit that missed on the capability axis
    alone (the 72% rung loss), and an attempt off the contract's facet set
    entirely. Keeping the middle arm separate is the point — it is the only arm
    rung-correct generation can move, and collapsing it into "miss" would hide
    whether a regression came from the rung or from topic drift.
    """

    attempts_total: int
    attempts_scored: int
    cell_hits: int
    #: Contract facet, wrong capability. §5.8.2: "purely because the item sits at
    #: the wrong rung".
    facet_only_hits: int
    off_contract: int
    #: Excluded from the denominator, with the reason kept visible.
    attempts_without_contract: int
    attempts_missing_item: int
    attempts_unrubricked: int
    #: (cell_hits, scored) per learning object, for locating the loss.
    by_learning_object: Mapping[str, tuple[int, int]]

    @property
    def cell_hit_rate(self) -> float | None:
        """``None`` with nothing scored — never a fake 1.0 (3.1's discipline)."""

        if self.attempts_scored == 0:
            return None
        return self.cell_hits / self.attempts_scored

    @property
    def facet_hit_rate(self) -> float | None:
        if self.attempts_scored == 0:
            return None
        return (self.cell_hits + self.facet_only_hits) / self.attempts_scored

    @property
    def rung_loss_share(self) -> float | None:
        """Share discarded by the capability axis alone. Step 0 measured 72%."""

        if self.attempts_scored == 0:
            return None
        return self.facet_only_hits / self.attempts_scored

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "attempts_total": self.attempts_total,
            "attempts_scored": self.attempts_scored,
            "cell_hits": self.cell_hits,
            "facet_only_hits": self.facet_only_hits,
            "off_contract": self.off_contract,
            "attempts_without_contract": self.attempts_without_contract,
            "attempts_missing_item": self.attempts_missing_item,
            "attempts_unrubricked": self.attempts_unrubricked,
            "cell_hit_rate": self.cell_hit_rate,
            "facet_hit_rate": self.facet_hit_rate,
            "rung_loss_share": self.rung_loss_share,
            "by_learning_object": {
                learning_object_id: {"cell_hits": hits, "attempts_scored": scored}
                for learning_object_id, (hits, scored) in sorted(self.by_learning_object.items())
            },
        }


def contract_cell_hit_rate(
    vault: LoadedVault,
    repository: Repository,
    *,
    since: str | None = None,
    report: ContractReachabilityReport | None = None,
) -> ContractHitRate:
    """Share of attempts that landed in a cell their own LO's contract requires.

    Composes 3.1's contract cells with the attempt ledger; reads no derived state,
    so it is stable under ``rebuild-derived-state``. ``since`` (ISO-8601, compared
    against ``created_at`` the same way the ledger stores it) is the window item
    5.1's hypothesis needs — "the hit rate of *new* attempts" is only meaningful
    against attempts authored after the change.

    Scoring is per attempt against **its own LO's** contract, per §5.8.2. An
    attempt on an LO that declares no contract cells is excluded rather than
    counted as a miss: there is nothing to hit, and folding legacy vaults into the
    denominator would make the metric a measure of blueprint coverage instead of
    rung correctness.
    """

    resolved = report if report is not None else analyze_contract_reachability(vault)
    cells_by_lo: dict[str, set[tuple[str, str]]] = {}
    facets_by_lo: dict[str, set[str]] = {}
    for row in resolved.cells:
        cell = row.cell
        cells_by_lo.setdefault(cell.learning_object_id, set()).add((cell.facet_id, cell.capability))
        facets_by_lo.setdefault(cell.learning_object_id, set()).add(cell.facet_id)

    observed_cache: dict[str, frozenset[tuple[str, str]] | None] = {}
    total = scored = cell_hits = facet_only = off_contract = 0
    no_contract = missing_item = unrubricked = 0
    per_lo: dict[str, list[int]] = {}
    for attempt in repository.list_all_attempts():
        if since is not None and str(attempt.get("created_at") or "") < since:
            continue
        # ``attempts_total`` is the window's population, so every other count below
        # is a share of something the caller asked about.
        total += 1
        learning_object_id = str(attempt.get("learning_object_id") or "")
        contract = cells_by_lo.get(learning_object_id)
        if not contract:
            no_contract += 1
            continue
        item = vault.practice_items.get(str(attempt.get("practice_item_id") or ""))
        if item is None:
            missing_item += 1
            continue
        if item.id not in observed_cache:
            observed_cache[item.id] = item_observed_cells(vault, item)
        observed = observed_cache[item.id]
        if observed is None:
            unrubricked += 1
            continue
        scored += 1
        bucket = per_lo.setdefault(learning_object_id, [0, 0])
        bucket[1] += 1
        if observed & contract:
            cell_hits += 1
            bucket[0] += 1
        elif {facet for facet, _ in observed} & facets_by_lo[learning_object_id]:
            facet_only += 1
        else:
            off_contract += 1
    return ContractHitRate(
        attempts_total=total,
        attempts_scored=scored,
        cell_hits=cell_hits,
        facet_only_hits=facet_only,
        off_contract=off_contract,
        attempts_without_contract=no_contract,
        attempts_missing_item=missing_item,
        attempts_unrubricked=unrubricked,
        by_learning_object={
            learning_object_id: (hits, count)
            for learning_object_id, (hits, count) in sorted(per_lo.items())
        },
    )
