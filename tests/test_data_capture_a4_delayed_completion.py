"""Data capture A4: failed independent completion and one delayed definition.

A genuinely delayed, unexposed presentation followed by requested help is a failure of unassisted completion
(adaptive difficulty's rule); a pre-exposed presentation and abandonment stay separate; the delay runs since
the last exposure or practice, never since the offer, so warm performance gets no cold label, for router and
AD outcomes alike. Version change only: ``router_outcomes_v2`` stays what it was.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from types import SimpleNamespace

import pytest

from learnloop import delayed_completion as DC
from learnloop.adaptive_difficulty.report import _offer_outcomes
from learnloop.db.repositories import Repository
from learnloop.outcome_contract import RETENTION_MIN_DELAY_SECONDS
from learnloop.db.stores.data_capture import reading_receipts
from learnloop.router.outcomes import (
    OUTCOME_VERSION,
    OUTCOME_VERSION_V3,
    R_COLD_ITT_RULE,
    R_COLD_RULE,
    R_COLD_RULE_V3,
    derive_router_outcomes,
)

from tests.helpers import create_basic_vault
from tests.test_router_outcomes import A, B, LO, _at, _attempt, _decision, _iso, _reveal

T0 = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)


@pytest.fixture
def repo(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    return Repository(paths.sqlite_path)


def _outcomes(repo, version=OUTCOME_VERSION_V3):
    with repo.connection() as connection:
        return {row["decision_id"]: row for row in derive_router_outcomes(
            connection, outcome_version=version,
            reader_exposures=reading_receipts(connection) if version == OUTCOME_VERSION_V3 else None)}


# -- the definition --------------------------------------------------------------------------


def _presentation(**kw):
    base = {"presented_at": "2026-05-22T12:00:00Z", "last_exposure_at": "2026-05-19T12:00:00Z", "correctness": 1.0}
    return DC.Presentation(**{**base, **kw})


def test_the_definition_reuses_the_contracts_delay_and_no_new_number():
    assert DC.MIN_DELAY_SECONDS == RETENTION_MIN_DELAY_SECONDS
    assert DC.DELAYED_COMPLETION_VERSION == "delayed_completion_v1"


@pytest.mark.parametrize("facts, status, value", [
    ({}, DC.COMPLETED, 1.0),
    ({"help_requested": True}, DC.FAILED_WITH_HELP, 0.0),
    ({"pre_exposed": True}, DC.PRE_EXPOSED, None),
    ({"pre_exposed": True, "help_requested": True}, DC.PRE_EXPOSED, None),
    ({"answered": False}, DC.ABANDONED, None),
    ({"answered": False, "help_requested": True}, DC.ABANDONED, None),
    ({"last_exposure_at": "2026-05-22T11:00:00Z"}, DC.NOT_DELAYED, None),
    ({"last_exposure_at": "2026-05-22T11:00:00Z", "help_requested": True}, DC.NOT_DELAYED, None),
    ({"last_exposure_at": None}, DC.NOT_DELAYED, None),
    ({"exclusions": ("grade_held_for_review",)}, DC.EXCLUDED, None),
    ({"correctness": None}, DC.EXCLUDED, None),
    ({"correctness": None, "help_requested": True}, DC.FAILED_WITH_HELP, 0.0),
])
def test_the_one_definition(facts, status, value):
    completion = DC.classify(_presentation(**facts))
    assert (completion.status, completion.value) == (status, value)
    assert completion.is_outcome == (status in (DC.COMPLETED, DC.FAILED_WITH_HELP))


def test_the_delay_is_since_the_exposure_and_since_a_named_decision_never_only_the_offer():
    warm = _presentation(last_exposure_at="2026-05-22T11:00:00Z", not_before="2026-05-19T00:00:00Z")
    assert DC.classify(warm).status == DC.NOT_DELAYED, "a day since the offer does not make it cold"
    early = _presentation(not_before="2026-05-22T11:00:00Z")
    assert DC.classify(early).status == DC.NOT_DELAYED, "the decision must have matured too"


# -- router_outcomes_v3 ------------------------------------------------------------------------


def test_requested_help_on_a_delayed_unexposed_presentation_is_r_cold_zero(repo):
    """Reproduced first: v2 skips the hinted attempt, so the learner's failure never reaches the outcome."""

    _decision(repo, "d1", created_at=_at(minutes=0))
    _attempt(repo, "a0", item=A, created_at=_at(minutes=1), correctness=1.0, candidate="c1")
    _attempt(repo, "a1", item=B, created_at=_at(days=2), correctness=1.0, session="s2", hints=1,
             attempt_type="hinted_attempt")

    v2 = _outcomes(repo, OUTCOME_VERSION)["d1"]
    assert v2["r_cold_status"] == "pending" and v2["outcome_version"] == OUTCOME_VERSION
    assert json.loads(v2["detail_json"])["r_cold_rule"] == R_COLD_RULE
    assert json.loads(v2["detail_json"])["r_cold_skip_reasons"]["hinted"] == 1

    v3 = _outcomes(repo)["d1"]
    assert v3["outcome_version"] == OUTCOME_VERSION_V3
    assert (v3["r_cold_status"], v3["r_cold_value"], v3["r_cold_attempt_id"]) == ("observed", 0.0, "a1")
    assert (v3["s_status"], v3["s_value"]) == ("final", 0.0)
    detail = json.loads(v3["detail_json"])
    assert detail["r_cold_rule"] == R_COLD_RULE_V3
    assert detail["r_cold_completion"] == DC.FAILED_WITH_HELP
    assert detail["delayed_completion_version"] == DC.DELAYED_COMPLETION_VERSION


