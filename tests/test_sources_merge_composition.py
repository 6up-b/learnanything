"""The canonical-sources merge onto main: the composition points with main's
held-grade predicate, shared output-budget policy, EVSI forecast logging and
exam protection (each would otherwise break silently)."""
from __future__ import annotations

from contextlib import closing
from datetime import timedelta
from decimal import Decimal

import pytest

from learnloop.ai.execution import output_limit
from learnloop.ai.spend import SpendBudget, SpendCaps, SpendEnvelope, SpendEstimate, SpendLimitExceeded, spend_envelopes
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.content.authoring import source_exercise_import as SEI
from learnloop.content.authoring.ai_contracts import ExerciseAuthoring
from learnloop.db.connection import connect
from learnloop.outcome_contract import GRADE_HELD_FOR_REVIEW, HELD_ROW_KEY
from learnloop.source_retrieval.tutor import PinnedSpanProvider
from learnloop.substrate.intervention_outcomes import COLD_STATES, MEASURED_COLD_STATES, outcome_for
from tests.source_service_fakes import FakeServiceLLM, build_service_vault, build_textbook_vault, loaded
from tests.test_intervention_outcomes_replayer import T0, _attempt as _outcome_attempt, _intervention


def _exam_span(repository) -> str:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = connection.execute(
            "SELECT span_id FROM source_document_blocks WHERE extraction_id = 'ext_exam' AND text LIKE 'Exam question%'"
        ).fetchone()
    assert row is not None
    return str(row[0])


def _self_graded(paths, repository, item_id, *, points, hints=0):
    return complete_self_graded_attempt(
        loaded(paths), repository,
        AttemptDraft(practice_item_id=item_id, learner_answer_md="x", attempt_type="independent_attempt",
                     hints_used=hints),
        SelfGradeInput(criterion_points={"correct": points}, fatal_errors=[], confidence=3))


def _hold(monkeypatch, attempt_ids):
    """THE predicate says these attempts' grades are held for review."""

    import learnloop.held_grades as held_grades

    held = frozenset(attempt_ids)
    monkeypatch.setattr(held_grades, "held_for_review_attempts",
                        lambda _connection, ids=None: held if ids is None else held & {str(i) for i in ids})


# -- held grades --------------------------------------------------------------------------------


def test_a_held_grade_is_no_intervention_outcome(tmp_path):
    paths, _repository = build_service_vault(tmp_path / "vault")
    vault = loaded(paths)
    later = T0 + timedelta(days=2)
    assert GRADE_HELD_FOR_REVIEW in COLD_STATES and GRADE_HELD_FOR_REVIEW not in MEASURED_COLD_STATES
    cold = outcome_for(_intervention(), [_outcome_attempt("a", later, **{HELD_ROW_KEY: True})], vault,
                       as_of=later, signals=[])
    assert cold["cold_outcome_state"] == GRADE_HELD_FOR_REVIEW and cold["cold_correctness"] is None
    # It still occupies its place: a later attempt is not the next cold one.
    both = outcome_for(_intervention(), [_outcome_attempt("a", later, **{HELD_ROW_KEY: True}),
                                         _outcome_attempt("b", later + timedelta(hours=1))],
                       vault, as_of=later, signals=[])
    assert both["cold_attempt_id"] == "a" and both["cold_outcome_state"] == GRADE_HELD_FOR_REVIEW
    soon = outcome_for(_intervention(), [_outcome_attempt("n", T0 + timedelta(minutes=5), **{HELD_ROW_KEY: True})],
                       vault, as_of=later, signals=[])
    assert soon["next_attempt_id"] == "n" and soon["next_correctness"] is None


def test_a_held_success_neither_poses_nor_suppresses_retention(tmp_path, monkeypatch):
    from learnloop.instructional.valuation import recent_assisted_success

    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    assisted = _self_graded(paths, repository, "pi_determinant_2", points=4, hints=1)
    assert recent_assisted_success(loaded(paths), repository, "lo_matrices")["id"] == assisted.attempt_id
    _hold(monkeypatch, {assisted.attempt_id})
    assert recent_assisted_success(loaded(paths), repository, "lo_matrices") is None


def test_a_held_correct_grade_keeps_the_attempt_window_open(tmp_path, monkeypatch):
    from learnloop.instructional.policy import attempt_window_open

    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    attempt = _self_graded(paths, repository, "pi_determinant_1", points=4)
    assert attempt_window_open(repository, "pi_determinant_1") is False
    _hold(monkeypatch, {attempt.attempt_id})
    assert attempt_window_open(repository, "pi_determinant_1") is True


# -- exam material is assessment-only on the new paths ------------------------------------------


def test_a_pinned_exam_passage_never_grounds_the_tutor(tmp_path):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    vault = loaded(paths)
    exam = _exam_span(repository)
    definition = spans["ch5"][1]
    pinned, manifest = PinnedSpanProvider([f"ext_exam:{exam}", f"ext_text:{definition}"])(
        vault, repository, context="library", question_md="q", learning_object_ids=[], item=None)
    assert [span["span_id"] for span in pinned] == [definition]
    assert {entry["span_id"]: entry["reason"] for entry in manifest["dropped_pins"]} == {
        exam: "it is exam material"}


