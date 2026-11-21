"""The readers' own assistance and coldness predicates, characterized on a matrix of attempt values.

Written and run against the readers as they were before their predicates moved under
``learnloop.attempts.fact_predicates``: each test calls the reader's own function (as its callers do) on every row
of the matrix and compares it with a verbatim copy of the reader's expression (``_base_*`` below), and the digest of
each reader's outputs on the whole matrix is pinned. A moved kernel or an adapter that changed one output fails here,
whatever the new code looks like.

The matrix crosses every stored attempt type (and a missing or empty one) with the submitted hint counts and
``primed`` values the store can hold (and the falsy forms a reader may see: None, 0, False), and the grades
(none, wrong, partial, right). The coldness dimension adds the reveal scans: none made, an empty one, a ledger row
under the auto-prime threshold, two rows, and a non-ledger finding on the cold item.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from typing import Any

import pytest

from learnloop.attempt_types import SUPPORTED_ATTEMPT_TYPES
from learnloop.attempts.attempts import AttemptValidationError, fsrs_rating_for_attempt
from learnloop.attempts.coldness_receipt import _unassisted
from learnloop.daily_plan.lesson_suggestion import _cold as lesson_cold
from learnloop.diagnosis.causal_activity_policy import attempt_counts_as_assisted
from learnloop.diagnosis.split.history import history_attempt_from_blind_record
from learnloop.learner.lesson_weight import COLD_ATTEMPT_TYPES
from learnloop.scheduling.fsrs import Rating, rating_from_score
from learnloop.substrate.intervention_outcomes import is_assisted
from learnloop.teacher.brief import _cold as teacher_cold
from learnloop.vault.loader import load_vault
from learnloop.vault.models import HintPolicy, PracticeItem, Rubric, RubricCriterion

from tests.helpers import create_basic_vault

TYPES = (*SUPPORTED_ATTEMPT_TYPES, None, "")
HINTS = (None, 0, 1, 2, 5)
PRIMED = (None, 0, 1, False, True)
CORRECTNESS = (None, 0.0, 0.5, 1.0)
MATRIX = tuple(
    {"attempt_type": kind, "hints_used": hints, "primed": primed, "correctness": correctness}
    for kind, hints, primed, correctness in itertools.product(TYPES, HINTS, PRIMED, CORRECTNESS)
)

_LEDGER_ROW = {"ledger": "reveal_events", "why": "reveal_ledger_answer_exposed_on_cold_item", "id": "rv1",
               "amount": 0.2, "source_kind": "tutor_answer"}
SCANS: tuple[Any, ...] = (
    None,
    {"events": []},
    {"events": [_LEDGER_ROW]},
    {"events": [_LEDGER_ROW, {**_LEDGER_ROW, "id": "rv2", "amount": 0.5}]},
    {"events": [{"ledger": "question_events", "why": "tutor_answer_leak_suspected_on_cold_item", "id": "q1"}]},
)

CAP_MAPS: tuple[dict[Any, Any], ...] = (
    {}, {"1": "good"}, {1: "hard"}, {"1": "good", "3": "again"}, {"2": "2", "x": "easy"}, {0: "Hard", "4": "1"},
    {"1": ""},
)
SCORES = ((0, 4), (1, 4), (2, 4), (3, 4), (4, 4), (5, 10))
CAP_HINTS = (0, 1, 2, 3, 4, 7)


# -- verbatim copies of the readers' expressions before they moved ----------------------------------------------

_LEGACY = frozenset({"hinted_attempt", "guided_walkthrough", "reconstruction_after_walkthrough"})
_UNAIDED = frozenset({"independent_attempt", "dont_know", "exam_attempt"})
_TEACHER_COLD = frozenset({"independent_attempt", "open_text", "diagnostic_probe", "exam_attempt"})


def _base_canonical(row):
    # diagnosis/causal_activity_policy.py::classify_attempt_activity's legacy union (the class adds nothing the
    # union does not already cover for a bare attempt).
    return row["attempt_type"] in _LEGACY or int(row["hints_used"] or 0) > 0 or bool(row["primed"])


def _base_intervention(attempt):
    # substrate/intervention_outcomes.py::is_assisted
    return (attempt.get("attempt_type") not in _UNAIDED or bool(attempt.get("hints_used"))
            or bool(attempt.get("primed")))


def _base_coldness(cold_attempt, scan):
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


def _base_history_assisted(attempt_type, hints_used):
    # diagnosis/split/history.py: history_attempt_from_blind_record and VaultHistoryStore._from_stored
    return bool(hints_used) or attempt_type in _LEGACY


def _base_teacher_cold(row):
    # teacher/brief.py::_cold
    return row["attempt_type"] in _TEACHER_COLD and not row["primed"] and not row["hints_used"]


def _base_lesson_cold(row):
    # daily_plan/lesson_suggestion.py::_cold
    return (row["attempt_type"] in COLD_ATTEMPT_TYPES and not row["primed"] and not row["hints_used"]
            and row["correctness"] is not None)


def _base_cap_value(mapping, hints_used):
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


def _base_rating(score, max_points, cap_map, hints):
    # attempts/attempts.py::fsrs_rating_for_attempt -> _capped_rating -> _rating_from_cap
    rating = rating_from_score(score, max_points)
    value = _base_cap_value(cap_map, hints)
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


def _digest(values: list[Any]) -> str:
    return hashlib.sha256(json.dumps(values, sort_keys=True, default=str).encode("utf-8")).hexdigest()


# -- the readers ------------------------------------------------------------------------------------------------


def _canonical_outputs():
    return [attempt_counts_as_assisted(attempt_type=row["attempt_type"], primed=row["primed"],
                                       hints_used=row["hints_used"]) for row in MATRIX]


def _intervention_outputs():
    return [is_assisted(dict(row)) for row in MATRIX]


def _coldness_outputs():
    return [_unassisted(dict(row) if row is not None else None, scan)
            for row in (*MATRIX, None) for scan in SCANS]


def _teacher_outputs():
    return [teacher_cold(row) for row in MATRIX]


def _lesson_outputs():
    return [lesson_cold(row) for row in MATRIX]


def _item(cap_map):
    return PracticeItem(
        id="pi_matrix", learning_object_id="lo_matrix", practice_mode="constructed_response",
        attempt_types_allowed=["independent_attempt", "hinted_attempt"], evidence_facets=["f"],
        evidence_weights={"f": 1.0}, prompt="Q", expected_answer="A",
        grading_rubric=Rubric(criteria=[RubricCriterion(id="c", points=4, description="d")]),
        hint_policy=HintPolicy(max_useful_hints=2, fsrs_rating_cap_by_hint=cap_map),
        created_at="2026-05-01T00:00:00Z", updated_at="2026-05-01T00:00:00Z")


def _rating_outputs():
    out = []
    for cap_map, (score, max_points), hints in itertools.product(CAP_MAPS, SCORES, CAP_HINTS):
        try:
            out.append(int(fsrs_rating_for_attempt(_item(cap_map), score, max_points, hints)))
        except AttemptValidationError:
            out.append("raises")
    return out


@pytest.fixture(scope="module")
def vault(tmp_path_factory):
    return load_vault(create_basic_vault(tmp_path_factory.mktemp("characterize") / "vault").root)


def _history_outputs(vault):
    out = []
    for row in MATRIX:
        attempt = history_attempt_from_blind_record(
            vault, attempt_id="att_m", item=None, learning_object_id="lo_m", practice_item_id="pi_m",
            completed_at="2026-06-01T12:00:00Z", learner_answer_md="x", attempt_type=row["attempt_type"],
            record={}, hints_used=row["hints_used"], primed=row["primed"])
        out.append([attempt.assisted, attempt.primed, attempt.cold_unassisted])
    return out


#: Each reader's outputs on the whole matrix, recorded before any predicate moved.
DIGESTS = {
    "canonical": "09ec11b3b3ba1f1ceb6a3d139681d81335a3462b02d9164fe250c60bad019a9e",
    "intervention": "637b26d842e46d1edc3ea75a3a18739cf211b4a6f03ae3eb8ee3bf0af46900e7",
    "coldness": "9b8aebbf8ac5721a2751f2b946be54bcbe0d714088d86c2be19c5646532e796e",
    "teacher_cold": "5eae4bf81f7639cbcb20d9e4e724a368f755f544ad82c844a0aee64e97306947",
    "lesson_cold": "6c38a366c7a465003b2a5ab0ae2f2db3f95b8c8910da2bda81b99d24406e359b",
    "fsrs_rating": "c6879d9849aa44f572ce7c9d25bfc1216396a9af648d46bba89405283f89ed1d",
    "history": "3b0b6e31de02452e9317f7801a9d8540504a378befca43f7ffd0e7f97160281d",
}


def test_the_canonical_policy_matches_its_legacy_union_on_the_matrix():
    outputs = _canonical_outputs()
    assert outputs == [_base_canonical(row) for row in MATRIX]
    assert _digest(outputs) == DIGESTS["canonical"]


def test_intervention_outcomes_counts_an_open_text_answer_as_assisted():
    outputs = _intervention_outputs()
    assert outputs == [_base_intervention(row) for row in MATRIX]
    assert _digest(outputs) == DIGESTS["intervention"]
    assert is_assisted({"attempt_type": "open_text", "hints_used": 0, "primed": False}) is True


def test_the_coldness_dimension_keeps_its_status_evidence_and_scan_flag():
    outputs = _coldness_outputs()
    assert outputs == [_base_coldness(row, scan) for row in (*MATRIX, None) for scan in SCANS]
    assert _digest(outputs) == DIGESTS["coldness"]
    # Key order is part of the stored JSON's bytes.
    clean = _unassisted({"attempt_type": "independent_attempt", "hints_used": 0, "primed": False}, SCANS[2])
    assert list(clean["evidence"]) == ["hints_used", "primed", "attempt_type", "reveal_ledger_rows",
                                       "reveal_ledger_amount", "reveal_ledger_scanned", "rule", "violation"]
    assert clean["status"] == "fail"  # a reveal under the auto-prime threshold still fails it


def test_the_teacher_and_lesson_cold_checks_on_the_matrix():
    teacher = _teacher_outputs()
    lesson = _lesson_outputs()
    assert teacher == [_base_teacher_cold(row) for row in MATRIX]
    assert lesson == [_base_lesson_cold(row) for row in MATRIX]
    assert _digest(teacher) == DIGESTS["teacher_cold"]
    assert _digest(lesson) == DIGESTS["lesson_cold"]


def test_the_fsrs_rating_cap_keeps_binning_key_coercion_fallback_and_errors():
    outputs = _rating_outputs()
    expected = [(lambda r: r if r == "raises" else int(r))(_base_rating(score, max_points, cap_map, hints))
                for cap_map, (score, max_points), hints in itertools.product(CAP_MAPS, SCORES, CAP_HINTS)]
    assert outputs == expected
    assert "raises" in outputs
    assert _digest(outputs) == DIGESTS["fsrs_rating"]


def test_the_diagnoser_history_keeps_assisted_and_primed_apart(vault):
    outputs = _history_outputs(vault)
    assert outputs == [[_base_history_assisted(row["attempt_type"], row["hints_used"]), bool(row["primed"]),
                        not _base_history_assisted(row["attempt_type"], row["hints_used"]) and not bool(row["primed"])]
                       for row in MATRIX]
    assert _digest(outputs) == DIGESTS["history"]


def _print_digests(vault) -> dict[str, str]:  # pragma: no cover - used once to record DIGESTS
    return {
        "canonical": _digest(_canonical_outputs()), "intervention": _digest(_intervention_outputs()),
        "coldness": _digest(_coldness_outputs()), "teacher_cold": _digest(_teacher_outputs()),
        "lesson_cold": _digest(_lesson_outputs()), "fsrs_rating": _digest(_rating_outputs()),
        "history": _digest(_history_outputs(vault)),
    }
