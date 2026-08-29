"""Contract-cell reachability: can *any* authored item observe this cell?
(spec_measurement_efficiency_v1 §5.8.2, Wave 1 / implementation_plan_v1 item 3.1.)

Step 0 (§5.8.2) measured that on ``fixtures/linear_algebra`` 55 of 64 contract
cells (86%) were unreachable and **zero** integration cells were reachable —
certification was structurally impossible for 20 of 21 LOs *regardless* of learner
performance, practice volume, or decision rule. 43 attempts were spent before
anybody noticed. This module is the standing check whose absence allowed that: it
is pure static analysis over vault content (no attempts, no learner state, no
model, no provider calls), so it costs nothing to run on every ``learnloop
doctor``.

Vocabulary, as it actually exists in the tree:

* A **contract cell** is a ``(learning_object_id, canonical facet, required
  capability)`` triple named by some blueprint recipe component of that LO
  (``vault.models.recipe_components`` — ``all_of``, ``any_of``, and the optional
  ``integration`` component alike). Cells are deduped: the same
  ``(facet, capability)`` requirement repeated across recipes of one LO is one
  cell, one commissioning obligation. Only requirement modalities in
  :data:`CONTRACT_MODALITIES` count, per knowledge-model §8.2 ("only ``hard`` and
  exercised ``path_specific`` requirements materially affect task
  likelihood/attribution"); ``facilitating`` / ``instructional_order`` components
  are counted separately as ``advisory_component_count`` and never gate anything.
  This is the definition that reproduces §5.8.2's 64 cells / 19 integration cells
  exactly.

* An **instrument** for a cell is an *active* practice item in the vault whose
  resolved rubric compiles a criterion target onto that facet **at that
  capability** (``capability_mapping.compile_criterion_targets``). That is not a
  proxy for "can produce evidence here" — it is the very same compile the write
  path uses, and §5.4 credit is structural on the capability axis: "credit accrues
  only to the ledger cell of the *observed* capability, so retrieval evidence can
  never reach the (facet, method_selection) cell." Diagnostic probes are ordinary
  practice items and are therefore already in the pool; exam-pool entries are
  *reservations of* those same items (``exam_pool.reserve_exam_pool``) and add no
  instrument, so no DB read is needed and the report is a pure function of vault
  content.

The four verdicts of §5.8.2 (:class:`ReachabilityVerdict`) plus one explicit
abstention arm. The output doubles as Stage 5.1's commissioning queue
(:meth:`ContractReachabilityReport.commissioning_queue`): each row carries the
contract that names the cell, the facet, the required capability, the capabilities
actually available, and the instruments at each, which is everything needed to
decide *what to author* without re-reading the vault.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Iterable, Mapping

from learnloop.learner.capability_mapping import (
    compile_criterion_targets,
    default_capability_for,
    is_valid_capability,
)
from learnloop.substrate.instrument_serving import unservable_reason
from learnloop.vault.models import (
    CAPABILITY_VOCABULARY,
    LoadedVault,
    PracticeItem,
    recipe_components,
)

# The capability ladder runs LOW -> HIGH in ``CAPABILITY_VOCABULARY`` declaration
# order: retrieval(0) < schema_interpretation(1) < procedure_execution(2) <
# method_selection(3) < coordination(4). Two independent authorities in the tree
# fix that direction: ``depth_rungs.DEFAULT_TRAJECTORY`` climbs recall ->
# interpret -> execute -> select_method in exactly this order and "deliberately
# stops before ... coordination" as the deepest region, and
# ``capability_mapping.DEFAULT_CAPABILITY`` calls ``schema_interpretation`` "the
# conservative middle capability (not retrieval, not coordination)".
#
# Therefore: an instrument authored ABOVE the requirement is a candidate for
# downward dominance propagation (§5.8.2's B1 remedy — demonstrating the deeper
# capability implies the shallower one), while an instrument BELOW it can never
# close the cell, because dominance only propagates downward.
CAPABILITY_RANK: dict[str, int] = {
    capability: index for index, capability in enumerate(CAPABILITY_VOCABULARY)
}

#: Requirement modalities that make a component a *contract* cell (knowledge-model
#: §8.2). ``path_specific`` is included because it binds whenever its path is the
#: exercised one and static analysis cannot know that it never will be; excluding
#: it would silently under-report an uncloseable obligation, which is the exact
#: failure mode this check exists to prevent. ``facilitating`` and
#: ``instructional_order`` are advisory and are reported separately.
CONTRACT_MODALITIES: frozenset[str] = frozenset({"hard", "path_specific"})

#: Practice-item statuses that count as available instruments. A ``retired`` item
#: is not an instrument: it cannot be scheduled, so it cannot close a cell. (This
#: is the pool that reproduces §5.8.2's "of 39 declared facets, only 14 are
#: observed by any item".)
INSTRUMENT_STATUSES: frozenset[str] = frozenset({"active"})

#: Roles under which a compiled criterion target counts as an observation of its
#: cell. Both earn certification credit (``supporting`` at weight 0.3, §5.4), so
#: both make the cell *observable*; the per-cell row keeps the roles so a
#: commissioning reader can prefer a cell that has a ``primary`` instrument.
OBSERVING_ROLES: frozenset[str] = frozenset({"primary", "supporting"})


class ReachabilityVerdict(StrEnum):
    """§5.8.2's four verdicts, plus one abstention arm.

    ``REACHABLE``
        Some active instrument observes this facet at exactly the capability the
        contract names. The cell is closeable by practice today.
    ``MISMATCH_ABOVE``
        Instruments observe the facet, none at the required capability, and at
        least one sits *higher* on the ladder. Remedy is B1 dominance
        propagation, not authoring — the evidence exists, the projection just
        does not carry it downward. §5.8.2 measured this as 1 cell in 25 on the
        practiced scope, which is why B1 was demoted from Wave 4.
    ``MISMATCH_BELOW``
        Instruments observe the facet but *every one* of them sits lower on the
        ladder. No amount of practice on them can close the cell; dominance only
        propagates downward. Remedy is real instruments authored at the rung.
    ``NO_INSTRUMENT``
        Nothing in the pool observes this facet at any capability. Remedy is
        authoring (or admitting the facet was minted without an instrument — D2's
        separability criterion).
    ``INDETERMINATE``
        Explicit abstention, NOT one of the four: the contract names a capability
        outside the closed vocabulary, so the cell cannot be placed on the ladder
        and the above/below question has no answer. Never counted as reachable.
        ``doctor``'s ``blueprint:invalid_capability`` is the error that fixes it.
    """

    REACHABLE = "REACHABLE"
    MISMATCH_ABOVE = "MISMATCH_ABOVE"
    MISMATCH_BELOW = "MISMATCH_BELOW"
    NO_INSTRUMENT = "NO_INSTRUMENT"
    INDETERMINATE = "INDETERMINATE"

    @property
    def reachable(self) -> bool:
        return self is ReachabilityVerdict.REACHABLE


#: Commissioning priority for the Stage 5.1 queue: cheapest remedy first, so the
#: queue reads top-down as "propagate, then re-rung, then author, then fix the
#: blueprint". Purely presentational — the verdict is the decision.
_QUEUE_PRIORITY: dict[ReachabilityVerdict, int] = {
    ReachabilityVerdict.MISMATCH_ABOVE: 0,
    ReachabilityVerdict.MISMATCH_BELOW: 1,
    ReachabilityVerdict.NO_INSTRUMENT: 2,
    ReachabilityVerdict.INDETERMINATE: 3,
    ReachabilityVerdict.REACHABLE: 4,
}

#: What Stage 5.1 has to commission per verdict (§5.8.2's remedy column).
_REMEDY: dict[ReachabilityVerdict, str] = {
    ReachabilityVerdict.REACHABLE: "none",
    ReachabilityVerdict.MISMATCH_ABOVE: "propagate_downward_dominance",
    ReachabilityVerdict.MISMATCH_BELOW: "author_instrument_at_required_capability",
    ReachabilityVerdict.NO_INSTRUMENT: "author_instrument_for_facet",
    ReachabilityVerdict.INDETERMINATE: "repair_blueprint_capability",
}


@dataclass(frozen=True)
class ContractCell:
    """One ``(LO, facet, required capability)`` obligation of a blueprint (§7.2).

    ``component_roles`` / ``recipe_refs`` are the *contract identity* a
    commissioning reader acts on: which recipe of which blueprint asked for this,
    and whether it asked conjunctively (``all_of``), as an alternative
    (``any_of``), or as the whole-task assembly (``integration``).
    """

    learning_object_id: str
    facet_id: str            # canonical (alias/merge resolved)
    capability: str          # the capability the CONTRACT names
    component_roles: tuple[str, ...]   # subset of ("all_of", "any_of", "integration")
    modalities: tuple[str, ...]
    recipe_refs: tuple[str, ...]       # "<blueprint_id>:<recipe_id>"

    @property
    def integration(self) -> bool:
        """True when some recipe names this cell as its integration component.

        §5.8.2/§5.8.3: 18 of 19 integration components sat at ``coordination`` and
        zero were reachable, which is what made 20 of 21 LOs uncertifiable.
        """

        return "integration" in self.component_roles

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.learning_object_id, self.facet_id, self.capability)

    def as_dict(self) -> dict[str, Any]:
        return {
            "learning_object_id": self.learning_object_id,
            "facet_id": self.facet_id,
            "required_capability": self.capability,
            "component_roles": list(self.component_roles),
            "modalities": list(self.modalities),
            "recipe_refs": list(self.recipe_refs),
            "integration": self.integration,
        }


@dataclass(frozen=True)
class CellReachability:
    """A contract cell plus its verdict and the instrument evidence behind it."""

    cell: ContractCell
    verdict: ReachabilityVerdict
    #: Every capability at which SOME active instrument observes this facet, in
    #: ladder order. Empty => NO_INSTRUMENT.
    observed_capabilities: tuple[str, ...]
    #: Instruments observing the facet at exactly the required capability
    #: (non-empty iff REACHABLE).
    matching_instrument_ids: tuple[str, ...]
    #: Instruments observing the facet at any capability — the material a
    #: re-rung/dominance remedy has to work from.
    instrument_ids: tuple[str, ...]
    #: Nearest observed capability strictly below / above the requirement, so a
    #: commissioning row states the size of the rung gap without recomputation.
    nearest_below: str | None
    nearest_above: str | None
    #: Roles under which the facet is observed at all ("primary"/"supporting").
    observed_roles: tuple[str, ...]

    @property
    def remedy(self) -> str:
        return _REMEDY[self.verdict]

    def as_dict(self) -> dict[str, Any]:
        payload = self.cell.as_dict()
        payload.update(
            {
                "verdict": str(self.verdict),
                "observed_capabilities": list(self.observed_capabilities),
                "matching_instrument_ids": list(self.matching_instrument_ids),
                "instrument_ids": list(self.instrument_ids),
                "nearest_below": self.nearest_below,
                "nearest_above": self.nearest_above,
                "observed_roles": list(self.observed_roles),
                "remedy": self.remedy,
            }
        )
        return payload


@dataclass(frozen=True)
class ContractReachabilityReport:
    """Per-cell verdicts plus §5.8's aggregate proportions.

    §5.8's whole argument is stated in shares ("86% unreachable", "0% of
    integration cells"), so the aggregates are part of the artifact, not a
    convenience: a vault whose reachable share is near zero is not a vault with a
    tuning problem.
    """

    cells: tuple[CellReachability, ...]
    #: LOs that declare at least one contract cell.
    learning_object_count: int
    #: LOs in the vault (contract-bearing or not) — the denominator that makes
    #: "no blueprints at all" visible instead of reading as a clean bill.
    learning_objects_total: int
    #: Active practice items considered as instruments.
    instrument_count: int
    #: Items skipped because no rubric resolves (they cannot be graded, so they
    #: cannot observe anything).
    unrubricked_item_count: int
    #: Components dropped as advisory (``facilitating`` / ``instructional_order``).
    advisory_component_count: int
    #: Registered facets, and how many of them any instrument observes at any
    #: capability (§5.8.2's ``measurement_rank / facets_declared``).
    facets_declared: int
    facets_instrumented: int
    #: Items skipped because the serving surface cannot carry their instrument
    #: class (``instrument_serving.unservable_reason``). Its own count, because
    #: its remedy is a renderer rather than authoring: a cell instrumented only
    #: by these is blocked on deployment, not unauthored, and it must not read as
    #: reachable. Zero while the predicate has no arms — the fence, not a finding.
    unservable_item_count: int = 0

    @property
    def counts(self) -> dict[str, int]:
        """Cell count per verdict, every arm present (zeros included)."""

        tally = {str(verdict): 0 for verdict in ReachabilityVerdict}
        for row in self.cells:
            tally[str(row.verdict)] += 1
        return tally

    @property
    def integration_counts(self) -> dict[str, int]:
        tally = {str(verdict): 0 for verdict in ReachabilityVerdict}
        for row in self.cells:
            if row.cell.integration:
                tally[str(row.verdict)] += 1
        return tally

    @property
    def cell_count(self) -> int:
        return len(self.cells)

    @property
    def integration_cell_count(self) -> int:
        return sum(1 for row in self.cells if row.cell.integration)

    @property
    def reachable_count(self) -> int:
        return sum(1 for row in self.cells if row.verdict.reachable)

    @property
    def unreachable_count(self) -> int:
        return self.cell_count - self.reachable_count

    @property
    def reachable_share(self) -> float | None:
        """Reachable / total, or ``None`` when there are no contract cells.

        ``None`` rather than ``1.0``: a legacy vault with no blueprints has
        nothing to certify, and reporting a perfect score for it would be the
        fake 100% that hides exactly the population Stage 5 needs to find.
        """

        if not self.cells:
            return None
        return self.reachable_count / self.cell_count

    @property
    def integration_reachable_share(self) -> float | None:
        total = self.integration_cell_count
        if total == 0:
            return None
        return self.integration_counts[str(ReachabilityVerdict.REACHABLE)] / total

    def commissioning_queue(self) -> tuple[CellReachability, ...]:
        """Non-reachable cells, cheapest remedy first (Stage 5.1's input)."""

        return tuple(
            sorted(
                (row for row in self.cells if not row.verdict.reachable),
                key=_queue_sort_key,
            )
        )

    def by_verdict(self, verdict: ReachabilityVerdict) -> tuple[CellReachability, ...]:
        return tuple(row for row in self.cells if row.verdict is verdict)

    def summary(self) -> dict[str, Any]:
        """Aggregate-only payload (bounded size; safe to embed in doctor JSON)."""

        return {
            "cell_count": self.cell_count,
            "reachable_count": self.reachable_count,
            "unreachable_count": self.unreachable_count,
            "reachable_share": self.reachable_share,
            "counts": self.counts,
            "integration_cell_count": self.integration_cell_count,
            "integration_counts": self.integration_counts,
            "integration_reachable_share": self.integration_reachable_share,
            "learning_object_count": self.learning_object_count,
            "learning_objects_total": self.learning_objects_total,
            "instrument_count": self.instrument_count,
            "unrubricked_item_count": self.unrubricked_item_count,
            "unservable_item_count": self.unservable_item_count,
            "advisory_component_count": self.advisory_component_count,
            "facets_declared": self.facets_declared,
            "facets_instrumented": self.facets_instrumented,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "summary": self.summary(),
            "cells": [row.as_dict() for row in self.cells],
        }


def _queue_sort_key(row: CellReachability) -> tuple[Any, ...]:
    return (
        _QUEUE_PRIORITY[row.verdict],
        row.cell.learning_object_id,
        CAPABILITY_RANK.get(row.cell.capability, len(CAPABILITY_RANK)),
        row.cell.capability,
        row.cell.facet_id,
    )


# -- the instrument pool -------------------------------------------------------


def _item_observed_capability(item: PracticeItem, tier: str) -> str:
    """Capability a criterion of ``tier`` observes on ``item``.

    Mirrors ``capability_mapping._observed_capability`` (the item's authored
    capability outranks the coarse practice-mode default; a ``transfer``-tier
    criterion deliberately probes past the item's own waypoint and keeps the tier
    default). Duplicated rather than imported because it is private there; kept
    in lockstep deliberately — if the two ever diverge, this report starts lying
    about what the write path files evidence under.
    """

    if tier != "transfer":
        declared = getattr(item, "capability", None)
        if declared and is_valid_capability(str(declared)):
            return str(declared)
    return default_capability_for(item.practice_mode, tier=tier)


@dataclass(frozen=True)
class _Observation:
    facet_id: str      # canonical
    capability: str
    role: str


def _item_observations(vault: LoadedVault, item: PracticeItem) -> list[_Observation] | None:
    """Cells ``item`` can put evidence into, or ``None`` when it cannot be graded.

    The authority is ``compile_criterion_targets`` over the item's resolved
    rubric: authored targets win verbatim, legacy criteria compile to the item's
    declared capability, and honest abstentions (``item_local`` /
    ``no_canonical_facet`` measurement status) contribute nothing — the same
    answers the grading write path gets, so a cell called REACHABLE here really
    is a cell an attempt can fill.
    """

    rubric = vault.rubric_for_item(item)
    if rubric is None:
        return None
    observations: list[_Observation] = []
    if rubric.criteria:
        for criterion in rubric.criteria:
            for target in compile_criterion_targets(item, criterion, resolved_rubric=rubric):
                if target.role not in OBSERVING_ROLES:
                    continue
                observations.append(
                    _Observation(
                        facet_id=vault.canonical_facet_id(str(target.facet)),
                        capability=str(target.capability),
                        role=str(target.role),
                    )
                )
        return observations
    # A criteria-less rubric still grades whole-item (there is nothing to
    # localize to), so fall back to the item's whole facet set at its own rung —
    # the same shape ``exam_pool._item_components`` uses. Without this an item
    # under a criteria-free rubric would read as measuring nothing and inflate
    # NO_INSTRUMENT.
    capability = _item_observed_capability(item, "core")
    return [
        _Observation(
            facet_id=vault.canonical_facet_id(str(facet)),
            capability=capability,
            role="primary",
        )
        for facet in item.evidence_facets
    ]


@dataclass(frozen=True)
class InstrumentPool:
    """facet -> capability -> instrument ids, plus the roles seen per facet."""

    by_facet: Mapping[str, Mapping[str, tuple[str, ...]]]
    roles_by_facet: Mapping[str, tuple[str, ...]]
    instrument_count: int
    unrubricked_item_count: int
    #: Items excluded because ``instrument_serving.unservable_reason`` says the
    #: serving surface cannot carry their class. Counted, never merged into
    #: ``unrubricked``: the remedy is a renderer, not a rubric.
    unservable_item_count: int = 0

    def capabilities(self, facet_id: str) -> tuple[str, ...]:
        """Observed capabilities for ``facet_id``, in ladder order."""

        return tuple(
            sorted(
                self.by_facet.get(facet_id, {}),
                key=lambda capability: (
                    CAPABILITY_RANK.get(capability, len(CAPABILITY_RANK)),
                    capability,
                ),
            )
        )

    def item_ids(self, facet_id: str, capability: str | None = None) -> tuple[str, ...]:
        per_capability = self.by_facet.get(facet_id, {})
        if capability is not None:
            return tuple(per_capability.get(capability, ()))
        merged: set[str] = set()
        for ids in per_capability.values():
            merged.update(ids)
        return tuple(sorted(merged))


def build_instrument_pool(
    vault: LoadedVault,
    *,
    statuses: Iterable[str] = INSTRUMENT_STATUSES,
) -> InstrumentPool:
    """Index every active practice item by the cells it can observe.

    Pure over vault content — no repository, no attempts. ``statuses`` is a seam
    for tests and for asking the counterfactual "what if retired items were
    revived?"; the standing check uses :data:`INSTRUMENT_STATUSES`.

    TWO AXES, NOT ONE (§7.2). "Authored" and "deliverable" are different facts.
    Status answers the first; ``instrument_serving.unservable_reason`` answers the
    second — whether the serving surface can carry the item's class at all — and
    a cell whose only instrument cannot be served is not reachable, it is blocked
    on a renderer. Counting it as REACHABLE would flip the cell green and hide
    the gap in the one report Stage 5 built to find gaps. The predicate has no
    arms today (both retired when their renderer landed), so this costs one
    ``None`` check per item and exists so the next class shipped ahead of its
    surface cannot silently certify.
    """

    allowed = frozenset(str(status) for status in statuses)
    raw: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    roles: dict[str, set[str]] = defaultdict(set)
    instrument_count = 0
    unrubricked = 0
    unservable = 0
    for item in sorted(vault.practice_items.values(), key=lambda entry: entry.id):
        if item.status not in allowed:
            continue
        # Before the rubric, so the buckets are disjoint and each means what it
        # says: an id here cannot reach a learner whatever its rubric compiles.
        if unservable_reason(item) is not None:
            unservable += 1
            continue
        observations = _item_observations(vault, item)
        if observations is None:
            unrubricked += 1
            continue
        instrument_count += 1
        for observation in observations:
            raw[observation.facet_id][observation.capability].add(item.id)
            roles[observation.facet_id].add(observation.role)
    return InstrumentPool(
        by_facet={
            facet: {
                capability: tuple(sorted(item_ids))
                for capability, item_ids in sorted(per_capability.items())
            }
            for facet, per_capability in sorted(raw.items())
        },
        roles_by_facet={facet: tuple(sorted(values)) for facet, values in sorted(roles.items())},
        instrument_count=instrument_count,
        unrubricked_item_count=unrubricked,
        unservable_item_count=unservable,
    )


# -- contract cells ------------------------------------------------------------


def contract_cells(vault: LoadedVault) -> tuple[tuple[ContractCell, ...], int]:
    """Every deduped contract cell in the vault, plus the advisory-component count.

    Deterministic: cells are sorted by (LO id, capability rank, capability, facet)
    and every accumulated tuple is sorted.
    """

    accumulated: dict[tuple[str, str, str], dict[str, set[str]]] = {}
    advisory = 0
    for learning_object_id in sorted(vault.learning_objects):
        lo = vault.learning_objects[learning_object_id]
        for blueprint in lo.blueprints:
            for recipe in blueprint.recipes:
                labelled = (
                    [("all_of", component) for component in recipe.all_of]
                    + [("any_of", component) for component in recipe.any_of]
                    + (
                        [("integration", recipe.integration)]
                        if recipe.integration is not None
                        else []
                    )
                )
                for role, component in labelled:
                    if str(component.modality) not in CONTRACT_MODALITIES:
                        advisory += 1
                        continue
                    key = (
                        lo.id,
                        vault.canonical_facet_id(str(component.facet)),
                        str(component.capability),
                    )
                    bucket = accumulated.setdefault(
                        key, {"roles": set(), "modalities": set(), "recipes": set()}
                    )
                    bucket["roles"].add(role)
                    bucket["modalities"].add(str(component.modality))
                    bucket["recipes"].add(f"{blueprint.id}:{recipe.id}")
    cells = tuple(
        sorted(
            (
                ContractCell(
                    learning_object_id=learning_object_id,
                    facet_id=facet_id,
                    capability=capability,
                    component_roles=tuple(sorted(bucket["roles"])),
                    modalities=tuple(sorted(bucket["modalities"])),
                    recipe_refs=tuple(sorted(bucket["recipes"])),
                )
                for (learning_object_id, facet_id, capability), bucket in accumulated.items()
            ),
            key=lambda cell: (
                cell.learning_object_id,
                CAPABILITY_RANK.get(cell.capability, len(CAPABILITY_RANK)),
                cell.capability,
                cell.facet_id,
            ),
        )
    )
    return cells, advisory


# -- the verdict ---------------------------------------------------------------


def classify_cell(
    required_capability: str,
    observed_capabilities: Iterable[str],
) -> ReachabilityVerdict:
    """The §5.8.2 verdict for one cell, given the capabilities its facet is observed at.

    Exact rules:

    * required capability outside the closed vocabulary -> ``INDETERMINATE``
      (abstain; the ladder comparison is undefined);
    * no observed capabilities at all -> ``NO_INSTRUMENT``;
    * the required capability is among them -> ``REACHABLE``;
    * else some observed capability ranks strictly HIGHER -> ``MISMATCH_ABOVE``
      (dominance could reach down to it);
    * else every observed capability ranks strictly LOWER -> ``MISMATCH_BELOW``.

    ``MISMATCH_ABOVE`` deliberately wins when a facet is observed both above and
    below the requirement: the cheap remedy (propagate what already exists)
    exists, and reporting it as a below-shortfall would send Stage 5 to author an
    instrument it does not need.
    """

    observed = tuple(str(capability) for capability in observed_capabilities)
    if required_capability not in CAPABILITY_RANK:
        return ReachabilityVerdict.INDETERMINATE
    if not observed:
        return ReachabilityVerdict.NO_INSTRUMENT
    if required_capability in observed:
        return ReachabilityVerdict.REACHABLE
    required_rank = CAPABILITY_RANK[required_capability]
    ranked = [CAPABILITY_RANK[capability] for capability in observed if capability in CAPABILITY_RANK]
    if any(rank > required_rank for rank in ranked):
        return ReachabilityVerdict.MISMATCH_ABOVE
    if any(rank < required_rank for rank in ranked):
        return ReachabilityVerdict.MISMATCH_BELOW
    # Observed only at capabilities outside the vocabulary: nothing comparable
    # observes this facet, so the honest answer is the no-instrument arm.
    return ReachabilityVerdict.NO_INSTRUMENT


def analyze_contract_reachability(
    vault: LoadedVault,
    *,
    statuses: Iterable[str] = INSTRUMENT_STATUSES,
) -> ContractReachabilityReport:
    """Static reachability report over a whole vault (§5.8.2).

    Deterministic and side-effect free: same vault content in, byte-identical
    report out. A vault with no blueprints yields ``cells == ()`` and a ``None``
    reachable share — an honest empty report, never a fake 100%.
    """

    pool = build_instrument_pool(vault, statuses=statuses)
    cells, advisory = contract_cells(vault)
    rows: list[CellReachability] = []
    for cell in cells:
        observed = pool.capabilities(cell.facet_id)
        verdict = classify_cell(cell.capability, observed)
        required_rank = CAPABILITY_RANK.get(cell.capability)
        below = [
            capability
            for capability in observed
            if required_rank is not None
            and CAPABILITY_RANK.get(capability, -1) < required_rank
        ]
        above = [
            capability
            for capability in observed
            if required_rank is not None
            and CAPABILITY_RANK.get(capability, len(CAPABILITY_RANK)) > required_rank
        ]
        rows.append(
            CellReachability(
                cell=cell,
                verdict=verdict,
                observed_capabilities=observed,
                matching_instrument_ids=pool.item_ids(cell.facet_id, cell.capability),
                instrument_ids=pool.item_ids(cell.facet_id),
                nearest_below=below[-1] if below else None,
                nearest_above=above[0] if above else None,
                observed_roles=tuple(pool.roles_by_facet.get(cell.facet_id, ())),
            )
        )
    declared = set(vault.evidence_facets)
    return ContractReachabilityReport(
        cells=tuple(rows),
        learning_object_count=len({cell.learning_object_id for cell in cells}),
        learning_objects_total=len(vault.learning_objects),
        instrument_count=pool.instrument_count,
        unrubricked_item_count=pool.unrubricked_item_count,
        unservable_item_count=pool.unservable_item_count,
        advisory_component_count=advisory,
        facets_declared=len(declared),
        # Registry-scoped: an observation of an unregistered facet is the
        # ``evidence_facet:unregistered`` doctor error's business, not a
        # measurement-rank numerator.
        facets_instrumented=len(declared & set(pool.by_facet)),
    )
