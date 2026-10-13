"""The stuck prompt (mvp-0.13) composed with what main gained before it merged.

The branch was built as mvp-0.11 over mvp-0.10; at the merge it became
mvp-0.13 over placement (mvp-0.11) and recurrence groups (mvp-0.12), with the
PF-c unassessed rule and R0's judgment_ledger. These tests pin how a stuck
answer meets each of them; all model calls are fakes.
"""

from __future__ import annotations

from types import SimpleNamespace

from learnloop.attempts.attempts import AttemptDraft, complete_attempt_with_ai_required
from learnloop.attempts.grading_support import REFERENCE_POLICY_PROMPT_VERSION
from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop.attempts.stuck import STUCK_READING_JUDGMENT_TASK, STUCK_READING_KEY, stuck_answers
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.placement.decisions import record_self_report
from learnloop.placement.rules import MISS_TO_LEARNING
from learnloop.placement.signals import blocking_signals_by_lo, taught_first_learning_objects
from learnloop.placement.state import load_answers
from learnloop.recurrence import recurrence_key
from learnloop.substrate.canonical_projection import (
    UNVERIFIED_INTERPRETATION_KEY,
    project_canonical_facet_state,
    unassessed_evidence_row,
)

from tests.diagnosis_fakes import FakeEmbeddingClient
from tests.recurrence_fakes import StatementFake, shares_word
from tests.split_live_helpers import ReadyRuntime, at, drain_jobs, split_vault, submit
from tests.test_pfc_unverified_unassessed import _mapped_split_vault, _mass, _support
from tests.test_placement_diagnosis_decides import DUE_HOURS, LO, WRONG, _Diagnosed, _state
from tests.test_recurrence_live import STATEMENTS, _heads
from tests.test_recurrence_live import _vault as _recurrence_vault
from tests.test_stuck_prompt import StuckFake, _draft

R0_JUDGES = {"llm", "verifier", "owner", "diagnoser", "learner_card", "exact_key", "decider"}
CONFUSED = {"attempts_answer": False, "describes_confusion": True, "confusion_quote": "why V is transposed"}


def _with_reading(model, base, reading):
    """The stuck wire model around ``base`` (what StuckFake returns)."""

    return model.model_validate({**base.model_dump(mode="json"), "stuck_reading": reading})


def _stuck(vault, repository, client, answer: str, *, item="pi_svd_compute_001", hours: float, drain=True, **drain_kwargs):
    clock = FrozenClock(at(hours))
    result = complete_attempt_with_ai_required(
        vault, repository, _draft(answer, item_id=item), runtime=ReadyRuntime(), ai_client=client, clock=clock,
    )
    run_post_attempt_pipeline(vault, repository, result=result, clock=clock)
    if drain:
        drain_jobs(vault, repository, client, clock=FrozenClock(at(hours + 0.5)), **drain_kwargs)
    return result


# -- PF-c ----------------------------------------------------------------------------


