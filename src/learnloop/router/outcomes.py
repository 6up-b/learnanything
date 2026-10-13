"""Router R1: ``router_outcomes`` (DERIVED, one replayer) per logged decision.

The Pipeline plan's outcome (``docs/brainstorming/Pipeline Augmentation
Plan.md``, "Outcome and cost contract"):

    S = alpha R_cold + (1 - alpha) R_next,   alpha = 0.75

* ``R_next``: success on the first fresh, unassisted, independently attempted
  item on the decision's learning object after the action. Fresh = a different
  item from the action's; unassisted = no hints, not primed; independent = an
  independent attempt type, human origin, a scorable resolved grade (PF-c
  nothing-assessed answers excluded), the outcome contract's own rules
  (``outcome_contract.retention_exclusions``) minus its delay rules.
* ``R_cold``: success on the next eligible delayed cold retrieval on that
  learning object under the reveal ledger: an attempt at least one day after
  the last exposure to the learning object, where an exposure is any attempt on
  it or any reveal on the item or the learning object (``reveal_events``), in
  a different session from that last attempt, and unassisted as above.

The action is the decision's chosen candidate. A Today offer's head is taken
when an attempt is bound to its scheduler candidate; a learner pick's when an
attempt is bound to the picked candidate; a staged decision's when its chosen
item is attempted at or after the decision in its session. An untaken head is
``overridden`` (a learner pick from the same offer), ``superseded`` (a later
decision in its session), ``not_taken`` (its session ended) or ``open``. An
outcome with no eligible attempt yet is ``pending``: right-censored at
``observed_through`` (the newest attempt in the ledger), never a failure.
Values are the attempt's ``correctness`` in [0, 1].

``S`` follows the plan's rule that R_next makes it provisional and only R_cold
finalizes it. An observed R_cold makes ``S`` final: with the R_next observed at
or before the cold attempt, ``S = 0.75 R_cold + 0.25 R_next``; with none, the
R_next window is closed (``not_applicable``, ``closed_by_r_cold``: a "next"
attempt after the cold retrieval is not immediate uptake) and ``S = R_cold``.
So a final ``S`` never moves. R_next is also ``not_applicable`` when the
learning object has no other servable item (``no_other_servable_item``): it
could never be observed, so it is not reported as pending forever.

Deterministic from ledgers (``router_decisions``, ``practice_attempts``,
grading evidence through the caller's PF-c states, ``reveal_events``,
``sessions.ended_at``) and the caller's map of servable items per learning
object (vault content): no clock, no model call. It imports no scheduler or
substrate code.
"""
from __future__ import annotations

from bisect import bisect_right
from collections import defaultdict
from collections.abc import Mapping
import json
import sqlite3
from typing import Any

from learnloop.clock import parse_utc
from learnloop.db.stores.router import replace_router_outcomes
from learnloop.outcome_contract import RETENTION_MIN_DELAY_SECONDS, retention_exclusions

OUTCOME_VERSION = "router_outcomes_v1"

#: The Pipeline plan's declared policy weight on durable retrieval.
S_ALPHA = 0.75

#: Attempt types that count as an independent attempt for R_next and R_cold.
INDEPENDENT_ATTEMPT_TYPES: frozenset[str] = frozenset(
    {"independent_attempt", "dont_know", "diagnostic_probe", "open_text", "exam_attempt"}
)

#: The outcome contract's delay rules, which R_next does not apply.
_DELAY_REASONS = frozenset({"insufficient_delay", "same_session", "intervening_practice"})

_ATTEMPT_COLUMNS = (
    "id, practice_item_id, learning_object_id, session_id, created_at, "
    "scheduler_candidate_id, attempt_type, hints_used, primed, correctness, "
    "manual_review, manual_review_reason, evidence_origin"
)


def _seconds(later: str, earlier: str) -> int | None:
    late, early = parse_utc(later), parse_utc(earlier)
    if late is None or early is None:
        return None
    return int((late - early).total_seconds())


def _exclusions(
    attempt: Mapping[str, Any],
    *,
    elapsed_seconds: int | None,
    source_session_id: str | None,
    pfc_states: Mapping[str, str],
) -> list[str]:
    reasons = retention_exclusions(
        {
            "label_value": attempt["correctness"],
            "elapsed_seconds": elapsed_seconds,
            "outcome_hints_used": attempt["hints_used"],
            "outcome_primed": attempt["primed"],
            "outcome_manual_review": attempt["manual_review"],
            "outcome_manual_review_reason": attempt["manual_review_reason"],
            "outcome_pfc_assessment": pfc_states.get(attempt["id"]),
            "source_session_id": source_session_id,
            "outcome_session_id": attempt["session_id"],
            "intervening_attempt_count": 0,
        }
    )
    if attempt["attempt_type"] not in INDEPENDENT_ATTEMPT_TYPES:
        reasons.append("not_independent_type")
    if attempt["evidence_origin"] != "human":
        reasons.append("non_human_outcome")
    return reasons


