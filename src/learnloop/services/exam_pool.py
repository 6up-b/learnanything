"""Exam pool: reserve existing items for a goal's held-out practice exam.

A goal's exam is a *held-out* test — items the learner has never practiced, set
aside so ordinary practice cannot contaminate them before the exam measures
whether the mastery model's projections were true. This module reserves those
items (``reserve_exam_pool``), quarantines them from the scheduler
(``reserved_item_ids`` — the scheduler skips them), and releases them back into
practice once the exam is finished (``release_exam_pool``).

Selection blueprint (``reserve_exam_pool``), all deterministic given DB state:

  * **Scope coverage** — cover the goal's scope facets (``resolve_goal_scope``).
    Greedy: each pick maximizes newly covered scope facets.
  * **Never attempted** — only items with zero recorded attempts are reservable
    (a practiced item is not held-out).
  * **At most one unreleased pool** — an item already reserved for another goal
    is not reservable (enforced by a partial unique index too).
  * **Stratified across difficulty** — ties prefer a difficulty stratum not yet
    represented in the reservation, so the exam spans easy/medium/hard.
  * **Novel surface families** — ties prefer a ``surface_family`` distinct from
    the items the learner has already practiced, so the exam is genuinely
    transfer, not a restatement of drilled surfaces.

``uncovered_facets`` reports scope facets that no reservable item can test — a
content gap to surface to the learner (they cannot be examined on it yet).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from learnloop.clock import Clock, SystemClock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.goal_projection import resolve_goal_scope
from learnloop.vault.models import Goal, LoadedVault, PracticeItem

# Difficulty strata for stratification (item.difficulty is a 0..1 prior).
_DIFFICULTY_STRATA = ("low", "mid", "high", "unknown")


def _difficulty_stratum(item: PracticeItem) -> str:
    difficulty = item.difficulty
    if difficulty is None:
        return "unknown"
    if difficulty < 0.34:
        return "low"
    if difficulty < 0.67:
        return "mid"
    return "high"


@dataclass(frozen=True)
class _Candidate:
    item_id: str
    facets: frozenset[str]      # canonical scope facets this item can test
    stratum: str
    surface_family: str | None
    novel_surface: bool         # surface_family unseen among practiced items


@dataclass(frozen=True)
class ExamPoolReport:
    goal_id: str
    reserved_item_ids: list[str]
    covered_facets: list[str]
    uncovered_facets: list[str]
    requested_item_count: int
    strata: dict[str, int]
    already_reserved: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "reserved_item_ids": list(self.reserved_item_ids),
            "covered_facets": list(self.covered_facets),
            "uncovered_facets": list(self.uncovered_facets),
            "requested_item_count": self.requested_item_count,
            "strata": dict(self.strata),
            "already_reserved": self.already_reserved,
        }


def reserved_item_ids(repository: Repository) -> set[str]:
    """All practice item ids currently reserved (unreleased) across all goals.

    The scheduler calls this once per build to skip reserved items so a held-out
    exam pool cannot leak into ordinary practice.
    """

    return repository.reserved_exam_pool_item_ids()


def release_exam_pool(repository: Repository, goal_id: str, *, clock: Clock | None = None) -> list[str]:
    """Release every unreleased reservation for ``goal_id``.

    Returns the freed practice item ids. Idempotent: a second call finds nothing
    unreleased and returns ``[]``.
    """

    return repository.release_exam_pool(goal_id, clock=clock)


def reserve_exam_pool(
    vault: LoadedVault,
    repository: Repository,
    goal: Goal,
    *,
    item_count: int | None = None,
    clock: Clock | None = None,
) -> ExamPoolReport:
    """Reserve up to ``item_count`` held-out items covering the goal's scope.

    Idempotent per goal: if the goal already has an unreleased reservation, the
    existing reservation is returned unchanged (``already_reserved=True``).
    """

    clock = clock or SystemClock()
    now_iso = utc_now_iso(clock)
    requested = int(item_count if item_count is not None else goal.exam.item_count)

    scope = resolve_goal_scope(vault, goal, repository)
    scope_facets = set().union(*scope.values()) if scope else set()

    existing = repository.reserved_exam_pool_items(goal.id)
    own_reserved_ids = {row["practice_item_id"] for row in existing}

    candidates = _candidates(vault, repository, scope, own_reserved_ids)
    coverable = set().union(*(candidate.facets for candidate in candidates)) if candidates else set()
    uncovered = sorted(scope_facets - coverable)

    if existing:
        # Idempotent re-call: return the standing reservation unchanged.
        reserved = [row["practice_item_id"] for row in existing]
        covered = sorted(
            {facet for candidate in candidates if candidate.item_id in own_reserved_ids for facet in candidate.facets}
        )
        strata: dict[str, int] = {}
        for row in existing:
            stratum = str(row.get("difficulty_stratum") or "unknown")
            strata[stratum] = strata.get(stratum, 0) + 1
        return ExamPoolReport(
            goal_id=goal.id,
            reserved_item_ids=reserved,
            covered_facets=covered,
            uncovered_facets=uncovered,
            requested_item_count=requested,
            strata=strata,
            already_reserved=True,
        )

    selected = _select(candidates, requested)
    # Dual-authority mutual exclusion (design §A.2 rule 3), asserted at reserve time:
    # _candidates already dropped staged-owned items, so a hit here means a staged
    # ownership assignment raced the reservation -- refuse with a typed error rather than
    # quarantine a staged-owned item into a held-out pool.
    from learnloop.services.controller_ownership import staged_owned_practice_item_ids

    _staged_owned = staged_owned_practice_item_ids(vault, repository)
    _conflict = {candidate.item_id for candidate in selected} & _staged_owned
    if _conflict:
        from learnloop.services.controller_ownership import ExamReservationOwnershipConflict

        raise ExamReservationOwnershipConflict(
            f"exam reservation for goal {goal.id} would cover staged-owned items: "
            f"{sorted(_conflict)}"
        )
    covered = sorted({facet for candidate in selected for facet in candidate.facets})
    strata = {}
    for candidate in selected:
        strata[candidate.stratum] = strata.get(candidate.stratum, 0) + 1

    rows = [
        {
            "id": new_ulid(),
            "goal_id": goal.id,
            "practice_item_id": candidate.item_id,
            "facet_id": next(iter(sorted(candidate.facets)), None),
            "difficulty_stratum": candidate.stratum,
            "reserved_at": now_iso,
            "released_at": None,
        }
        for candidate in selected
    ]
    if rows:
        repository.insert_exam_pool_items(rows)

    # P0.4 §3.4 pin wiring: when the goal has a CONFIRMED terminal contract, dual-write
    # an activity_surface_reservation carrying target_contract_version_id +
    # target_support_hash (the 065 columns) alongside the legacy exam_pool_items,
    # so the assessment reserve pins the exact version + support hash at reservation.
    # Fully inert for unconfirmed goals (legacy exam path unchanged).
    from learnloop.services.goal_contracts import resolve_head

    head = resolve_head(repository, goal.id)
    if head is not None:
        from learnloop.services.activities import (
            SurfaceAlreadyReserved,
            reserve_surface,
            resolve_legacy_item,
        )

        for candidate in selected:
            item = vault.practice_items.get(candidate.item_id)
            if item is None:
                continue
            resolved = resolve_legacy_item(
                vault, repository, item, purpose="assessment", clock=clock
            )
            try:
                reserve_surface(
                    repository,
                    surface_id=resolved.surface_id,
                    purpose="assessment",
                    goal_id=goal.id,
                    target_contract_version_id=head.id,
                    target_support_hash=head.support_hash,
                    clock=clock,
                )
            except SurfaceAlreadyReserved:
                continue

    return ExamPoolReport(
        goal_id=goal.id,
        reserved_item_ids=[candidate.item_id for candidate in selected],
        covered_facets=covered,
        uncovered_facets=uncovered,
        requested_item_count=requested,
        strata=strata,
        already_reserved=False,
    )


def _candidates(
    vault: LoadedVault,
    repository: Repository,
    scope: dict[str, set[str]],
    own_reserved_ids: set[str],
) -> list[_Candidate]:
    """Reservable items: active, never attempted, not reserved elsewhere.

    ``own_reserved_ids`` (this goal's standing reservation) are treated as
    reservable so the idempotent branch can recompute their facet coverage.
    """

    attempted = repository.attempted_practice_item_ids()
    reserved_elsewhere = repository.reserved_exam_pool_item_ids() - own_reserved_ids
    item_states = repository.practice_item_states()
    practiced_surfaces = _practiced_surface_families(vault, attempted)
    # P4 §14.2 step 3 dual-authority (design §A.2 rule 3): the held-out exam is an
    # administration surface. A staged-owned P2 commitment's items are never reservable --
    # exam reservation and staged ownership are mutually exclusive. Empty (no-op) for a
    # vault with no ownership rows, so the legacy exam pool is byte-identical.
    from learnloop.services import controller_ownership as _ownership

    staged_owned = _ownership.staged_owned_practice_item_ids(vault, repository)

    candidates: list[_Candidate] = []
    for item in vault.practice_items.values():
        if item.status != "active":
            continue
        scope_facets = scope.get(item.learning_object_id)
        if not scope_facets:
            continue
        if item.id in attempted or item.id in reserved_elsewhere:
            continue
        if item.id in staged_owned:
            continue
        state = item_states.get(item.id)
        if state is not None and not state.active:
            continue
        item_facets = {vault.canonical_facet_id(str(facet)) for facet in item.evidence_facets}
        covered = item_facets & scope_facets
        if not covered:
            continue
        candidates.append(
            _Candidate(
                item_id=item.id,
                facets=frozenset(covered),
                stratum=_difficulty_stratum(item),
                surface_family=item.surface_family,
                novel_surface=item.surface_family is not None
                and item.surface_family not in practiced_surfaces,
            )
        )
    return candidates


def _practiced_surface_families(vault: LoadedVault, attempted: set[str]) -> set[str]:
    families: set[str] = set()
    for item_id in attempted:
        item = vault.practice_items.get(item_id)
        if item is not None and item.surface_family is not None:
            families.add(item.surface_family)
    return families


def _select(candidates: list[_Candidate], item_count: int) -> list[_Candidate]:
    """Greedy scope-coverage selection with stratification + surface novelty.

    Deterministic: each pick maximizes newly covered scope facets; ties break to
    a novel surface family, then an under-represented difficulty stratum, then a
    novel surface family value, then item id.
    """

    if item_count <= 0:
        return []
    remaining = list(candidates)
    selected: list[_Candidate] = []
    covered: set[str] = set()
    stratum_counts: dict[str, int] = {}
    used_surfaces: set[str] = set()

    while remaining and len(selected) < item_count:
        def sort_key(candidate: _Candidate) -> tuple:
            new_facets = len(candidate.facets - covered)
            surface_new = (
                candidate.surface_family is not None and candidate.surface_family not in used_surfaces
            )
            return (
                -new_facets,
                0 if candidate.novel_surface else 1,
                stratum_counts.get(candidate.stratum, 0),
                0 if surface_new else 1,
                candidate.item_id,
            )

        remaining.sort(key=sort_key)
        pick = remaining.pop(0)
        selected.append(pick)
        covered |= pick.facets
        stratum_counts[pick.stratum] = stratum_counts.get(pick.stratum, 0) + 1
        if pick.surface_family is not None:
            used_surfaces.add(pick.surface_family)
    return selected
