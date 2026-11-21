"""The attempt matrix and the verbatim copies of the readers' predicate expressions, shared by the
characterization of the readers (``tests/test_attempt_predicate_characterization.py``) and the named predicates over
attempt facts (``tests/test_attempt_fact_predicates.py``). Each ``base_*`` is the reader's expression as it stood
before it moved under ``learnloop.attempts.fact_predicates``, kept here so both files compare against one copy."""

from __future__ import annotations

import hashlib
import itertools
import json
from typing import Any

from learnloop.attempt_types import SUPPORTED_ATTEMPT_TYPES
from learnloop.learner.lesson_weight import COLD_ATTEMPT_TYPES
from learnloop.scheduling.fsrs import Rating, rating_from_score

TYPES = (*SUPPORTED_ATTEMPT_TYPES, None, "")
HINTS = (None, 0, 1, 2, 5)
PRIMED = (None, 0, 1, False, True)
CORRECTNESS = (None, 0.0, 0.5, 1.0)
MATRIX = tuple(
    {"attempt_type": kind, "hints_used": hints, "primed": primed, "correctness": correctness}
    for kind, hints, primed, correctness in itertools.product(TYPES, HINTS, PRIMED, CORRECTNESS)
)

LEDGER_ROW = {"ledger": "reveal_events", "why": "reveal_ledger_answer_exposed_on_cold_item", "id": "rv1",
               "amount": 0.2, "source_kind": "tutor_answer"}
SCANS: tuple[Any, ...] = (
    None,
    {"events": []},
    {"events": [LEDGER_ROW]},
    {"events": [LEDGER_ROW, {**LEDGER_ROW, "id": "rv2", "amount": 0.5}]},
    {"events": [{"ledger": "question_events", "why": "tutor_answer_leak_suspected_on_cold_item", "id": "q1"}]},
)

CAP_MAPS: tuple[dict[Any, Any], ...] = (
    {}, {"1": "good"}, {1: "hard"}, {"1": "good", "3": "again"}, {"2": "2", "x": "easy"}, {0: "Hard", "4": "1"},
    {"1": ""},
)
SCORES = ((0, 4), (1, 4), (2, 4), (3, 4), (4, 4), (5, 10))
CAP_HINTS = (0, 1, 2, 3, 4, 7)


# -- verbatim copies of the readers' expressions before they moved ----------------------------------------------

LEGACY = frozenset({"hinted_attempt", "guided_walkthrough", "reconstruction_after_walkthrough"})
UNAIDED = frozenset({"independent_attempt", "dont_know", "exam_attempt"})
TEACHER_COLD = frozenset({"independent_attempt", "open_text", "diagnostic_probe", "exam_attempt"})


def base_canonical(row):
    # diagnosis/causal_activity_policy.py::classify_attempt_activity's legacy union (the class adds nothing the
    # union does not already cover for a bare attempt).
    return row["attempt_type"] in LEGACY or int(row["hints_used"] or 0) > 0 or bool(row["primed"])


def base_intervention(attempt):
    # substrate/intervention_outcomes.py::is_assisted
    return (attempt.get("attempt_type") not in UNAIDED or bool(attempt.get("hints_used"))
            or bool(attempt.get("primed")))


def base_coldness(cold_attempt, scan):
    # attempts/coldness_receipt.py::_unassisted
    if cold_attempt is None:
        return {"status": "unknown", "evidence": {"reason": "no_attempt_yet"}}
    hints = int(cold_attempt.get("hints_used") or 0)
    primed = bool(cold_attempt.get("primed"))
    ledger_rows = [dict(event) for event in scan.get("events") or []
                   if event.get("ledger") == "reveal_events"
                   and event.get("why") == "reveal_ledger_answer_exposed_on_cold_item"] if scan is not None else []
    ok = hints == 0 and not primed and not ledger_rows
    evidence = {
        "hints_used": hints, "primed": primed,
        "attempt_type": str(cold_attempt.get("attempt_type") or "") or None,
        "reveal_ledger_rows": ledger_rows,
        "reveal_ledger_amount": sum(float(row.get("amount") or 0.0) for row in ledger_rows),
        "reveal_ledger_scanned": scan is not None,
        "rule": ("pass requires hints_used == 0, primed false, AND no recorded "
                 "reveal of this item's answer in the measurement window"),
    }
    if ledger_rows:
        evidence["violation"] = "answer_revealed_before_the_cold_attempt"
    return {"status": "pass" if ok else "fail", "evidence": evidence}


def base_history_assisted(attempt_type, hints_used):
    # diagnosis/split/history.py: history_attempt_from_blind_record and VaultHistoryStore._from_stored
    return bool(hints_used) or attempt_type in LEGACY


def base_teacher_cold(row):
    # teacher/brief.py::_cold
    return row["attempt_type"] in TEACHER_COLD and not row["primed"] and not row["hints_used"]


def base_lesson_cold(row):
    # daily_plan/lesson_suggestion.py::_cold
    return (row["attempt_type"] in COLD_ATTEMPT_TYPES and not row["primed"] and not row["hints_used"]
            and row["correctness"] is not None)