def test_a_help_equivalent_question_is_requested_help(repo):
    _decision(repo, "d1", created_at=_at(minutes=0))
    _attempt(repo, "a0", item=A, created_at=_at(minutes=1), correctness=1.0, candidate="c1")
    _attempt(repo, "a1", item=B, created_at=_at(days=2), correctness=1.0, session="s2")
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO question_events(id, context, practice_item_id, attempt_id, question_md, question_type, created_at)"
            " VALUES ('q1', 'practice', ?, 'a1', 'How?', 'strategy', ?)", (B, _at(days=2)))
        connection.commit()
    outcome = _outcomes(repo)["d1"]
    assert (outcome["r_cold_value"], outcome["r_cold_attempt_id"]) == (0.0, "a1")


def test_an_answer_seen_before_the_presentation_stays_separate(repo):
    _decision(repo, "d1", created_at=_at(minutes=0))
    _attempt(repo, "a0", item=A, created_at=_at(minutes=1), correctness=1.0, candidate="c1")
    _reveal(repo, "r1", item=B, created_at=_at(hours=2))
    _attempt(repo, "a1", item=B, created_at=_at(days=2), correctness=0.0, session="s2", primed=1)
    _attempt(repo, "a2", item=B, created_at=_at(days=5), correctness=1.0, session="s3")

    outcome = _outcomes(repo)["d1"]
    assert (outcome["r_cold_value"], outcome["r_cold_attempt_id"]) == (1.0, "a2"), "pre-exposed is neither a success nor a failure"
    assert json.loads(outcome["detail_json"])["r_cold_skip_reasons"] == {"pre_exposed": 1}


def test_a_primed_attempt_with_no_reveal_timing_is_excluded_as_ad_excludes_it(repo):
    _decision(repo, "d1", created_at=_at(minutes=0))
    _attempt(repo, "a0", item=A, created_at=_at(minutes=1), correctness=1.0, candidate="c1")
    _attempt(repo, "a1", item=B, created_at=_at(days=2), correctness=0.0, session="s2", primed=1)
    outcome = _outcomes(repo)["d1"]
    assert outcome["r_cold_status"] == "pending"
    assert json.loads(outcome["detail_json"])["r_cold_skip_reasons"] == {"primed_unbound": 1}


