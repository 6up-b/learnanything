"""The one "Check once" feasibility gate (DL2 fix round 6, orchestrator ruling).

Every candidate of a due "Check once" passes :meth:`CheckGate.refusal` before
it can be selected (``split_check``, then ``pick_checks``) or forced into a
plan's first block, under every plan policy: the staged frame, the mixture
and DL1's pair alike. A check is exempt from value and count composition
(round 4), never from a mandatory constraint. The gate refuses, in this order
(the first refusal is the candidate's reason):

1. ``held_out_material``: an item made from held-out material, ALWAYS
   (verify F18). ``goals.held_out_selection`` keeps governing ordinary serving
   exactly as before (``serving_exclusions.routine_serving_exclusions``); a
   check is a measurement, and held-out material is the exam's.
2. ``assessment_reservation``: a surface holding a live assessment
   reservation (``activity_surface_reservations``; F16).
3. ``exam_pool``: an item reserved in an exam pool.
4. ``build_admission``: the build's one admission predicate (round 3, R1),
   with its reason (``scheduler.admission_reason``).
5. The staged frame's mandatory constraints (``frame_constraints``), evaluated
   here even when the plan's own policy is DL1's pair, purely as a check gate
   (verify F19): ``hard_exposure_collision`` and the rest, with the
   constraint's own key. Nothing else changes under DL1's pair.

A read that fails refuses every candidate (``constraints_unavailable``,
``detail.input`` naming the failing input: one of the three protected sets,
``build_admission`` or ``staged_frame``; round 7, F22): fail closed, as the
frame does. Each refusal is kept on the check
(``CheckState.refused``), so a due check is either planned or recorded with
its candidates' reasons (verify F20).

Only due checks' candidates are ever evaluated: non-check items and vaults with
no due check never reach the gate.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Any

from learnloop.content.sources import exam_material as EM
from learnloop.goals import exam_pool

_LOG = logging.getLogger(__name__)

SOURCE = "check_gate"
HELD_OUT_KEY = "held_out_material"
ASSESSMENT_RESERVATION_KEY = "assessment_reservation"
EXAM_POOL_KEY = "exam_pool"
ADMISSION_KEY = "build_admission"
UNAVAILABLE_KEY = "constraints_unavailable"
#: The input name of the staged frame's evaluation in an unavailable refusal.
FRAME_INPUT = "staged_frame"
#: The frame's maintain block budget (``daily_plan.types.BLOCK_MAX_MINUTES``).
_BLOCK_MINUTES = 15.0


def _refusal(key: str, reason: str, **detail: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"constraint_key": key, "reason": reason, "source": SOURCE}
    if detail:
        out["detail"] = detail
    return out


def reserved_assessment_items(repository: Any) -> frozenset[str]:
    """The practice items whose surface holds a live assessment reservation
    (the staged frame's own read)."""

    return frozenset(
        str(row["legacy_practice_item_id"])
        for row in repository.reserved_assessment_surfaces()
        if row.get("legacy_practice_item_id")
    )


class CheckGate:
    """The gate for one intent view: each read once, on first use; the frame's
    evaluation once, over every due check's candidates together."""

    def __init__(
        self,
        vault: Any,
        repository: Any,
        *,
        now: datetime,
        admission: Callable[[str], Any] | None,
        candidate_ids: Iterable[str],
    ) -> None:
        self.vault = vault
        self.repository = repository
        self.now = now
        self.admission = admission
        self.candidate_ids = tuple(dict.fromkeys(candidate_ids))
        self._sets: dict[str, frozenset[str]] = {}
        #: ``{input: error}`` for each protected set that could not be read.
        self._sets_errors: dict[str, str] = {}
        self._frame: dict[str, tuple[dict[str, Any], ...]] | None = None
        self._frame_error: str | None = None

    # -- the reads ------------------------------------------------------------

    def _protected(self, key: str) -> frozenset[str] | None:
        """One protected set, read once; None when it could not be read
        (round 7, F22: each input fails closed under its own name)."""

        if key not in self._sets and key not in self._sets_errors:
            readers = {
                HELD_OUT_KEY: lambda: EM.held_out_items(self.vault, self.repository),
                ASSESSMENT_RESERVATION_KEY: lambda: reserved_assessment_items(self.repository),
                EXAM_POOL_KEY: lambda: exam_pool.reserved_item_ids(self.repository),
            }
            try:
                self._sets[key] = frozenset(str(item_id) for item_id in readers[key]())
            except Exception as exc:  # noqa: BLE001 - fail closed: no candidate passes
                _LOG.warning("check gate: %s could not be read; every candidate is refused", key, exc_info=True)
                self._sets_errors[key] = type(exc).__name__
        return self._sets.get(key)

    def _frame_refusals(self) -> dict[str, tuple[dict[str, Any], ...]]:
        if self._frame is None:
            from learnloop.clock import FrozenClock
            from learnloop.scheduling import controller_actions as A
            from learnloop.scheduling.frame_constraints import (
                ROLE_FRESH_EVIDENCE,
                GateItem,
                attention_block,
                evaluate_mandatory,
            )

            items = []
            for item_id in self.candidate_ids:
                practice_item = self.vault.practice_items.get(item_id)
                if practice_item is None:
                    continue
                learning_object = self.vault.learning_object_for_item(practice_item)
                items.append(
                    GateItem(
                        practice_item_id=item_id,
                        learning_object_id=learning_object.id if learning_object is not None else "",
                        est_minutes=float(getattr(practice_item, "expected_minutes", None) or 0.0),
                    )
                )

            def block_for(item: Any, role: str) -> Any:
                # The block the frame evaluates a check in: a fresh-evidence
                # item in a diagnostic block, any other in its lane (maintain).
                if role == ROLE_FRESH_EVIDENCE:
                    return attention_block(A.MEASURE_DIAGNOSTIC, None, budget_minutes=_BLOCK_MINUTES,
                                           source=SOURCE, lane=item.lane)
                return attention_block(A.MAINTAIN, None, budget_minutes=_BLOCK_MINUTES, source=SOURCE,
                                       lane=item.lane)

            evaluation = evaluate_mandatory(
                self.vault, self.repository, items, clock=FrozenClock(self.now), block_for=block_for,
                log_prefix="check gate",
            )
            self._frame = dict(evaluation.refusals)
        return self._frame

    # -- the gate -------------------------------------------------------------

    def refusal(self, item_id: str) -> dict[str, Any] | None:
        """Why ``item_id`` can never be a check's item now, or None."""

        if item_id not in self.vault.practice_items:
            return _refusal(ADMISSION_KEY, "unknown_item")
        for key in (HELD_OUT_KEY, ASSESSMENT_RESERVATION_KEY, EXAM_POOL_KEY):
            found = self._protected(key)
            if found is None:
                return _refusal(UNAVAILABLE_KEY, f"{key}_unreadable", input=key, error=self._sets_errors[key])
            if item_id in found:
                return _refusal(key, key)
        if self.admission is not None:
            try:
                verdict = self.admission(item_id)
            except Exception as exc:  # noqa: BLE001 - fail closed (round 7, F22)
                _LOG.warning("check gate: the admission predicate failed for %s; refused", item_id, exc_info=True)
                return _refusal(UNAVAILABLE_KEY, f"{ADMISSION_KEY}_unreadable", input=ADMISSION_KEY,
                                error=type(exc).__name__)
            if verdict is False:
                return _refusal(ADMISSION_KEY, "not_admitted")
            if isinstance(verdict, str):
                return _refusal(ADMISSION_KEY, verdict)
        if self._frame_error is None:
            try:
                frame = self._frame_refusals()
            except Exception as exc:  # noqa: BLE001 - fail closed
                _LOG.warning("check gate: the frame's constraints could not be evaluated", exc_info=True)
                self._frame_error = type(exc).__name__
        if self._frame_error is not None:
            return _refusal(UNAVAILABLE_KEY, "staged_frame_unreadable", input=FRAME_INPUT, error=self._frame_error)
        reasons = frame.get(item_id)
        if reasons:
            first = dict(reasons[0])
            return {
                "constraint_key": str(first.get("constraint_key") or UNAVAILABLE_KEY),
                "reason": str(first.get("reason") or ""),
                "source": SOURCE,
                "refusals": [dict(reason) for reason in reasons],
            }
        return None


__all__ = [
    "ADMISSION_KEY",
    "ASSESSMENT_RESERVATION_KEY",
    "CheckGate",
    "EXAM_POOL_KEY",
    "HELD_OUT_KEY",
    "UNAVAILABLE_KEY",
    "reserved_assessment_items",
]
