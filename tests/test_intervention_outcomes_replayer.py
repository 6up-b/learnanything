"""S5 (§11.2, G13): the outcome join rebuilds deterministically from one replayer, with no model call."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.db.stores.source_service import outcomes
from learnloop.instructional.interventions import record_need_served
from learnloop.substrate.intervention_outcomes import outcome_for, rebuild_intervention_outcomes
from learnloop.substrate.rebuild_orchestrator import derived_table_owners, rebuild_all_derived_state
from tests.source_service_fakes import build_service_vault, loaded, table_counts

T0 = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)


def _intervention(**extra):
    return {"id": "rti_1", "created_at": T0.isoformat(), "session_id": "s1",
            "assets": {"practice_item_ids": ["pi_eigen_1"]}, "targets": {"facets": ["facet_eigen"]}, **extra}


def _attempt(attempt_id, at, **extra):
    return {"id": attempt_id, "practice_item_id": "pi_eigen_1", "created_at": at.isoformat(), "session_id": "s1",
            "correctness": 1.0, "rubric_score": 4, "error_type": None, "attempt_type": "independent_attempt",
            "hints_used": 0, "primed": 0, "latency_seconds": 90.0, "declared_dont_know": 0,
            "facets": {"facet_eigen"}, **extra}


def test_outcome_states(tmp_path):
    paths, _repository = build_service_vault(tmp_path / "vault")
    vault = loaded(paths)
    later = T0 + timedelta(days=2)

    def state(attempts, as_of=later, **extra):
        return outcome_for(_intervention(**extra), attempts, vault, as_of=as_of, signals=[])

    assert state([_attempt("a", later)])["cold_outcome_state"] == "cold_success"
    assert state([_attempt("a", later, correctness=0.0)])["cold_outcome_state"] == "cold_failure"
    assert state([_attempt("a", later, attempt_type="hinted_attempt")])["cold_outcome_state"] == \
        "contaminated_or_assisted"
    assert state([_attempt("a", later, declared_dont_know=1)])["cold_outcome_state"] == "learner_declined"
    assert state([_attempt("a", later, latency_seconds=None)])["cold_outcome_state"] == "missing_duration"
    # Pending stays right-censored, never a failure; past the horizon it is expired.
    assert state([])["cold_outcome_state"] == "right_censored_pending"
    assert state([], as_of=T0 + timedelta(days=45))["cold_outcome_state"] == "right_censored_expired"
    assert state([], assets={}, targets={})["cold_outcome_state"] == "unmeasurable_no_targets"
    # An attempt the same session is R_next, not R_cold.
    soon = state([_attempt("a", T0 + timedelta(minutes=5), correctness=0.5)])
    assert soon["next_attempt_id"] == "a" and soon["next_window"] == "session"
    assert soon["cold_outcome_state"] == "right_censored_pending"


def test_a_valued_check_logs_its_bucket_beside_the_prediction(tmp_path):
    paths, _repository = build_service_vault(tmp_path / "vault")
    predicted = {"high|none": 0.6, "low|none": 0.3, "mid|none": 0.1}
    row = outcome_for(_intervention(valuation={"predicted_outcomes": predicted, "expected_minutes": 2.0,
                                               "regime": "item_point"}),
                      [_attempt("a", T0 + timedelta(minutes=3))], loaded(paths), as_of=T0 + timedelta(days=1),
                      signals=[])
    assert row["observed_bucket"] == "high|none" and row["predicted_outcomes"] == predicted
    assert row["predicted_minutes"] == 2.0 and row["actual_minutes"] == 1.5


def test_the_replayer_is_registered_deterministic_and_calls_nothing(tmp_path):
    paths, repository = build_service_vault(tmp_path / "vault")
    vault = loaded(paths)
    assert derived_table_owners()["retrieval_intervention_outcomes"] == ("retrieval_intervention_outcomes",)
    record_need_served(vault, repository, {"id": "n1", "target_facets": ["facet_eigen"],
                                           "learning_object_id": "lo_matrices"}, practice_item_id="pi_eigen_1",
                       session_id="s1")
    complete_self_graded_attempt(vault, repository,
                                 AttemptDraft(practice_item_id="pi_eigen_1", learner_answer_md="x",
                                              attempt_type="independent_attempt", session_id="s1"),
                                 SelfGradeInput(criterion_points={"correct": 4}, fatal_errors=[], confidence=3))
    before = table_counts(repository, ["model_call_receipts", "judgment_ledger"])
    rebuild_intervention_outcomes(vault, repository)
    with repository.connection() as connection:
        first = outcomes(connection)
    rebuild_all_derived_state(loaded(paths), repository)
    with repository.connection() as connection:
        second = outcomes(connection)
    assert first == second and len(first) == 1
    [row] = first.values()
    assert row["next_attempt_id"] is not None and row["cold_outcome_state"] == "right_censored_pending"
    assert table_counts(repository, ["model_call_receipts", "judgment_ledger"]) == before