def test_warm_performance_gets_no_cold_label_a_reading_is_an_exposure(repo):
    """v2's gap reads attempts and reveals; a reading an hour before the attempt is warm under v3."""

    _decision(repo, "d1", created_at=_at(minutes=0))
    _attempt(repo, "a0", item=A, created_at=_at(minutes=1), correctness=1.0, candidate="c1")
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO source_exposure_events(id, context, extraction_id, span_id, entity_type, entity_id, created_at)"
            " VALUES ('e1', 'reader', 'x', 's', 'learning_object', ?, ?)", (LO, _at(days=2, minutes=-30)))
        connection.commit()
    _attempt(repo, "a1", item=B, created_at=_at(days=2), correctness=1.0, session="s2")

    assert _outcomes(repo, OUTCOME_VERSION)["d1"]["r_cold_status"] == "observed"
    v3 = _outcomes(repo)["d1"]
    assert v3["r_cold_status"] == "pending"
    assert json.loads(v3["detail_json"])["r_cold_skip_reasons"] == {"insufficient_delay": 1}


def test_a_delay_counts_to_the_presentation_not_the_answer(repo):
    """An answer given later than the serve: the delay is what the learner came back after."""

    _decision(repo, "d1", created_at=_at(minutes=0))
    _attempt(repo, "a0", item=A, created_at=_at(minutes=1), correctness=1.0, candidate="c1")
    _attempt(repo, "a1", item=B, created_at=_at(days=1, minutes=30), correctness=1.0, session="s2")
    outcome = _outcomes(repo)["d1"]
    assert outcome["r_cold_attempt_id"] == "a1" and outcome["r_cold_gap_seconds"] >= RETENTION_MIN_DELAY_SECONDS


def test_an_unanswered_presentation_is_no_outcome(repo):
    """Abandonment: a presentation with no attempt writes nothing and stays pending."""

    _decision(repo, "d1", created_at=_at(minutes=0))
    _attempt(repo, "a0", item=A, created_at=_at(minutes=1), correctness=1.0, candidate="c1")
    outcome = _outcomes(repo)["d1"]
    assert outcome["r_cold_status"] == "pending" and outcome["r_cold_skipped"] == 0


def test_the_lesson_suggestion_adapter_reads_the_same_definition(repo):
    detail = {"drawn_learning_object_ids": [LO], "shown": False,
              "target_scope": [{"ref": "t", "learning_object_ids": [LO]}], "drawn_ref": "t"}
    with repo.atomic(), repo.connection() as connection:
        from learnloop.db.stores.router import ROUTER_LOG_VERSION, insert_router_decision

        insert_router_decision(connection, {
            "id": "s1", "receipt_key": "lesson_suggestion:s1", "decision_kind": "lesson_suggestion", "surface": "today_card",
            "mode": "mixture", "policy": "lesson_suggestion_v1", "algorithm_version": "mvp-0.43",
            "log_version": ROUTER_LOG_VERSION, "session_id": None, "snapshot_hash": "h", "candidates_json": "[]",
            "exclusions_json": "{}", "candidate_count": 0, "chosen_ref": "no_suggestion", "propensity": 0.5,
            "propensity_kind": "exact", "learner_pick": 0, "detail_json": json.dumps(detail), "created_at": _at(minutes=0),
        })
    _attempt(repo, "a1", item=A, created_at=_at(hours=1), correctness=1.0)                 # warm practice
    _attempt(repo, "a2", item=A, created_at=_at(days=2), correctness=0.5, session="s2", hints=1,
             attempt_type="hinted_attempt")
    outcome = _outcomes(repo)["s1"]
    assert (outcome["r_cold_value"], outcome["r_cold_attempt_id"]) == (0.0, "a2")
    detail_row = json.loads(outcome["detail_json"])
    assert detail_row["r_cold_rule"] == R_COLD_ITT_RULE and detail_row["r_cold_completion"] == DC.FAILED_WITH_HELP
    assert detail_row["basis"] == OUTCOME_VERSION_V3


