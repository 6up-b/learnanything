"""What other test files use from ``tests/test_data_capture_codex_review.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from types import SimpleNamespace

from learnloop.daily_plan import measurement as M
from learnloop.scheduling.intent.serving import check_date

from tests.data_capture_a2_measurement_helpers import _answer, _objectives


def _second_decision(env, source_id):
    with env.repository.atomic(), env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO router_decisions SELECT 'd2', 'k2', decision_kind, surface, mode, policy, algorithm_version, log_version,"
            " session_id, parent_decision_id, scheduler_slate_id, controller_decision_id, snapshot_hash, design, seed,"
            " candidates_json, exclusions_json, candidate_count, chosen_ref, chosen_practice_item_id, chosen_learning_object_id,"
            " chosen_scheduler_candidate_id, propensity, propensity_kind, learner_pick, fallback, mixture_weights_json,"
            " model_distributions_json, sensor_answers_json, question_set_version, model_ids_json, card_hash,"
            " similar_decision_ids_json, latency_ms, cost_usd, detail_json, ? FROM router_decisions WHERE id = ?",
            (env.now_iso(), source_id))
        M.record(env.vault, env.repository, connection, decision_id="d2", decision_kind="plan_interrupt",
                 frozen=M.freeze_followup("lo_diag", support=["insert_now", "continue_current"]), arm=M.ARM_WAIT,
                 clock=env.clock)
    return _objectives(env)["d2"]


def _due_hint(env, commitment_id):
    with env.repository.connection() as connection:
        return connection.execute(
            "SELECT due_hint FROM commitment_versions WHERE commitment_id = ?", (commitment_id,)).fetchone()[0]


def _hint_instant(hint):
    return check_date(SimpleNamespace(due_hint=hint, created_at=""), default_days=1)[0]


def _warm_answer(env, objective, *, warm_item="pi_diag_easy"):
    """The learner practises the LO, then answers the due check minutes later: on their own, and warm."""

    lo = objective["learning_object_id"]
    _answer(env, warm_item, lo)
    env.clock.advance(5)
    _answer(env, objective["practice_item_id"], lo)
    env.clock.advance(1)
