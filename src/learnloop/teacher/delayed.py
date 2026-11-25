"""Delayed cold and transfer checks (spec_teacher_v1 §13): code picks the items and the dates, never the model.

One mechanism (W13): DL2's Check once (``test_me_later`` commitments, the path
RW1b's reconstruct already uses), served cold in Today with no source, hint or
tutor; the answer is an ordinary attempt with full evidence and FSRS.

* **Retention:** one per landed node that has an LO: a vault item of that LO
  that was never attempted, has no reveal row from this lesson (nor exposure
  elsewhere reaching the auto-prime threshold: it could not be taken cold), was
  never shown in this lesson and shares no lineage with an item the lesson
  showed (its family, its contrast pair, its shared stimulus, its source
  exercise: §13's "a family the lesson didn't show"; review F7), is not
  withheld (exam, held-out, reserved, a pending check) and is servable (no
  lesson item: those stay in their lesson). An item the lesson "showed" is one
  whose question its displayed text reproduces (:func:`shown_vault_items`: a
  vault question reused as a check, or quoted in teaching).
* **Transfer:** one per lesson (§13; review F8), only where the relation is
  established: an item on an LO downstream of a landed one whose rubric
  measures a taught facet (a criterion's facet targets, else the item's
  facets, meet a landed LO's facets), else an item on a goal LO whose recorded
  presentation (``evidence_fingerprint.representation``) differs from that of
  every item the lesson showed and every check already picked. Otherwise the
  transfer check is reported unavailable, never filled by a look-alike.
* **The pick** among candidates is the item whose predicted success is nearest
  the middle of adaptive difficulty's band (the house pitch prior, §10 item 7).
  RW6b's valuation replaces this picker when it lands (one producer). The
  prediction is the item's own (data capture A6, mvp-0.44), and an exact tie is a
  uniform draw whose seed, draw and probability 1/n are on the check's receipt
  (:func:`pick_with_receipt`).
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

import re
from collections.abc import Iterable, Mapping, Sequence
from datetime import timedelta
from typing import Any

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.delayed_checks import PICK_VERSION, candidates, due_days, lineage, pick_with_receipt
from learnloop.delayed_checks import attempted_items as _attempted
from learnloop.delayed_checks import revealed_items as _revealed
from learnloop.teacher.brief import downstream_learning_objects

PURPOSES = ("retention", "transfer")
DEPTH_PRESET = "keep_in_touch"
VIA = "lesson"


def _bigrams(text: str) -> set[tuple[str, str]]:
    tokens = re.sub(r"[^\w]+", " ", str(text).lower()).split()
    return set(zip(tokens, tokens[1:], strict=False))


def question_overlap(shown: str, question: str) -> float:
    """The share of a question's word pairs (numbers kept: a matrix is part of the question) that the
    shown text contains, in 0..1: 1 for a question reproduced as it stands, near 0 for teaching that
    only shares its topic's vocabulary."""

    wanted = _bigrams(question)
    if not wanted:
        return 0.0
    return len(wanted & _bigrams(shown)) / len(wanted)


def shown_vault_items(vault: Any, texts: Iterable[str]) -> list[str]:
    """Vault items whose question the lesson's displayed text reproduces (a vault question reused as a
    check, or quoted in teaching), at the house exposure threshold (the auto-prime rule), in id order."""

    from learnloop.serve_eligibility import AUTO_PRIME_REVEAL_THRESHOLD

    shown = "\n".join(text for text in texts if text)
    if not shown.strip():
        return []
    out = []
    for item in sorted(vault.practice_items.values(), key=lambda value: value.id):
        extra = getattr(item.provenance, "model_extra", None) or {}
        if extra.get("mechanism") == "teacher_lesson_v1":
            continue
        if question_overlap(shown, str(item.prompt or "")) >= AUTO_PRIME_REVEAL_THRESHOLD:
            out.append(item.id)
    return out


def taught_facets(vault: Any, learning_object_ids: Iterable[str]) -> set[str]:
    from learnloop.vault.models import learning_object_facet_union

    out: set[str] = set()
    for lo in learning_object_ids:
        learning_object = vault.learning_objects.get(lo)
        if learning_object is not None:
            out |= {vault.canonical_facet_id(str(f)) for f in learning_object_facet_union(learning_object)}
    return out


def measures_facet(vault: Any, item: Any, facets: set[str]) -> bool:
    """Whether a criterion of the item's rubric measures one of ``facets`` (its targets, else the item's
    declared facets: KM §9.3's "a criterion that visibly exercises it")."""

    from learnloop.attempts.grading import resolved_rubric

    if not facets:
        return False
    fallback = {vault.canonical_facet_id(str(f)) for f in item.evidence_facets}
    try:
        rubric = resolved_rubric(vault, item)
    except Exception:  # noqa: BLE001 - an unreadable rubric establishes nothing
        return False
    for criterion in rubric.criteria:
        measured = ({vault.canonical_facet_id(str(t.facet)) for t in criterion.targets} if criterion.targets
                    else fallback)
        if measured & facets:
            return True
    return False


def presentation(item: Any) -> str | None:
    fingerprint = getattr(item, "evidence_fingerprint", None)
    value = getattr(fingerprint, "representation", None) if fingerprint is not None else None
    return str(value) if value else None


def pick(vault: Any, repository: Any, items: Sequence[Any], *, seed_key: str = "") -> Any | None:
    """The candidate pitched nearest the band's middle (the house prior); module docstring."""

    return pick_with_receipt(vault, repository, items, seed_key=seed_key)[0] if items else None