class _Ledger:
    """The attempt and reveal ledgers, indexed once for every decision."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        attempts = [
            dict(row)
            for row in connection.execute(
                f"SELECT {_ATTEMPT_COLUMNS} FROM practice_attempts ORDER BY created_at, id"
            )
        ]
        self.by_id = {row["id"]: row for row in attempts}
        self.by_lo: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.position: dict[str, int] = {}
        self.by_candidate: dict[str, dict[str, Any]] = {}
        self.by_item: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in attempts:
            lo_rows = self.by_lo[row["learning_object_id"]]
            self.position[row["id"]] = len(lo_rows)
            lo_rows.append(row)
            self.by_item[row["practice_item_id"]].append(row)
            candidate = row.get("scheduler_candidate_id")
            if candidate and candidate not in self.by_candidate:
                self.by_candidate[candidate] = row
        self.observed_through = attempts[-1]["created_at"] if attempts else None
        reveals: dict[tuple[str, str], list[str]] = defaultdict(list)
        has_reveals = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='reveal_events'"
        ).fetchone()
        if has_reveals:
            for row in connection.execute(
                "SELECT practice_item_id, learning_object_id, created_at FROM reveal_events ORDER BY created_at, id"
            ):
                if row["practice_item_id"]:
                    reveals[("item", row["practice_item_id"])].append(row["created_at"])
                if row["learning_object_id"]:
                    reveals[("lo", row["learning_object_id"])].append(row["created_at"])
        self.reveals = reveals

    def last_reveal(self, item_id: str, learning_object_id: str, until: str) -> str | None:
        """The newest reveal on the item or its learning object at or before ``until``."""

        latest = None
        for key in (("item", item_id), ("lo", learning_object_id)):
            times = self.reveals.get(key) or []
            index = bisect_right(times, until)
            if index:
                candidate = times[index - 1]
                if latest is None or candidate > latest:
                    latest = candidate
        return latest


def _action_attempt(decision: Mapping[str, Any], ledger: _Ledger) -> dict[str, Any] | None:
    candidate = decision.get("chosen_scheduler_candidate_id")
    if candidate:
        return ledger.by_candidate.get(candidate)
    item_id = decision.get("chosen_practice_item_id")
    if not item_id:
        return None
    for row in ledger.by_item.get(item_id, []):
        if row["created_at"] < decision["created_at"]:
            continue
        if decision.get("session_id") and row["session_id"] != decision["session_id"]:
            continue
        return row
    return None


def servable_items_by_learning_object(vault: Any) -> dict[str, set[str]]:
    """Each learning object's active, servable practice items (vault content).

    R_next needs a different item on the action's learning object; where there
    is none it is ``not_applicable``. Retired items and ephemeral dialogue-turn
    microprobes are never served.
    """

    by_lo: dict[str, set[str]] = defaultdict(set)
    for item in getattr(vault, "practice_items", {}).values():
        if getattr(item, "status", "active") != "active":
            continue
        if getattr(item, "practice_mode", None) == "diagnostic_microprobe":
            continue
        learning_object_id = getattr(item, "learning_object_id", None)
        if learning_object_id:
            by_lo[learning_object_id].add(item.id)
    return dict(by_lo)


def _r_next(
    action: Mapping[str, Any],
    ledger: _Ledger,
    pfc_states: Mapping[str, str],
    *,
    until_position: int | None = None,
) -> dict[str, Any]:
    """The first fresh, unassisted, independent attempt after the action, at or
    before ``until_position`` (the R_cold attempt) when one is given."""

    rows = ledger.by_lo[action["learning_object_id"]]
    end = len(rows) if until_position is None else until_position + 1
    skipped: dict[str, int] = defaultdict(int)
    for row in rows[ledger.position[action["id"]] + 1:end]:
        if row["practice_item_id"] == action["practice_item_id"]:
            skipped["not_fresh_same_item"] += 1
            continue
        reasons = [
            reason
            for reason in _exclusions(row, elapsed_seconds=None, source_session_id=None, pfc_states=pfc_states)
            if reason not in _DELAY_REASONS
        ]
        if reasons:
            for reason in reasons:
                skipped[reason] += 1
            continue
        return {
            "status": "observed",
            "value": float(row["correctness"]),
            "attempt_id": row["id"],
            "elapsed_seconds": _seconds(row["created_at"], action["created_at"]),
            "skipped": skipped,
        }
    return {"status": "pending", "value": None, "attempt_id": None, "elapsed_seconds": None, "skipped": skipped}


def _r_cold(action: Mapping[str, Any], ledger: _Ledger, pfc_states: Mapping[str, str]) -> dict[str, Any]:
    learning_object_id = action["learning_object_id"]
    rows = ledger.by_lo[learning_object_id]
    start = ledger.position[action["id"]]
    skipped: dict[str, int] = defaultdict(int)
    for index in range(start + 1, len(rows)):
        row = rows[index]
        previous = rows[index - 1]
        last_exposure = previous["created_at"]
        reveal = ledger.last_reveal(row["practice_item_id"], learning_object_id, row["created_at"])
        if reveal is not None and reveal > last_exposure:
            last_exposure = reveal
        gap = _seconds(row["created_at"], last_exposure)
        reasons = _exclusions(
            row,
            elapsed_seconds=gap,
            source_session_id=previous["session_id"],
            pfc_states=pfc_states,
        )
        if reasons:
            for reason in reasons:
                skipped[reason] += 1
            continue
        return {
            "status": "observed",
            "value": float(row["correctness"]),
            "attempt_id": row["id"],
            "gap_seconds": gap,
            "position": index,
            "skipped": skipped,
        }
    return {
        "status": "pending", "value": None, "attempt_id": None, "gap_seconds": None, "position": None,
        "skipped": skipped,
    }


def _not_applicable(decision: Mapping[str, Any], status: str, observed_through: str | None, *, pending: bool) -> dict[str, Any]:
    outcome = "pending" if pending else "not_applicable"
    return {
        "decision_id": decision["id"],
        "outcome_version": OUTCOME_VERSION,
        "target_practice_item_id": decision.get("chosen_practice_item_id"),
        "target_learning_object_id": decision.get("chosen_learning_object_id"),
        "action_status": status,
        "action_attempt_id": None,
        "r_next_status": outcome,
        "r_next_value": None,
        "r_next_attempt_id": None,
        "r_next_elapsed_seconds": None,
        "r_next_skipped": 0,
        "r_cold_status": outcome,
        "r_cold_value": None,
        "r_cold_attempt_id": None,
        "r_cold_gap_seconds": None,
        "r_cold_skipped": 0,
        "s_status": outcome,
        "s_value": None,
        "s_alpha": S_ALPHA,
        "observed_through": observed_through,
        "detail_json": json.dumps({"basis": OUTCOME_VERSION}, sort_keys=True),
    }


def _ended_sessions(connection: sqlite3.Connection, session_ids: set[str]) -> set[str]:
    if not session_ids:
        return set()
    ended: set[str] = set()
    ids = sorted(session_ids)
    for start in range(0, len(ids), 500):
        chunk = ids[start:start + 500]
        ended.update(
            row[0]
            for row in connection.execute(
                f"SELECT id FROM sessions WHERE ended_at IS NOT NULL AND id IN ({','.join('?' for _ in chunk)})",
                chunk,
            )
        )
    return ended


def derive_router_outcomes(
    connection: sqlite3.Connection,
    *,
    pfc_states: Mapping[str, str] | None = None,
    servable_items_by_lo: Mapping[str, set[str]] | None = None,
) -> list[dict[str, Any]]:
    """One outcome row per logged decision, from the ledgers alone (read-only).

    ``pfc_states`` maps attempt id to its PF-c assessment
    (``substrate.canonical_projection.pfc_assessments``); a nothing-assessed
    answer is never an outcome. ``servable_items_by_lo``
    (:func:`servable_items_by_learning_object`) lets R_next be
    ``not_applicable`` where the learning object has no other item; without it
    an unobserved R_next stays ``pending``.
    """

    pfc_states = pfc_states or {}
    ledger = _Ledger(connection)
    decisions = [
        dict(row)
        for row in connection.execute(
            "SELECT id, decision_kind, session_id, created_at, chosen_ref, chosen_practice_item_id, "
            "chosen_learning_object_id, chosen_scheduler_candidate_id, parent_decision_id "
            "FROM router_decisions ORDER BY created_at, id"
        )
    ]
    overridden = {row["parent_decision_id"] for row in decisions if row["decision_kind"] == "learner_pick"}
    # Decisions are ordered by (created_at, id): a later one in the same
    # session supersedes an offer whose head was never taken.
    last_in_session: dict[str, int] = {}
    for index, row in enumerate(decisions):
        if row["session_id"]:
            last_in_session[row["session_id"]] = index
    ended = _ended_sessions(connection, set(last_in_session))

    outcomes: list[dict[str, Any]] = []
    for index, decision in enumerate(decisions):
        if not decision.get("chosen_practice_item_id"):
            # Stop for today, a vetoed run, a block with no item: no action to follow.
            outcomes.append(_not_applicable(decision, "not_applicable", ledger.observed_through, pending=False))
            continue
        action = _action_attempt(decision, ledger)
        if action is None:
            if decision["decision_kind"] == "today_offer" and decision["id"] in overridden:
                status, pending = "overridden", False
            elif decision["session_id"] and last_in_session.get(decision["session_id"], -1) > index:
                status, pending = "superseded", False
            elif decision["session_id"] in ended:
                status, pending = "not_taken", False
            else:
                status, pending = "open", True
            outcomes.append(_not_applicable(decision, status, ledger.observed_through, pending=pending))
            continue
        r_cold = _r_cold(action, ledger, pfc_states)
        # Only R_cold finalizes S: once it is observed, R_next counts only if
        # it came at or before the cold attempt.
        r_next = _r_next(action, ledger, pfc_states, until_position=r_cold["position"])
        r_next_not_applicable = None
        if r_next["status"] != "observed":
            others = (
                set(servable_items_by_lo.get(action["learning_object_id"], set())) - {action["practice_item_id"]}
                if servable_items_by_lo is not None
                else None
            )
            if others is not None and not others:
                r_next_not_applicable = "no_other_servable_item"
            elif r_cold["status"] == "observed":
                r_next_not_applicable = "closed_by_r_cold"
            if r_next_not_applicable is not None:
                r_next = {**r_next, "status": "not_applicable"}
        if r_cold["status"] == "observed":
            s_status = "final"
            s_value = (
                S_ALPHA * r_cold["value"] + (1.0 - S_ALPHA) * r_next["value"]
                if r_next["status"] == "observed"
                else r_cold["value"]
            )
        elif r_next["status"] == "observed":
            # Provisional: R_next while R_cold is pending.
            s_status, s_value = "provisional", r_next["value"]
        else:
            s_status, s_value = "pending", None
        outcomes.append(
            {
                "decision_id": decision["id"],
                "outcome_version": OUTCOME_VERSION,
                "target_practice_item_id": action["practice_item_id"],
                "target_learning_object_id": action["learning_object_id"],
                "action_status": "taken",
                "action_attempt_id": action["id"],
                "r_next_status": r_next["status"],
                "r_next_value": r_next["value"],
                "r_next_attempt_id": r_next["attempt_id"],
                "r_next_elapsed_seconds": r_next["elapsed_seconds"],
                "r_next_skipped": sum(r_next["skipped"].values()),
                "r_cold_status": r_cold["status"],
                "r_cold_value": r_cold["value"],
                "r_cold_attempt_id": r_cold["attempt_id"],
                "r_cold_gap_seconds": r_cold["gap_seconds"],
                "r_cold_skipped": sum(r_cold["skipped"].values()),
                "s_status": s_status,
                "s_value": s_value,
                "s_alpha": S_ALPHA,
                "observed_through": ledger.observed_through,
                "detail_json": json.dumps(
                    {
                        "basis": OUTCOME_VERSION,
                        "cold_min_gap_seconds": RETENTION_MIN_DELAY_SECONDS,
                        "r_next_skip_reasons": dict(sorted(r_next["skipped"].items())),
                        "r_cold_skip_reasons": dict(sorted(r_cold["skipped"].items())),
                        "r_next_not_applicable": r_next_not_applicable,
                        "s_provisional_from": "r_next" if s_status == "provisional" else None,
                        "s_from": (
                            None
                            if s_value is None
                            else "r_cold_and_r_next"
                            if s_status == "final" and r_next["status"] == "observed"
                            else "r_cold" if s_status == "final" else "r_next"
                        ),
                    },
                    sort_keys=True,
                ),
            }
        )
    return outcomes


def rebuild_router_outcomes(
    connection: sqlite3.Connection,
    *,
    pfc_states: Mapping[str, str] | None = None,
    servable_items_by_lo: Mapping[str, set[str]] | None = None,
) -> int:
    """Replace the derived cache; the caller owns the transaction."""

    return replace_router_outcomes(
        connection,
        derive_router_outcomes(
            connection, pfc_states=pfc_states, servable_items_by_lo=servable_items_by_lo
        ),
    )


__all__ = [
    "INDEPENDENT_ATTEMPT_TYPES",
    "OUTCOME_VERSION",
    "S_ALPHA",
    "derive_router_outcomes",
    "rebuild_router_outcomes",
    "servable_items_by_learning_object",
]
