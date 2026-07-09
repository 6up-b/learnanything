"""Tutor questions as observations: question_signal + follow-up/scheduler wiring."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.codex.schemas import TutorAnswer
from learnloop.db.repositories import Repository
from learnloop.services.followups import evaluate_intervention_followup
from learnloop.services.question_signal import (
    apply_question_observation,
    collect_question_signal,
    question_adjusted_uncertainty_states,
    resolve_question_likelihood,
)
from learnloop.services.tutor_qa import ask_question
from learnloop.vault.loader import load_vault
from tests.helpers import NOW, NOW_ISO, create_basic_vault

EARLIER_ISO = "2026-05-19T10:00:00Z"  # before NOW (12:00)
QUESTION_ISO = "2026-05-19T11:00:00Z"
LATER_ISO = "2026-05-19T11:30:00Z"


def _setup(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    return vault_root, vault, repository


def _insert_attempt(
    repository,
    *,
    attempt_id,
    created_at,
    correctness,
    session_id="sess_1",
    attempt_type="independent_attempt",
    facets=("recall",),
):
    with repository.connection() as connection:
        connection.execute(
            """
            INSERT INTO practice_attempts(
              id, practice_item_id, learning_object_id, practice_mode, attempt_type,
              learner_answer_md, hints_used, correctness, evidence_facets_json,
              created_at, session_id
            )
            VALUES (?, 'pi_svd_define_001', 'lo_svd_definition', 'short_answer', ?,
                    'my answer', 0, ?, ?, ?, ?)
            """,
            (
                attempt_id,
                attempt_type,
                correctness,
                '["' + '","'.join(facets) + '"]',
                created_at,
                session_id,
            ),
        )
        connection.commit()


def _insert_question(
    repository,
    *,
    created_at=QUESTION_ISO,
    question_type="mechanism",
    facets=("recall",),
    answer_status="answered",
    context="practice",
):
    return repository.insert_question_event(
        {
            "context": context,
            "practice_item_id": "pi_svd_define_001",
            "session_id": "sess_1",
            "question_md": "Why are the factors orthogonal?",
            "answer_md": "Think about the geometry." if answer_status == "answered" else None,
            "question_type": question_type if answer_status == "answered" else None,
            "facets": list(facets) if answer_status == "answered" else [],
            "hint_equivalent": answer_status == "answered",
            "answer_status": answer_status,
            "created_at": created_at,
        },
    )


# ── observation model ─────────────────────────────────────────────────────────


def test_question_observation_shifts_mass_away_from_solid():
    marginal = {"facet_solid:recall": 0.5, "facet_absent:recall": 0.3, "misconception:x": 0.2}
    updated = apply_question_observation(marginal, solid_likelihood_ratio=0.45)
    assert updated["facet_solid:recall"] < 0.5
    assert updated["facet_absent:recall"] > 0.3
    assert updated["misconception:x"] > 0.2
    # Relative mass among non-solid hypotheses is preserved.
    assert updated["facet_absent:recall"] / updated["misconception:x"] == pytest.approx(0.3 / 0.2)
    assert sum(updated.values()) == pytest.approx(1.0)


def test_neutral_ratio_is_a_noop():
    marginal = {"facet_solid:recall": 0.5, "facet_absent:recall": 0.5}
    updated = apply_question_observation(marginal, solid_likelihood_ratio=1.0)
    assert updated == pytest.approx(marginal)


# ── calibration ───────────────────────────────────────────────────────────────


def test_likelihood_falls_back_below_min_samples(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    resolved = resolve_question_likelihood(repository, vault.config.tutor_qa)
    assert resolved.source == "absolute_fallback"
    assert resolved.value == vault.config.tutor_qa.question_solid_likelihood_ratio


def test_likelihood_calibrates_from_question_failure_lift(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    # 12 questioned attempts that all failed, against a base of 12 passes.
    for index in range(12):
        q_at = f"2026-05-19T10:{index:02d}:00Z"
        a_at = f"2026-05-19T10:{index:02d}:30Z"
        _insert_question(repository, created_at=q_at)
        _insert_attempt(repository, attempt_id=f"att_fail_{index}", created_at=a_at, correctness=0.0)
    for index in range(12):
        _insert_attempt(
            repository,
            attempt_id=f"att_pass_{index}",
            created_at=f"2026-05-19T09:{index:02d}:00Z",
            correctness=1.0,
        )
    resolved = resolve_question_likelihood(repository, vault.config.tutor_qa)
    assert resolved.source == "empirical"
    assert resolved.sample_size == 12
    # Questions predict failure -> asking is strong evidence against solid.
    assert resolved.value < vault.config.tutor_qa.question_solid_likelihood_ratio


# ── resolution semantics (the regression that motivated all this) ────────────


def test_failed_attempt_does_not_resolve_question(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    _insert_question(repository, created_at=QUESTION_ISO)
    _insert_attempt(repository, attempt_id="att_fail", created_at=LATER_ISO, correctness=0.2)
    signal = collect_question_signal(vault, repository, "lo_svd_definition", clock=FrozenClock(NOW))
    assert "recall" in signal.events_by_facet


def test_successful_attempt_resolves_question(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    _insert_question(repository, created_at=QUESTION_ISO)
    _insert_attempt(repository, attempt_id="att_pass", created_at=LATER_ISO, correctness=1.0)
    signal = collect_question_signal(vault, repository, "lo_svd_definition", clock=FrozenClock(NOW))
    assert signal.events_by_facet == {}


def test_triggering_attempt_cannot_resolve_its_own_questions(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    _insert_question(repository, created_at=QUESTION_ISO)
    # The graded attempt itself succeeded the facet, but it is the attempt
    # under decision — excluded, so the mid-attempt question stays live.
    _insert_attempt(repository, attempt_id="att_current", created_at=LATER_ISO, correctness=1.0)
    signal = collect_question_signal(
        vault,
        repository,
        "lo_svd_definition",
        exclude_attempt_id="att_current",
        clock=FrozenClock(NOW),
    )
    assert "recall" in signal.events_by_facet


def test_non_substantive_and_unanswered_questions_are_ignored(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    _insert_question(repository, question_type="clarification")
    _insert_question(repository, answer_status="failed", created_at=LATER_ISO)
    signal = collect_question_signal(vault, repository, "lo_svd_definition", clock=FrozenClock(NOW))
    assert signal.events_by_facet == {}


# ── adjusted states ───────────────────────────────────────────────────────────


def test_virtual_open_state_for_questioned_facet_without_row(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    _insert_question(repository, created_at=QUESTION_ISO)
    states, signal = question_adjusted_uncertainty_states(
        vault, repository, "lo_svd_definition", clock=FrozenClock(NOW)
    )
    assert signal.events_by_facet
    virtual = [state for state in states if state.opened_reason == "tutor_question"]
    assert len(virtual) == 1
    state = virtual[0]
    assert state.facet_id == "recall"
    assert state.status == "open"
    ratio = signal.likelihood.value
    expected_solid = (0.5 * ratio) / (0.5 * ratio + 0.5)
    assert state.hypothesis_marginal["facet_solid:recall"] == pytest.approx(expected_solid)
    assert state.uncertainty > 0.0


def test_adjustment_disabled_by_config(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    vault.config.tutor_qa.apply_question_evidence = False
    _insert_question(repository, created_at=QUESTION_ISO)
    states, _signal = question_adjusted_uncertainty_states(
        vault, repository, "lo_svd_definition", clock=FrozenClock(NOW)
    )
    assert states == []


# ── follow-up wiring ──────────────────────────────────────────────────────────


def _evaluate(vault, repository, *, attempt_id):
    return evaluate_intervention_followup(
        vault,
        repository,
        attempt_id=attempt_id,
        learning_object_id="lo_svd_definition",
        practice_item_id="pi_svd_define_001",
        surprise_direction="negative",
        bayesian_surprise=1.0,
        grader_confidence=0.9,
        error_event_written=True,
        max_error_severity=0.9,
        target_facets=["recall"],
        clock=FrozenClock(NOW),
    )


def test_need_focus_carries_tutor_question_evidence(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    _insert_question(repository, created_at=QUESTION_ISO)
    _insert_attempt(repository, attempt_id="att_current", created_at=LATER_ISO, correctness=0.2)

    decision = _evaluate(vault, repository, attempt_id="att_current")
    assert decision.need_id is not None
    need = repository.intervention_need_for_attempt("att_current")
    focus = need["diagnostic_focus"]

    sources = focus["facet_source_scores"]["recall"]["sources"]
    assert any(source["source"] == "tutor_question" for source in sources)
    assert focus["tutor_question_context"]
    entry = focus["tutor_question_context"][0]
    assert "orthogonal" in entry["question_excerpt"]
    assert focus["question_likelihood"]["source"] in ("empirical", "absolute_fallback")
    assert "recall" in focus["target_facets"]
    assert focus["target_facet_marginals"]
    assert decision.gate_diagnostics is not None


def test_focus_has_no_question_keys_without_questions(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    _insert_attempt(repository, attempt_id="att_current", created_at=LATER_ISO, correctness=0.2)
    decision = _evaluate(vault, repository, attempt_id="att_current")
    assert decision.need_id is not None
    need = repository.intervention_need_for_attempt("att_current")
    focus = need["diagnostic_focus"]
    assert "tutor_question_context" not in focus
    assert all(
        source["source"] != "tutor_question"
        for payload in focus["facet_source_scores"].values()
        for source in payload["sources"]
    )


# ── two-phase persistence ─────────────────────────────────────────────────────


class FailingTutorClient:
    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-model"

    def run_tutor_qa(self, context):
        raise TimeoutError("provider down")


class WorkingTutorClient:
    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-model"

    def run_tutor_qa(self, context):
        return TutorAnswer(
            answer_md="Consider the factor geometry.",
            question_type="mechanism",
            facets=list(context.candidate_facets),
        )


def test_failed_provider_keeps_question_row_without_charging_budget(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    with pytest.raises(TimeoutError):
        ask_question(
            vault,
            repository,
            FailingTutorClient(),
            context="practice",
            question_md="Why are the factors orthogonal?",
            practice_item_id="pi_svd_define_001",
            session_id="sess_1",
            clock=FrozenClock(NOW),
        )
    events = repository.question_events(practice_item_id="pi_svd_define_001")
    assert len(events) == 1
    assert events[0]["answer_status"] == "failed"
    assert events[0]["answer_md"] is None
    assert events[0]["question_md"] == "Why are the factors orthogonal?"
    # Budget only counts answered turns.
    assert repository.count_question_events(
        context="practice",
        practice_item_id="pi_svd_define_001",
        session_id="sess_1",
        answer_status="answered",
    ) == 0
    runs = [run for run in _agent_runs(repository) if run["purpose"] == "tutor_qa"]
    assert len(runs) == 1
    assert runs[0]["status"] == "failed"


def test_successful_ask_records_answered_event_and_agent_run(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    result = ask_question(
        vault,
        repository,
        WorkingTutorClient(),
        context="practice",
        question_md="Why are the factors orthogonal?",
        practice_item_id="pi_svd_define_001",
        session_id="sess_1",
        clock=FrozenClock(NOW),
    )
    event = repository.question_event(result["event_id"])
    assert event["answer_status"] == "answered"
    assert event["question_type"] == "mechanism"
    runs = [run for run in _agent_runs(repository) if run["purpose"] == "tutor_qa"]
    assert len(runs) == 1
    assert runs[0]["status"] == "completed"


def _agent_runs(repository):
    with repository.connection() as connection:
        rows = connection.execute("SELECT purpose, status FROM agent_runs").fetchall()
    return [dict(row) for row in rows]