def retention_seed_key(lesson_id: str, learning_object_id: str, node_id: str | None = None) -> str:
    """The retention check's draw: its commit and the lesson forecast about it share it (§12.2). From the corrections'
    tag (mvp-0.73) each landed node's check has its own (``node_id``): two nodes on one LO sharing one draw would make the
    second pick a function of the first, its recorded propensity not its real one."""

    base = f"lesson:{lesson_id}:retention:{learning_object_id}"
    return base if node_id is None else f"{base}:node:{node_id}"


def node_seed(vault: Any, node_id: Any) -> str | None:
    """The node's identity in its retention seed from the corrections' tag (mvp-0.73); None below it."""

    from learnloop.algorithm_versions import forecast_scoring_fixed

    return str(node_id) if forecast_scoring_fixed(vault.config.algorithms.algorithm_version) else None


def commit_checks(vault: Any, repository: Any, *, lesson_id: str, landed: Sequence[Mapping[str, Any]],
                  goal_learning_object_ids: Sequence[str], lesson_items_by_lo: Mapping[str, Sequence[str]],
                  shown_items: Iterable[str], taught_learning_objects: Sequence[str] = (),
                  clock: Clock | None = None) -> tuple[list[dict[str, Any]], list[str]]:
    """Commit one retention check per landed node with an LO and one transfer check; returns
    ``(delayed_checks, warnings)`` for the receipt. ``shown_items``: the lesson's own check items and
    the vault items it showed (excluded with their lineage)."""

    from learnloop.curriculum import commitments as C
    from learnloop.learner_protection import withheld_items

    withheld = withheld_items(vault, repository)
    attempted, revealed = _attempted(repository), _revealed(repository, lesson_id)
    used: set[str] = set(shown_items)
    shown_vault = [vault.practice_items[i] for i in sorted(used) if i in vault.practice_items]
    shown_lineage: set[str] = set().union(*(lineage(item) for item in shown_vault)) if shown_vault else set()
    shown_presentations = {p for p in (presentation(item) for item in shown_vault) if p}
    out: list[dict[str, Any]] = []
    warnings: list[str] = []
    now = parse_utc(utc_now_iso(clock))
    assert now is not None
    plan: list[tuple[str, str | None, str, Any]] = []
    landed_los: list[str] = []
    item_picks: dict[str, dict[str, Any]] = {}

    def picked_for(found: Sequence[Any], seed_key: str) -> Any | None:
        """The pick among ``found``; its receipt is kept for the check's row."""

        item, receipt = pick_with_receipt(vault, repository, found, seed_key=seed_key)
        if item is not None:
            item_picks[item.id] = receipt
        return item

    for node in landed:
        lo = node.get("lo_id")
        if not lo or lo not in vault.learning_objects:
            continue
        landed_los.append(str(lo))
        item = picked_for(candidates(vault, repository, str(lo), exclude=used, withheld=withheld,
                                     attempted=attempted, revealed=revealed, excluded_lineage=shown_lineage),
                          retention_seed_key(lesson_id, str(lo), node_seed(vault, node.get("id"))))
        if item is None:
            warnings.append(f"no unseen question for a cold check on {lo}")
            plan.append(("retention", str(node.get("id")), str(lo), None))
            continue
        used.add(item.id)
        plan.append(("retention", str(node.get("id")), str(lo), item))
    if landed_los:
        transfer = None
        facets = taught_facets(vault, [*landed_los, *taught_learning_objects])
        picked = [entry[3] for entry in plan if entry[3] is not None]
        avoid = shown_presentations | {p for p in (presentation(item) for item in picked) if p}
        for lo in downstream_learning_objects(vault, landed_los):
            found = [item for item in candidates(vault, repository, lo, exclude=used, withheld=withheld,
                                                 attempted=attempted, revealed=revealed,
                                                 excluded_lineage=shown_lineage)
                     if measures_facet(vault, item, facets)]
            transfer = picked_for(found, f"lesson:{lesson_id}:transfer")
            if transfer is not None:
                break
        if transfer is None:
            picked_lineage = set().union(*(lineage(item) for item in picked)) if picked else set()
            for lo in goal_learning_object_ids:
                found = [item for item in candidates(vault, repository, lo, exclude=used, withheld=withheld,
                                                     attempted=attempted, revealed=revealed,
                                                     excluded_lineage=shown_lineage | picked_lineage)
                         if presentation(item) is not None and presentation(item) not in avoid]
                transfer = picked_for(found, f"lesson:{lesson_id}:transfer")
                if transfer is not None:
                    break
        if transfer is None:
            warnings.append("no question that applies what was taught in a new situation, so no transfer check")
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
        picked = {"pick": item_picks[item.id]} if item.id in item_picks else {}
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
                        "dated_by": basis, **picked},
            clock=clock,
        )
        out.append({"purpose": purpose, "node_id": node_id, "learning_object_id": lo, "item_id": item.id,
                    "commitment_id": commitment.id, "due": due, "dated_by": basis, "days": round(days, 3), **picked})
    return out, warnings


__all__ = ["PICK_VERSION", "PURPOSES", "candidates", "commit_checks", "due_days", "lineage", "measures_facet", "pick",
           "node_seed", "pick_with_receipt", "presentation", "retention_seed_key", "shown_vault_items", "taught_facets"]