def test_find_sources_and_compare_never_hand_exam_material_to_a_model(tmp_path):
    from learnloop.source_retrieval.compare import compare_sources
    from learnloop.source_retrieval.find_sources import find_sources_for_caller
    from learnloop.source_retrieval.policy import CallerContext
    from tests.source_retrieval_fakes import EXAM_QUESTION

    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    vault = loaded(paths)
    exam = _exam_span(repository)
    hits = find_sources_for_caller(vault, repository, EXAM_QUESTION, caller=CallerContext(kind="reader"))
    assert all(hit["extraction_id"] != "ext_exam" for hit in hits.hits)
    assert hits.manifest["exam_withheld"] >= 1  # found, then withheld
    llm = FakeServiceLLM()
    result = compare_sources(vault, repository, EXAM_QUESTION, caller=CallerContext(kind="reader"),
                             client=llm, verify_client=llm, pinned_span_keys=[f"ext_exam:{exam}"])
    assert {entry["span_id"]: entry["reason"] for entry in result.dropped_pins} == {
        exam: "it is exam material"}
    assert all(source.get("extraction_id") != "ext_exam" for source in result.sources)
    assert result.manifest["exam_withheld"] >= 1


# -- main's output-budget policy on the import's authoring request ------------------------------


def test_authoring_runs_at_the_policy_budget_and_retries_a_truncation_once_at_double(tmp_path):
    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    vault = loaded(paths)
    admit = SEI.authoring_admission(vault, repository, FakeServiceLLM(), owner_id="sei_budget")
    with admit("prompt", ExerciseAuthoring):
        first = output_limit()
    assert first == 16_384  # ai.output_tokens, the shared default
    assert admit.after_truncation() is True
    with admit("prompt", ExerciseAuthoring):
        assert output_limit() == 2 * first
    assert admit.after_truncation() is False  # once only


# -- spend: a subscription route is never refused by a service envelope -------------------------


def test_a_subscription_route_reserves_nothing_in_a_spent_envelope():
    spent = SpendEnvelope("daily", 0.5, observed=lambda: 1.0)  # the day already passed its cap
    caps = SpendCaps(max_candidates=10, max_pairs=10, max_retries=1, max_calls=2, max_total_tokens=10_000,
                     max_estimated_usd=1.0)
    estimate = SpendEstimate(calls=1, total_tokens=0, estimated_usd=0.0)
    with spend_envelopes(spent):
        with pytest.raises(SpendLimitExceeded):
            with SpendBudget(caps).request(estimate):
                pass
        # PaidCalls on a Codex / ChatGPT-plan route: priced $0, never refused for money.
        with SpendBudget(caps).request(estimate, subscription_route=True) as charge:
            charge.note_estimated_only(total_tokens=1200, estimated_usd=None)
    assert spent.report()["estimated_only"]["tokens"] == 1200
    assert spent.remaining() == float(Decimal(0))


# -- EVSI calibration: a source-first need's value decision is a logged forecast ----------------


def test_a_decision_mode_valuation_records_its_forecast_when_logging_is_on(tmp_path):
    from learnloop.instructional.valuation import CandidateInput, PendingDecision, ValuationProblem, rank_listener
    from learnloop.instructional.valuation import value_problem
    from learnloop.scheduling import action_loss as AL
    from learnloop.scheduling import voi_forecasts as VF

    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    vault = loaded(paths)
    assert "source_need_selection" in VF.VOI_SITES
    table = AL.build_loss_table(routes=[{"reason": "h1", "first_intervention": "repair_a"},
                                        {"reason": "h2", "first_intervention": "repair_b"}],
                                duration_overrides={"repair_a": 10.0, "repair_b": 10.0})
    problem = ValuationProblem(key="causal:f", space_kind="causal_factor", slots=("h1", "h2"),
                               prior={"h1": 0.5, "h2": 0.5}, prior_basis="support_weighted", state_hash="c",
                               decision=PendingDecision("repair_class", {"h1": "repair_a", "h2": "repair_b"}, table))
    sharp = CandidateInput(ref="sharp", kind="item", members=({"h1": {"x": 1.0}, "h2": {"y": 1.0}},),
                           outcome_alphabet=("x", "y"), regime="pinned_channel", construction="p", expected_minutes=1.0)
    seen = []

    def listener(*, problem, result, candidates, loss_table):
        seen.append(VF.record_rank_feasible_forecast(
            repository, vault=vault, site="source_need_selection", receipt_key=f"t:{problem.state_hash}",
            result=result, candidates=candidates, loss_table=loss_table))

    with rank_listener(listener):
        report = value_problem(problem, [sharp])
    without = value_problem(problem, [sharp])
    assert report == without  # logging never changes the decision
    assert len(seen) == 1 and seen[0] is not None
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        assert connection.execute("SELECT site FROM voi_forecasts WHERE id = ?", (seen[0],)).fetchone()[0] == \
            "source_need_selection"