def base_cap_value(mapping, hints_used):
    # attempts/attempts.py::_hint_policy_value
    if hints_used in mapping:
        return mapping[hints_used]
    if str(hints_used) in mapping:
        return mapping[str(hints_used)]
    numeric = []
    for key in mapping:
        try:
            numeric.append(int(key))
        except (TypeError, ValueError):
            continue
    eligible = [key for key in numeric if key <= hints_used]
    if not eligible:
        return None
    return mapping.get(max(eligible)) or mapping.get(str(max(eligible)))


def base_rating(score, max_points, cap_map, hints):
    # attempts/attempts.py::fsrs_rating_for_attempt -> _capped_rating -> _rating_from_cap
    rating = rating_from_score(score, max_points)
    value = base_cap_value(cap_map, hints)
    if value is None:
        return rating
    if isinstance(value, int):
        cap = Rating(max(1, min(4, value)))
    else:
        names = {"again": 1, "hard": 2, "good": 3, "easy": 4, "1": 1, "2": 2, "3": 3, "4": 4}
        normalized = str(value).strip().lower()
        if normalized not in names:
            return "raises"
        cap = Rating(names[normalized])
    return Rating(min(int(rating), int(cap)))


def digest(values: list[Any]) -> str:
    return hashlib.sha256(json.dumps(values, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def base_teacher_kind(row):
    # teacher/brief.py::_history's kind (its "cold" is _cold, base_teacher_cold above)
    return "cold" if base_teacher_cold(row) else ("assisted" if row["attempt_type"] in (
        "hinted_attempt", "guided_walkthrough", "reconstruction_after_walkthrough") or row["hints_used"] else (
        "primed" if row["primed"] else row["attempt_type"]))


def base_card_assisted(row):
    # daily_plan/router_card.py::CardGatherer.inputs, the per-LO "assisted" count
    return int(row.get("hints_used") or 0) > 0 or bool(row.get("primed"))


def base_primed_only(row):
    # daily_plan/router_card.py::CardGatherer._recent_work and learner_context.py::_traces, the "assisted" field
    return bool(row.get("primed"))


#: The readers' expressions as they stood, as source text, for the moved kernels' AST identity: each maps the reader's
#: row (or local) reads onto the facts fields a kernel reads instead.
BASE_SOURCES = {
    "fsrs_cap_value": '''
def _hint_policy_value(mapping: dict[int | str, object], hints_used: int) -> object | None:
    if hints_used in mapping:
        return mapping[hints_used]
    string_key = str(hints_used)
    if string_key in mapping:
        return mapping[string_key]
    numeric_keys: list[int] = []
    for key in mapping:
        try:
            numeric_keys.append(int(key))
        except (TypeError, ValueError):
            continue
    eligible = [key for key in numeric_keys if key <= hints_used]
    if not eligible:
        return None
    return mapping.get(max(eligible)) or mapping.get(str(max(eligible)))
''',
    "cold_item_reveal_rows": '''
def _cold_item_reveal_rows(scan: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Ledger rows (migration 154) that exposed the COLD item's own answer."""

    return [
        dict(event)
        for event in scan.get("events") or []
        if event.get("ledger") == "reveal_events"
        and event.get("why") == "reveal_ledger_answer_exposed_on_cold_item"
    ]
''',
    "unassisted_for_coldness": '''
def _unassisted(cold_attempt, scan=None):
    if cold_attempt is None:
        return _dimension("unknown", {"reason": "no_attempt_yet"})
    hints = int(cold_attempt.get("hints_used") or 0)
    primed = bool(cold_attempt.get("primed"))
    ledger_rows = _cold_item_reveal_rows(scan) if scan is not None else []
    ok = hints == 0 and not primed and not ledger_rows
    evidence: dict[str, Any] = {
        "hints_used": hints,
        "primed": primed,
        "attempt_type": str(cold_attempt.get("attempt_type") or "") or None,
        "reveal_ledger_rows": ledger_rows,
        "reveal_ledger_amount": sum(
            float(row.get("amount") or 0.0) for row in ledger_rows
        ),
        "reveal_ledger_scanned": scan is not None,
        "rule": (
            "pass requires hints_used == 0, primed false, AND no recorded "
            "reveal of this item's answer in the measurement window"
        ),
    }
    if ledger_rows:
        evidence["violation"] = "answer_revealed_before_the_cold_attempt"
    return _dimension("pass" if ok else "fail", evidence)
''',
    "diagnoser_assisted": 'bool(hints_used) or attempt_type in ASSISTED_ATTEMPT_TYPES',
    "unhelped_cold_type": 'row["attempt_type"] in _COLD_TYPES and not row["primed"] and not row["hints_used"]',
    "graded_cold_check": ('row["attempt_type"] in COLD_ATTEMPT_TYPES and not row["primed"] and not row["hints_used"]'
                          ' and row["correctness"] is not None'),
    "teacher_attempt_kind": ('"cold" if _cold(row) else ("assisted" if row["attempt_type"] in ('
                             '"hinted_attempt", "guided_walkthrough", "reconstruction_after_walkthrough") or '
                             'row["hints_used"] else ("primed" if row["primed"] else row["attempt_type"]))'),
    "hinted_or_primed": 'int(row.get("hints_used") or 0) > 0 or bool(row.get("primed"))',
    "primed_only": 'bool(row.get("primed"))',
}