class _StuckPartial(StuckFake):
    """A stuck reading, and ``result`` given half its points with no error named
    (the PF-c complement-route shape of tests/test_pfc_unverified_unassessed)."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        evidence = [
            row.model_copy(update={"points_awarded": 1.0}) if row.criterion_id == "result" else row
            for row in result.criterion_evidence
        ]
        return result.model_copy(update={
            "criterion_evidence": evidence,
            "rubric_score": int(sum(row.points_awarded for row in evidence)),
            "error_attributions": [],
        })


def test_a_stuck_answers_pfc_unverified_criteria_are_unassessed(tmp_path):
    """A stuck answer that verifies by another route is graded under the PF-c
    reference policy AND the stuck rules: its unverified criterion is
    unassessed exactly as on any other answer (out of the grade, no facet
    evidence either way), and the stuck reading is recorded beside it."""

    _paths, vault, repository = _mapped_split_vault(tmp_path, "mvp-0.13")
    project_canonical_facet_state(vault, repository)
    recall_before = _mass(repository, "recall")
    answer = "I'm not sure why this route works.\nFinal answer: U Sigma V^T"
    result = _stuck(vault, repository, _StuckPartial(reading=CONFUSED), answer, hours=20, drain=False)

    attempt = repository.fetch_practice_attempt(result.attempt_id)
    assert attempt["declared_stuck"] is True
    assert (attempt["rubric_score"], attempt["correctness"]) == (4, 1.0)
    support = _support(repository, result.attempt_id)
    assert support["unverified_criterion_ids"] == ["result"]
    assert support["assessed_shortfall"] is False and UNVERIFIED_INTERPRETATION_KEY in support
    record = repository.latest_blind_grade_record(result.attempt_id)
    assert record["record"][STUCK_READING_KEY]["describes_confusion"] is True
    assert record["grading_prompt_version"] == f"{REFERENCE_POLICY_PROMPT_VERSION}+stuck-v1"
    rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(result.attempt_id)}
    assert unassessed_evidence_row(rows["result"].attribution_json)
    assert not unassessed_evidence_row(rows["setup"].attribution_json)
    assert _mass(repository, "recall") == recall_before
    with connect(repository.sqlite_path, read_only=True) as connection:
        (row,) = stuck_answers(connection)
        judges = {
            judge for (judge,) in connection.execute(
                "SELECT judge FROM judgment_ledger WHERE task = ?", (STUCK_READING_JUDGMENT_TASK,)
            )
        }
    assert row["attempt_id"] == result.attempt_id and row["describes_confusion"] is True
    # The grader's reading is an llm judgment, one of R0's seven judges.
    assert judges == {"llm"} <= R0_JUDGES


# -- placement -------------------------------------------------------------------------


def _assumed(tmp_path):
    paths, vault, repository = split_vault(tmp_path, version="mvp-0.13", seed=False)
    result = record_self_report(
        vault, repository, learning_object_ids=[LO], report="know_this", clock=FrozenClock(at(0)),
    )
    assert {row["status"] for row in result["results"]} == {"assumed"}
    return paths, vault, repository


def test_an_empty_stuck_answer_on_an_assumed_topic_takes_todays_rule_at_once(tmp_path):
    """No diagnosis can arrive for an empty stuck answer (nothing to read; no
    blind grade is recorded), so its miss is decided with the answer by
    today's rule: the topic goes back to learning (reason ``no_diagnosis``,
    fallback ``not_blind_graded``)."""

    _paths, vault, repository = _assumed(tmp_path)
    empty = _stuck(vault, repository, StuckFake(), "", hours=DUE_HOURS + 1)
    assert repository.latest_blind_grade_record(empty.attempt_id) is None
    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.resolving_attempt_id, assumption.resolution_reason) == (
        "failed", empty.attempt_id, "no_diagnosis",
    )
    assert assumption.resolution.outcome == MISS_TO_LEARNING
    assert assumption.resolution.fallback == "not_blind_graded"
    assert intent.intent == "learning" and assumption.awaiting_diagnosis_attempt_id is None


def test_an_empty_stuck_answer_is_a_miss_not_learner_side_help(tmp_path):
    """Unlike "don't know" (learner-side help, today's rule at once), an empty
    stuck answer is an ordinary answer scored 0: behind an earlier miss whose
    diagnosis is pending it waits like any later miss. Once that miss is kept
    (a slip: the check passes into maintenance), the empty answer is a lapse
    in maintenance that no diagnosis can read: today's rule, back to
    learning."""

    _paths, vault, repository = _assumed(tmp_path)
    client = _Diagnosed(causal_class="transient_execution")
    first = submit(vault, repository, client, answer=WRONG, when=at(DUE_HOURS + 1))
    empty = _stuck(vault, repository, client, "", item="pi_svd_compute_002", hours=DUE_HOURS + 2, drain=False)
    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.awaiting_diagnosis_attempt_id, intent.intent) == (
        "open", first.attempt_id, "assumed",
    )
    drain_jobs(vault, repository, client, clock=FrozenClock(at(DUE_HOURS + 3)))
    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.resolving_attempt_id, assumption.resolution_reason) == (
        "passed", first.attempt_id, "slip",
    )
    assert (intent.intent, intent.reason, intent.outcome_reason) == (
        "learning", "missed_in_maintenance", "no_diagnosis",
    )
    assert intent.resolution is not None and intent.resolution.attempt_id == empty.attempt_id
    assert intent.resolution.fallback == "not_blind_graded"


def test_a_stuck_answer_with_text_that_misses_is_decided_by_its_diagnosis(tmp_path):
    for causal_class, expected in (("transient_execution", ("passed", "slip")), ("learner_state", ("failed", "knowledge_gap"))):
        _paths, vault, repository = _assumed(tmp_path / causal_class)

        class _StuckDiagnosed(_Diagnosed):
            def _blind_grading(self, request, context):
                model = request.result_model
                if "stuck_reading" not in getattr(model, "model_fields", {}):
                    return super()._blind_grading(request, context)
                base = super()._blind_grading(SimpleNamespace(result_model=model.__mro__[1]), context)
                return _with_reading(model, base, CONFUSED)

        miss = _stuck(vault, repository, _StuckDiagnosed(causal_class=causal_class), WRONG, hours=DUE_HOURS + 1)
        assert repository.current_live_diagnosis(miss.attempt_id) is not None
        assumption, _intent = _state(vault, repository)
        assert (assumption.status, assumption.resolution_reason) == expected, causal_class
        assert assumption.resolution is None or assumption.resolution.fallback is None


def test_a_confused_stuck_answer_keeps_its_topic_out_of_fast_track(tmp_path):
    """``stuck_confusion`` is in main's fast-track blocking set, so placement
    teaches the LO first, through the shared field rule."""

    _paths, vault, repository = _assumed(tmp_path)
    confused = _stuck(vault, repository, StuckFake(reading=CONFUSED), "why is V transposed here?", hours=20)
    plain = _stuck(
        vault, repository, StuckFake(), "U Sigma then something", item="pi_transpose_001", hours=21,
    )
    with repository.connection() as connection:
        blocking = blocking_signals_by_lo(connection, vault, load_answers(connection))
    assert blocking.get(LO) == (f"stuck:{confused.attempt_id}",)
    assert not any(signal == f"stuck:{plain.attempt_id}" for ids in blocking.values() for signal in ids)
    assert taught_first_learning_objects(vault, repository, [LO, "lo_transpose"]) == {LO}


# -- recurrence groups -------------------------------------------------------------------


class _StuckStatementFake(StatementFake):
    def _blind_grading(self, request, context):
        model = request.result_model
        if "stuck_reading" not in getattr(model, "model_fields", {}):
            return super()._blind_grading(request, context)
        base = super()._blind_grading(SimpleNamespace(result_model=model.__mro__[1]), context)
        return _with_reading(model, base, CONFUSED)


def test_stuck_answers_hypotheses_join_recurrence_groups_and_count_toward_k(tmp_path):
    """A diagnosed stuck answer is an ordinary answer to recurrence: its
    hypothesis joins the group the judge merges, and it counts toward the
    third-time escalation."""

    _paths, vault, repository = _recurrence_vault(tmp_path, version="mvp-0.13")
    client = _StuckStatementFake(STATEMENTS, decide=shares_word("transpos"), operators={"third": "worked_contrast"})
    embedder = FakeEmbeddingClient()
    first = submit(vault, repository, client, item_id="pi_svd_compute_001", answer="A = U Sigma V first", when=at(10))
    drain_jobs(vault, repository, client, embedding=embedder, judge_factory=lambda: client, clock=FrozenClock(at(11)))
    second = _stuck(
        vault, repository, client, "B = U Sigma V second? I'm not sure", item="pi_svd_compute_002", hours=12,
        embedding=embedder, judge_factory=lambda: client,
    )
    third = submit(vault, repository, client, item_id="pi_svd_compute_001", answer="A = U Sigma V third", when=at(14))
    drain_jobs(vault, repository, client, embedding=embedder, judge_factory=lambda: client, clock=FrozenClock(at(15)))

    assert repository.fetch_practice_attempt(second.attempt_id)["declared_stuck"] is True
    groups = repository.recurrence_group_map()
    keys = {recurrence_key(_heads(repository, result.attempt_id)[0], groups) for result in (first, second, third)}
    assert len(keys) == 1
    escalation = repository.recurrence_escalation(repository.current_live_diagnosis(third.attempt_id)["id"])
    assert escalation is not None and escalation["recurrence_count"] == 3
    assert escalation["earlier_attempt_ids"] == [second.attempt_id, first.attempt_id]
