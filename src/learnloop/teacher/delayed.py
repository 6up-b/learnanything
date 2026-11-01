"""Delayed cold and transfer checks (spec_teacher_v1 §13): code picks the items and the dates, never the model.

One mechanism (W13): DL2's Check once (``test_me_later`` commitments, the path
RW1b's reconstruct already uses), served cold in Today with no source, hint or
tutor; the answer is an ordinary attempt with full evidence and FSRS.

* **Retention:** one per landed node that has an LO: a vault item of that LO
  that was never attempted, has no reveal row (from this lesson or any other),
  was never shown in this lesson, is not withheld (exam, held-out, reserved, a
  pending check) and is servable (no lesson item: those stay in their lesson).
* **Transfer:** one per lesson: such an item on an LO downstream of a landed one
  (one whose concept builds on it), else another of the goal's LOs' items not
  already picked.
* **The pick** among candidates is the item whose predicted success is nearest
  the middle of adaptive difficulty's band (the house pitch prior, §10 item 7),
  ties by id. RW6b's valuation replaces this picker when it lands (one producer).
* **Dates from retrievability** (owner, 2026-10-24): the first day the LO's
  predicted retrievability falls to ``R*`` (``teacher.delayed.target_retrievability``,
  a seeded prior, basis ``published``), by FSRS from the stability the lesson's
  own checks left on the LO; with no FSRS state, the seeded fallbacks (3 days for
  retention, 7 for transfer, basis ``legacy``); never later than
  ``teacher.delayed.max_wait_days`` (``keep``).
* **No fitting item:** recorded on the receipt as missing (the existing need step
  may generate one as an ordinary item); the teacher never authors its own.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import timedelta
from typing import Any

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.teacher.brief import downstream_learning_objects, lo_prediction

PURPOSES = ("retention", "transfer")
DEPTH_PRESET = "keep_in_touch"
VIA = "lesson"


def _attempted(repository: Any) -> set[str]:
    with repository.connection() as connection:
        return {str(row[0]) for row in connection.execute("SELECT DISTINCT practice_item_id FROM practice_attempts")}


def _revealed(repository: Any) -> set[str]:
    with repository.connection() as connection:
        return {str(row[0]) for row in connection.execute("SELECT DISTINCT practice_item_id FROM reveal_events")}


def candidates(vault: Any, repository: Any, learning_object_id: str, *, exclude: Iterable[str],
               withheld: Any, attempted: set[str], revealed: set[str]) -> list[Any]:
    """The candidate rule (§13 step 1) for one LO, in id order."""

    from learnloop.vault.lifecycle import practice_item_serving_block

    excluded = set(exclude)
    out = []
    for item in sorted(vault.practice_items.values(), key=lambda value: value.id):
        if item.learning_object_id != learning_object_id or item.id in excluded:
            continue
        if item.id in attempted or item.id in revealed:
            continue
        if withheld.reason(item.id) or practice_item_serving_block(vault, item) is not None:
            continue
        out.append(item)
    return out


def pick(vault: Any, repository: Any, items: Sequence[Any]) -> Any | None:
    """The candidate pitched nearest the band's middle (the house prior), ties by id."""

    if not items:
        return None
    band = tuple(getattr(vault.config.adaptive_difficulty, "practice_band", (0.70, 0.80)))
    middle = (float(band[0]) + float(band[1])) / 2.0

    def distance(item: Any) -> tuple[float, str]:
        p = lo_prediction(vault, repository, item.learning_object_id).get("p")
        return (abs(float(p) - middle) if p is not None else 1.0, item.id)

    return min(items, key=distance)


