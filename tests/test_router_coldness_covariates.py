"""Owner decision D12 (2026-10-12, router spec §15.2): coldness is learned.

R1's ``R_cold`` (an attempt at least a day after the last attempt or reveal on
the learning object, in another session, unassisted) stays as a provisional
label. Each outcome also records the covariates coldness can later be fitted
from (R3), for its R_next and R_cold attempts:

* the time since the last exposure to the attempt's item, its facets and its
  learning object (an attempt, a reveal, a tutor question or a reading of the
  source);
* the attempts in between (since the last exposure to the learning object);
* the FSRS-predicted retrievability at the attempt (the replayer's fold of the
  attempt ledger under the vault's FSRS weights, as the fitting job chains it);
* the reveal-ledger amount since the last attempt on the learning object.

``coldness_candidates_json`` lists the same covariates for every later attempt
the one-day rule considered, so a learned coldness is not limited to the
rule's own pick.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
import sqlite3

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.db.stores.router import ROUTER_LOG_VERSION, insert_router_decision
from learnloop.router.outcomes import derive_router_outcomes
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault

T0 = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)
LO, OTHER_LO = "lo_svd_definition", "lo_other"
A, B, X = "pi_svd_define_001", "pi_svd_define_002", "pi_other_001"


def _at(**delta) -> str:
    return (T0 + timedelta(**delta)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _seconds(**delta) -> int:
    return int(timedelta(**delta).total_seconds())


@pytest.fixture
def repo(tmp_path):
    return Repository(create_basic_vault(tmp_path / "vault").sqlite_path)


def _decision(repo, decision_id: str, *, created_at: str, item: str = A, candidate: str = "c1") -> None:
    row = {
        "id": decision_id, "receipt_key": f"today_offer:{decision_id}", "decision_kind": "today_offer",
        "surface": "desktop_queue", "mode": "legacy_queue", "policy": "composed_offer_v2",
        "algorithm_version": "mvp-0.15", "log_version": ROUTER_LOG_VERSION, "session_id": "s1",
        "snapshot_hash": "h", "candidates_json": "[]", "exclusions_json": "{}", "candidate_count": 0,
        "chosen_ref": item, "chosen_practice_item_id": item, "chosen_learning_object_id": LO,
        "chosen_scheduler_candidate_id": candidate, "propensity": 1.0, "propensity_kind": "deterministic",
        "learner_pick": 0, "detail_json": "{}", "created_at": created_at,
    }
    with repo.atomic(), repo.connection() as connection:
        insert_router_decision(connection, row)


def _attempt(repo, attempt_id: str, *, item: str, lo: str = LO, created_at: str, correctness: float,
             session: str, facets: list[str], candidate: str | None = None, rubric_score: int | None = None) -> None:
    with repo.connection() as connection:
        connection.execute(
            """INSERT INTO practice_attempts(
                 id, practice_item_id, learning_object_id, practice_mode, attempt_type, hints_used,
                 correctness, rubric_score, manual_review, created_at, session_id, scheduler_candidate_id,
                 primed, evidence_origin, evidence_facets_json)
               VALUES (?,?,?,?,?,0,?,?,0,?,?,?,0,'human',?)""",
            (attempt_id, item, lo, "short_answer", "independent_attempt", correctness, rubric_score, created_at,
             session, candidate, json.dumps(facets)),
        )
        connection.commit()


def _reveal(repo, reveal_id: str, *, item: str, created_at: str, amount: float, kind: str) -> None:
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO reveal_events(id, practice_item_id, learning_object_id, source_kind, amount, created_at)"
            " VALUES (?,?,?,?,?,?)",
            (reveal_id, item, LO, kind, amount, created_at),
        )
        connection.commit()


def _reading(repo, event_id: str, *, created_at: str) -> None:
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO source_exposure_events(id, context, extraction_id, span_id, entity_type, entity_id,"
            " created_at) VALUES (?,?,?,?,?,?,?)",
            (event_id, "reader", "ext_1", "span_1", "learning_object", LO, created_at),
        )
        connection.commit()


def test_each_outcome_records_its_coldness_covariates(repo):
    _decision(repo, "d1", created_at=_at(minutes=0))
    _attempt(repo, "a0", item=A, created_at=_at(minutes=1), correctness=0.5, session="s1",
             facets=["f_def"], candidate="c1")                                                 # the action
    _attempt(repo, "x1", item=X, lo=OTHER_LO, created_at=_at(minutes=10), correctness=1.0, session="s1",
             facets=["f_def"])                                                                  # shares a facet
    _attempt(repo, "a1", item=B, created_at=_at(minutes=20), correctness=1.0, session="s1",
             facets=["f_def", "f_b"])                                                           # R_next
    # The stuck prompt's answer display (mvp-0.13) is a reveal like any other.
    _reveal(repo, "r1", item=A, created_at=_at(hours=30), amount=0.4, kind="answer_display")
    _reading(repo, "read1", created_at=_at(hours=50))
    _attempt(repo, "y1", item=X, lo=OTHER_LO, created_at=_at(hours=60), correctness=1.0, session="s2",
             facets=["f_other"])                                                                # in between
    _attempt(repo, "a2", item=B, created_at=_at(hours=96), correctness=0.0, session="s3",
             facets=["f_b"])                                                                    # R_cold

    with repo.connection() as connection:
        [outcome] = [
            row for row in derive_router_outcomes(connection, retrievability_by_attempt={"a2": 0.42, "a1": 0.97})
            if row["decision_id"] == "d1"
        ]

    assert (outcome["r_next_attempt_id"], outcome["r_cold_attempt_id"]) == ("a1", "a2")
    # R_next (a1): B never seen before; its facet f_def was exercised by x1;
    # its learning object last by the action a0, with x1 in between.
    assert outcome["r_next_since_item_seconds"] is None
    assert outcome["r_next_since_facet_seconds"] == _seconds(minutes=10)
    assert outcome["r_next_since_lo_seconds"] == _seconds(minutes=19)
    assert outcome["r_next_intervening_attempts"] == 1
    assert outcome["r_next_predicted_retrievability"] == pytest.approx(0.97)
    assert outcome["r_next_reveal_amount"] == 0.0
    # R_cold (a2): B last at a1; f_b last at a1; the learning object last by
    # the reading at 50 h (later than the 30 h reveal), with y1 in between;
    # the reveal's amount since the last attempt on the learning object.
    assert outcome["r_cold_since_item_seconds"] == _seconds(hours=96) - _seconds(minutes=20)
    assert outcome["r_cold_since_facet_seconds"] == _seconds(hours=96) - _seconds(minutes=20)
    assert outcome["r_cold_since_lo_seconds"] == _seconds(hours=46)
    assert outcome["r_cold_intervening_attempts"] == 1
    assert outcome["r_cold_predicted_retrievability"] == pytest.approx(0.42)
    assert outcome["r_cold_reveal_amount"] == pytest.approx(0.4)

    candidates = json.loads(outcome["coldness_candidates_json"])
    assert [entry["attempt_id"] for entry in candidates] == ["a1", "a2"]
    by_id = {entry["attempt_id"]: entry for entry in candidates}
    assert (by_id["a1"]["role"], by_id["a2"]["role"]) == ("r_next", "r_cold")
    # The one-day rule's verdict travels with the covariates it is fitted against.
    assert "insufficient_delay" in by_id["a1"]["exclusions"] and by_id["a2"]["exclusions"] == []
    assert by_id["a2"]["last_lo_exposure_kind"] == "reading"
    assert by_id["a2"]["correctness"] == 0.0 and by_id["a2"]["since_action_seconds"] == _seconds(hours=96, minutes=-1)
    detail = json.loads(outcome["detail_json"])
    assert detail["r_cold_rule"] == "provisional_one_day"


def test_an_unobserved_outcome_has_no_covariates(repo):
    _decision(repo, "d1", created_at=_at(minutes=0))
    _attempt(repo, "a0", item=A, created_at=_at(minutes=1), correctness=0.5, session="s1", facets=["f"], candidate="c1")

    with repo.connection() as connection:
        [outcome] = derive_router_outcomes(connection)

    assert outcome["r_next_status"] == outcome["r_cold_status"] == "pending"
    for prefix in ("r_next", "r_cold"):
        for name in ("since_item_seconds", "since_facet_seconds", "since_lo_seconds", "intervening_attempts",
                     "predicted_retrievability", "reveal_amount"):
            assert outcome[f"{prefix}_{name}"] is None
    assert json.loads(outcome["coldness_candidates_json"]) == []


def test_the_replayer_records_the_fsrs_predicted_retrievability(tmp_path):
    from learnloop.params.fitted_params import resolve_fsrs_weights
    from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS, Rating, apply_review, forgetting_curve
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    _decision(repository, "d1", created_at=_at(minutes=0))
    _attempt(repository, "a0", item=A, created_at=_at(minutes=1), correctness=1.0, session="s1",
             facets=["f"], candidate="c1", rubric_score=4)
    _attempt(repository, "a1", item=A, created_at=_at(days=3), correctness=1.0, session="s2",
             facets=["f"], rubric_score=4)                                                     # R_cold, same item
    vault = load_vault(paths.root)
    assert resolve_fsrs_weights(repository) == FSRS6_DEFAULT_WEIGHTS

    rebuild_all_derived_state(vault, repository, clock=FrozenClock(NOW), require_complete_attempt_coverage=False)

    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT * FROM router_outcomes WHERE decision_id = 'd1'").fetchone()
    assert row["r_cold_attempt_id"] == "a1"
    # The fold the FSRS fitting job chains: the first review sets the memory,
    # the next is predicted from it after the elapsed days.
    item = vault.practice_items[A]
    rubric = vault.rubric_for_item(item)
    from learnloop.attempts.attempts import fsrs_rating_for_attempt

    rating = fsrs_rating_for_attempt(item, 4, rubric.max_points if rubric is not None else 4, 0)
    first = apply_review(None, Rating(rating), 0.0, FSRS6_DEFAULT_WEIGHTS)
    elapsed = (3 * 86400 - 60) / 86400
    expected = forgetting_curve(first.stability, elapsed, FSRS6_DEFAULT_WEIGHTS)
    assert row["r_cold_predicted_retrievability"] == pytest.approx(expected)
    assert 0.0 < row["r_cold_predicted_retrievability"] < 1.0