def test_v2_derivation_is_untouched_by_default(repo):
    _decision(repo, "d1", created_at=_at(minutes=0))
    _attempt(repo, "a0", item=A, created_at=_at(minutes=1), correctness=1.0, candidate="c1")
    _attempt(repo, "a1", item=B, created_at=_at(days=2), correctness=1.0, session="s2")
    with repo.connection() as connection:
        default = derive_router_outcomes(connection, reader_exposures=None)
        explicit = derive_router_outcomes(connection, outcome_version=OUTCOME_VERSION, reader_exposures=None)
    assert default == explicit
    detail = json.loads(default[0]["detail_json"])
    assert "delayed_completion_version" not in detail and "r_cold_completion" not in detail


# -- AD's dose outcomes ------------------------------------------------------------------------


class _View:
    """The material view's few reads, over plain rows."""

    def __init__(self, *, draws, attempts, reveals=(), questions=()):
        self._draws, self._attempts, self._reveals, self._questions = draws, attempts, reveals, questions

    def dose_rows(self, _connection):
        return list(self._draws)

    def reveals(self, _connection):
        return list(self._reveals)

    def attempts(self, _connection):
        return list(self._attempts)

    def reading_opportunities(self, _connection):
        return []

    def rows(self, _connection, table, *args, **kwargs):
        return list(self._questions) if table == "question_events" else []


def _event(attempt_id, *, at, category=2, lo=LO, item=A, served=None):
    return SimpleNamespace(attempt_id=attempt_id, created_at=at, served_at=served or at, eligible=True, category=category,
                           learning_object_id=lo, practice_item_id=item)


def _dose(events, *, draw_at, reveals=(), practice=(), delayed):
    draw = {"id": "dr1", "row_kind": "draw", "created_at": draw_at, "learning_object_ids": [LO], "forecast_p": 0.7,
            "chosen_variant": "extra_question", "propensities": {"none": 0.5, "extra_question": 0.5}, "detail": {}}
    view = _View(draws=[draw], attempts=[{"learning_object_id": e.learning_object_id, "created_at": e.created_at,
                                          "practice_item_id": e.practice_item_id} for e in events] + list(practice), reveals=reveals)
    snapshot = SimpleNamespace(events=SimpleNamespace(attempts=events, opportunities=[]))
    return _offer_outcomes(None, snapshot, view=view, delayed_definition=delayed)


def test_ad_dose_outcome_warm_practice_a_day_after_the_offer_gets_no_cold_label():
    """Reproduced first (the predecessor's rule): a day since the offer labels warm performance cold."""

    decided = _iso(T0)
    practice = {"learning_object_id": LO, "practice_item_id": B, "created_at": _iso(T0 + timedelta(days=2, minutes=-10))}
    warm = _event("x", at=_iso(T0 + timedelta(days=2)))
    later = _event("y", at=_iso(T0 + timedelta(days=5)), category=0)
    assert _dose([warm, later], draw_at=decided, practice=[practice], delayed=False)["extra_question"][0].outcome == 1.0
    assert _dose([warm, later], draw_at=decided, practice=[practice], delayed=True)["extra_question"][0].outcome == 0.0


def test_ad_dose_outcome_uses_the_last_exposure_not_the_offer():
    decided = _iso(T0)
    warm_reveal = [{"practice_item_id": A, "learning_object_id": LO, "created_at": _iso(T0 + timedelta(days=2, minutes=-10))}]
    warm = _event("x", at=_iso(T0 + timedelta(days=2)))
    cold = _event("y", at=_iso(T0 + timedelta(days=5)), category=1)
    assert _dose([warm, cold], draw_at=decided, reveals=[], delayed=False)["extra_question"][0].outcome == 1.0
    picked = _dose([warm, cold], draw_at=decided, reveals=warm_reveal, delayed=True)["extra_question"][0]
    assert picked.outcome == 0.0, "the warm success is not the outcome; the next delayed attempt (any help: 0) is"


def test_ad_dose_outcome_needs_a_day_since_the_decision_too():
    decided = _iso(T0)
    too_soon = _event("x", at=_iso(T0 + timedelta(hours=2)))
    assert _dose([too_soon], draw_at=decided, delayed=True)["extra_question"][0].outcome is None