def due_days(vault: Any, repository: Any, *, purpose: str, lesson_item_ids: Sequence[str]) -> tuple[float, str]:
    """Days until the check is due, and how they were set (``retrievability`` or ``fallback``)."""

    from learnloop.scheduling.fsrs import interval_for_retention

    config = vault.config.teacher.delayed
    stabilities: list[float] = []
    if lesson_item_ids:
        marks = ",".join("?" for _ in lesson_item_ids)
        with repository.connection() as connection:
            stabilities = [float(row[0]) for row in connection.execute(
                f"SELECT stability FROM practice_item_state WHERE practice_item_id IN ({marks}) AND stability IS NOT NULL",
                list(lesson_item_ids))]
    if stabilities:
        days = interval_for_retention(max(stabilities), float(config.target_retrievability))
        basis = "retrievability"
    else:
        days = float(config.fallback_retention_days if purpose == "retention" else config.fallback_transfer_days)
        basis = "fallback"
    return min(max(days, 0.0), float(config.max_wait_days)), basis


def commit_checks(vault: Any, repository: Any, *, lesson_id: str, landed: Sequence[Mapping[str, Any]],
                  goal_learning_object_ids: Sequence[str], lesson_items_by_lo: Mapping[str, Sequence[str]],
                  shown_items: Iterable[str], clock: Clock | None = None) -> tuple[list[dict[str, Any]], list[str]]:
    """Commit one retention check per landed node with an LO and one transfer check; returns
    ``(delayed_checks, warnings)`` for the receipt."""

    from learnloop.curriculum import commitments as C
    from learnloop.learner_protection import withheld_items

    withheld = withheld_items(vault, repository)
    attempted, revealed = _attempted(repository), _revealed(repository)
    used: set[str] = set(shown_items)
    out: list[dict[str, Any]] = []
    warnings: list[str] = []
    now = parse_utc(utc_now_iso(clock))
    assert now is not None
    plan: list[tuple[str, str | None, str, Any]] = []
    landed_los: list[str] = []
    for node in landed:
        lo = node.get("lo_id")
        if not lo or lo not in vault.learning_objects:
            continue
        landed_los.append(str(lo))
        item = pick(vault, repository, candidates(vault, repository, str(lo), exclude=used, withheld=withheld,
                                                  attempted=attempted, revealed=revealed))
        if item is None:
            warnings.append(f"no unseen question for a cold check on {lo}")
            plan.append(("retention", str(node.get("id")), str(lo), None))
            continue
        used.add(item.id)
        plan.append(("retention", str(node.get("id")), str(lo), item))
    if landed_los:
        transfer = None
        for lo in [*downstream_learning_objects(vault, landed_los), *goal_learning_object_ids]:
            transfer = pick(vault, repository, candidates(vault, repository, lo, exclude=used, withheld=withheld,
                                                          attempted=attempted, revealed=revealed))
            if transfer is not None:
                break
        if transfer is None:
            warnings.append("no unseen question for a transfer check")
            plan.append(("transfer", None, landed_los[0], None))
        else:
            used.add(transfer.id)
            plan.append(("transfer", None, transfer.learning_object_id, transfer))
    for purpose, node_id, lo, item in plan:
        if item is None:
            out.append({"purpose": purpose, "node_id": node_id, "learning_object_id": lo, "item_id": None,
                        "commitment_id": None, "due": None, "missing": True})
            continue
        days, basis = due_days(vault, repository, purpose=purpose,
                               lesson_item_ids=list(lesson_items_by_lo.get(lo, ())))
        due = (now + timedelta(days=days)).strftime("%Y-%m-%d")
        commitment = C.create_commitment(
            repository,
            action="test_me_later",
            intent_text=f"one question on your own after a lesson ({purpose})",
            targets=[{"target_kind": "legacy_practice_item", "target_ref": item.id, "role": "required"}],
            depth_preset=DEPTH_PRESET,
            client_idempotency_key=f"lesson:{lesson_id}:{purpose}:{node_id or 'lesson'}",
            due_hint=due,
            reason=f"lesson_{purpose}_check",
            provenance={"via": VIA, "lesson_id": lesson_id, "node_id": node_id, "purpose": purpose,
                        "dated_by": basis},
            clock=clock,
        )
        out.append({"purpose": purpose, "node_id": node_id, "learning_object_id": lo, "item_id": item.id,
                    "commitment_id": commitment.id, "due": due, "dated_by": basis, "days": round(days, 3)})
    return out, warnings


__all__ = ["PURPOSES", "candidates", "commit_checks", "due_days", "pick"]
