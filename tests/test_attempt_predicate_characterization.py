"""The readers' own assistance and coldness predicates, characterized on a matrix of attempt values.

Written and run against the readers as they were before their predicates moved under
``learnloop.attempts.fact_predicates``: each test calls the reader's own function (as its callers do) on every row
of the matrix and compares it with a verbatim copy of the reader's expression (``base_*`` in
``tests/attempt_predicate_helpers.py``), and the digest of each reader's outputs on the whole matrix is pinned. A
moved kernel or an adapter that changed one output fails here, whatever the new code looks like.

The matrix crosses every stored attempt type (and a missing or empty one) with the submitted hint counts and
``primed`` values the store can hold (and the falsy forms a reader may see: None, 0, False), and the grades
(none, wrong, partial, right). The coldness dimension adds the reveal scans: none made, an empty one, a ledger row
under the auto-prime threshold, two rows, and a non-ledger finding on the cold item.
"""

from __future__ import annotations

import itertools

import pytest

from learnloop.attempts.attempts import AttemptValidationError, fsrs_rating_for_attempt
from learnloop.attempts.coldness_receipt import _unassisted
from learnloop.daily_plan.lesson_suggestion import _cold as lesson_cold
from learnloop.diagnosis.causal_activity_policy import attempt_counts_as_assisted
from learnloop.diagnosis.split.history import history_attempt_from_blind_record
from learnloop.substrate.intervention_outcomes import is_assisted
from learnloop.teacher.brief import _cold as teacher_cold
from learnloop.vault.loader import load_vault
from learnloop.vault.models import HintPolicy, PracticeItem, Rubric, RubricCriterion

from tests.attempt_predicate_helpers import (
    CAP_HINTS, CAP_MAPS, MATRIX, SCANS, SCORES, base_canonical, base_coldness, base_history_assisted,
    base_intervention, base_lesson_cold, base_rating, base_teacher_cold, digest,
)
from tests.helpers import create_basic_vault

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
    assert outputs == [base_canonical(row) for row in MATRIX]
    assert digest(outputs) == DIGESTS["canonical"]


def test_intervention_outcomes_counts_an_open_text_answer_as_assisted():
    outputs = _intervention_outputs()
    assert outputs == [base_intervention(row) for row in MATRIX]
    assert digest(outputs) == DIGESTS["intervention"]
    assert is_assisted({"attempt_type": "open_text", "hints_used": 0, "primed": False}) is True


def test_the_coldness_dimension_keeps_its_status_evidence_and_scan_flag():
    outputs = _coldness_outputs()
    assert outputs == [base_coldness(row, scan) for row in (*MATRIX, None) for scan in SCANS]
    assert digest(outputs) == DIGESTS["coldness"]
    # Key order is part of the stored JSON's bytes.
    clean = _unassisted({"attempt_type": "independent_attempt", "hints_used": 0, "primed": False}, SCANS[2])
    assert list(clean["evidence"]) == ["hints_used", "primed", "attempt_type", "reveal_ledger_rows",
                                       "reveal_ledger_amount", "reveal_ledger_scanned", "rule", "violation"]
    assert clean["status"] == "fail"  # a reveal under the auto-prime threshold still fails it


def test_the_teacher_and_lesson_cold_checks_on_the_matrix():
    teacher = _teacher_outputs()
    lesson = _lesson_outputs()
    assert teacher == [base_teacher_cold(row) for row in MATRIX]
    assert lesson == [base_lesson_cold(row) for row in MATRIX]
    assert digest(teacher) == DIGESTS["teacher_cold"]
    assert digest(lesson) == DIGESTS["lesson_cold"]


def test_the_fsrs_rating_cap_keeps_binning_key_coercion_fallback_and_errors():
    outputs = _rating_outputs()
    expected = [(lambda r: r if r == "raises" else int(r))(base_rating(score, max_points, cap_map, hints))
                for cap_map, (score, max_points), hints in itertools.product(CAP_MAPS, SCORES, CAP_HINTS)]
    assert outputs == expected
    assert "raises" in outputs
    assert digest(outputs) == DIGESTS["fsrs_rating"]


def test_the_diagnoser_history_keeps_assisted_and_primed_apart(vault):
    outputs = _history_outputs(vault)
    assert outputs == [[base_history_assisted(row["attempt_type"], row["hints_used"]), bool(row["primed"]),
                        not base_history_assisted(row["attempt_type"], row["hints_used"]) and not bool(row["primed"])]
                       for row in MATRIX]
    assert digest(outputs) == DIGESTS["history"]


def _print_digests(vault) -> dict[str, str]:  # pragma: no cover - used once to record DIGESTS
    return {
        "canonical": digest(_canonical_outputs()), "intervention": digest(_intervention_outputs()),
        "coldness": digest(_coldness_outputs()), "teacher_cold": digest(_teacher_outputs()),
        "lesson_cold": digest(_lesson_outputs()), "fsrs_rating": digest(_rating_outputs()),
        "history": digest(_history_outputs(vault)),
    }
