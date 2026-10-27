"""Reader CA2, one Ask (docs/specs/ux_reader_compare_ask_v1.md §7, K5-K10, §15 Q2-Q5;
docs/reviews/reader-ca2-one-ask.md), backend.

* **The successor (mvp-0.35; mvp-0.34 on the branch, ``ask.cold_help_converts``).** One help rule on a
  check on your own: a cold question counts as help only when the tutor's
  ``question_type`` is substantive, on the Reader's cold paths too (K10); help
  taken on a cold follow-up makes the attempt practice with help, admitted and
  never the cold measurement (Q4). Off, or below the tag: the predecessor.
* **The panel (``ask.panel_enabled``).** The practice thread is the attempt's
  (K5); so is the budget on a metered route (owner 2026-10-26: B3's
  per-attempt rule kept; a subscription route has none, F8);
  the help style is Ask's answer mode on every host (§7.4, Q5); a Work-in-Steps
  question names a workbench session the server checks (K7); *earlier on this
  question* lists earlier attempts' help, absent on a cold check (K6, Q2); the
  answer's question type carries its receipt.
"""
from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import timedelta

import pytest

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop import serve_eligibility as se
from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    ONE_ASK_ALGORITHM_VERSION,
    ONE_ASK_VERSIONS,
    REPLAY_LEDGER_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.tutor import reader_modes
from learnloop.tutor.ai_contracts import TutorAnswer, tutor_qa_prompt
from learnloop.tutor.tutor_qa import (
    HELP_STYLE_ANSWER_MODES,
    ask_question,
    earlier_threads,
    practice_thread_events,
    question_usage,
)
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext, config_dto
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.helpers import NOW, NOW_ISO, create_basic_vault
from tests.structured_ai import StructuredClientFake
from tests.ux_phase1_support import set_config

ITEM = "pi_svd_define_001"
TAG = ONE_ASK_ALGORITHM_VERSION


class FakeTutor(StructuredClientFake):
    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-model"

    def __init__(self, question_type: str = "mechanism") -> None:
        self.question_type = question_type
        self.contexts: list = []

    def run_tutor_qa(self, context):
        self.contexts.append(context)
        return TutorAnswer(answer_md="Think about the shapes.", question_type=self.question_type,
                           facets=list(context.candidate_facets))


def _vault(tmp_path, updates: dict | None = None):
    """A basic vault at the successor's tag (the basic vault is mvp-0.6)."""

    paths = create_basic_vault(tmp_path / "vault")
    set_config(paths.root, {("algorithms", "algorithm_version"): TAG, **(updates or {})})
    return paths, load_vault(paths.root), Repository(paths.sqlite_path)


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _rows(paths, sql, params=()):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(sql, params)]


# -- the successor's vocabulary, switch and upgrade --------------------------------------------------


def test_the_successor_is_one_constant_after_rebuild_equivalence():
    from learnloop.config.schema import AskConfig
    from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, defaults_fingerprint_for_version
    from learnloop.one_ask_upgrade import PREDECESSOR
    from learnloop.params.parameter_registry import classify_config_path

    # Built after RW7b's mvp-0.32 as mvp-0.34; the batch landing renumbered it after rebuild equivalence's mvp-0.34.
    # The kept replaced claims' mvp-0.36 follows it as the latest (and keeps it).
    assert SUCCESSOR_CHAIN[-2] == TAG == "mvp-0.35" and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.36"
    assert SUCCESSOR_CHAIN[-3] == PREDECESSOR == REPLAY_LEDGER_ALGORITHM_VERSION == "mvp-0.34"
    assert ONE_ASK_VERSIONS == frozenset({TAG, "mvp-0.36"})
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[TAG] == defaults_fingerprint_for_version(TAG)
    assert AskConfig().panel_enabled is True and AskConfig().cold_help_converts is True
    for key in ("ask.panel_enabled", "ask.cold_help_converts"):
        assert classify_config_path(key) is not None


def test_the_rule_is_live_only_at_the_tag_with_its_switch(tmp_path):
    _paths, vault, _repository = _vault(tmp_path)
    assert vault.config.algorithms.algorithm_version == TAG
    assert se.help_converts_active(vault)
    off_paths, off, _ = _vault(tmp_path / "off", {("ask", "cold_help_converts"): False})
    assert not se.help_converts_active(off)
    below_paths, below, _ = _vault(tmp_path / "below", {("algorithms", "algorithm_version"): PREDECESSOR_TAG})
    assert not se.help_converts_active(below)
    assert not se.help_converts_active(None)


# The immediate predecessor since the batch landing (rebuild equivalence's mvp-0.34; RW7b's mvp-0.32 on the branch).
PREDECESSOR_TAG = REPLAY_LEDGER_ALGORITHM_VERSION


def test_the_upgrade_moves_the_predecessor_and_refuses_twice(tmp_path):
    from learnloop.one_ask_upgrade import upgrade_to_one_ask

    paths, _vault_, _ = _vault(tmp_path, {("algorithms", "algorithm_version"): PREDECESSOR_TAG})
    result = upgrade_to_one_ask(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == (PREDECESSOR_TAG, TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
    again = upgrade_to_one_ask(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


# -- Q4: help taken on a cold follow-up converts the attempt ----------------------------------------


def _cold_inputs(*, hints: int, help_converts: bool, primed: bool = False) -> se.EligibilityInputs:
    task = se.FollowupTask(id="task_cold", kind="cold_retry", created_at="2026-05-01T00:00:00Z",
                           not_before="2026-05-02T00:00:00Z", expires_at="2026-06-30T00:00:00Z")
    return se.EligibilityInputs(practice_item_id=ITEM, learning_object_id=None, at="2026-05-03T00:00:00Z",
                                tasks=(task,), hints_used=hints, declared_primed=primed,
                                help_converts=help_converts)


def test_the_predecessor_refuses_a_hinted_cold_check_and_the_successor_converts_it():
    refused = se.decide(_cold_inputs(hints=1, help_converts=False), se.SUBMIT)
    assert refused.verdict == se.REFUSE and refused.reason == se.COLD_CHECK_ASSISTED
    converted = se.decide(_cold_inputs(hints=1, help_converts=True), se.SUBMIT)
    assert converted.verdict == se.SERVE and converted.reason == se.COLD_CHECK_HELP_TAKEN
    # It claims no task: the cold measurement is not answered by an assisted attempt.
    assert converted.task_ids == () and not converted.writes
    # Help that showed the answer converts too (the attempt is practice either way).
    assert se.decide(_cold_inputs(hints=1, help_converts=True, primed=True), se.SUBMIT).verdict == se.SERVE


def test_without_help_the_cold_rules_are_unchanged():
    clean = se.decide(_cold_inputs(hints=0, help_converts=True), se.SUBMIT)
    assert clean.verdict == se.SERVE and clean.reason == se.ELIGIBLE and clean.task_ids == ("task_cold",)
    primed = se.decide(_cold_inputs(hints=0, help_converts=True, primed=True), se.SUBMIT)
    assert primed.verdict == se.REFUSE


def _repair_at(tmp_path, *, converts: bool):
    from tests.test_remediation_cold_retry import _setup

    vault, repository, misconception_id = _setup(tmp_path)
    set_config(vault.root, {("algorithms", "algorithm_version"): TAG,
                            ("ask", "cold_help_converts"): converts})
    return load_vault(vault.root), repository, misconception_id


def test_a_hinted_cold_retry_is_practice_with_help_and_never_consumes_the_measurement(tmp_path):
    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
    from tests.test_remediation_cold_retry import NOW as REPAIR_NOW, _drive_to_cold_scheduled

    vault, repository, misconception_id = _repair_at(tmp_path, converts=True)
    episode, _primed, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)
    moment = REPAIR_NOW + timedelta(days=1, hours=1)
    at = moment.strftime("%Y-%m-%dT%H:%M:%SZ")
    task = repository.active_followup_task_for_item(cold_item, kind="cold_retry", at=at)
    assert task is not None
    result = complete_self_graded_attempt(
        vault, repository, AttemptDraft(practice_item_id=cold_item, learner_answer_md="an answer", hints_used=1),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=3), clock=FrozenClock(moment),
    )
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    assert attempt["hints_used"] == 1
    assert repository.consumed_followup_task_for_attempt(result.attempt_id, kind="cold_retry") is None
    assert repository.followup_task(task["id"])["status"] in {"pending", "served"}
    assert repository.remediation_episode(episode["id"])["state"] == "cold_scheduled"


def test_switched_off_a_hinted_cold_retry_is_refused_as_before(tmp_path):
    from learnloop.attempts.attempts import (
        AttemptDraft,
        AttemptValidationError,
        SelfGradeInput,
        complete_self_graded_attempt,
    )
    from tests.test_remediation_cold_retry import NOW as REPAIR_NOW, _drive_to_cold_scheduled

    vault, repository, misconception_id = _repair_at(tmp_path, converts=False)
    _episode, _primed, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)
    with pytest.raises(AttemptValidationError, match="a cold retry must be unassisted and unprimed: hints were used"):
        complete_self_graded_attempt(
            vault, repository, AttemptDraft(practice_item_id=cold_item, learner_answer_md="an answer", hints_used=1),
            SelfGradeInput(criterion_points={"correctness": 4}, confidence=3),
            clock=FrozenClock(REPAIR_NOW + timedelta(days=1, hours=1)),
        )


def test_an_assisted_attempt_is_recognised():
    from learnloop.diagnosis.remediation import assisted_attempt

    assert assisted_attempt({"hints_used": 1})
    assert assisted_attempt({"hints_used": 0, "attempt_type": "hinted_attempt"})
    assert assisted_attempt({"hints_used": 0, "primed": 1})
    assert not assisted_attempt({"hints_used": 0, "attempt_type": "independent_attempt", "primed": 0})


def test_a_due_cold_follow_up_is_served_with_the_take_step(tmp_path):
    from learnloop.intent.checks import HELP_LADDER_HEADER, cold_followup_view
    from tests.test_remediation_cold_retry import NOW as REPAIR_NOW, _drive_to_cold_scheduled

    vault, repository, misconception_id = _repair_at(tmp_path, converts=True)
    _episode, _primed, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)
    later = REPAIR_NOW + timedelta(days=1, hours=1)
    view = cold_followup_view(vault, repository, cold_item, now=later)
    assert view is not None and view["help_header"] == HELP_LADDER_HEADER and view["locators_hidden"] is True
    assert cold_followup_view(vault, repository, cold_item, now=REPAIR_NOW) is None  # not due yet
    off_vault, off_repository, off_misconception = _repair_at(tmp_path / "off", converts=False)
    _e, _p, off_item = _drive_to_cold_scheduled(off_vault, off_repository, off_misconception)
    assert cold_followup_view(off_vault, off_repository, off_item, now=later) is None


# -- K10: the Reader's cold Ask counts only substantive questions -------------------------------------


@pytest.mark.parametrize("cold_every", [True, False])
@pytest.mark.parametrize("substantive", [True, False])
def test_the_bound_cold_ask_follows_the_rule(cold_every, substantive):
    binding = reader_modes.BoundAsk(item=object(), cold=True, cold_counts_every_question=cold_every)
    assert binding.hint_equivalent(substantive) is (substantive or cold_every)
    warm = reader_modes.BoundAsk(item=object(), cold=False, cold_counts_every_question=cold_every)
    assert warm.hint_equivalent(substantive) is substantive


@pytest.mark.parametrize("converts", [True, False])
@pytest.mark.parametrize("question_type", ["clarification", "mechanism"])
def test_the_readers_cold_paths_count_a_clarification_only_under_the_predecessor(tmp_path, monkeypatch,
                                                                                converts, question_type):
    from tests.reader_tutor_fakes import LookupTutor, ask, reader_ctx
    from tests.test_reader_rw1c_review import ITEM as READER_ITEM, _bound_to, _cold_attempt

    from tests.test_reader_rw1c_review import _rebind

    tutor = LookupTutor(question_type=question_type)
    paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    set_config(paths.root, {("algorithms", "algorithm_version"): TAG, ("ask", "cold_help_converts"): converts})
    ctx = _rebind(paths, ctx)
    vault, _repository = ctx.require_vault()
    assert vault.config.algorithms.algorithm_version == TAG
    session = repository.create_session()
    counts = converts is False or question_type == "mechanism"
    # Bound to a workbench item, cold.
    bound = ask(ctx, workbenchSessionId=_bound_to(repository, READER_ITEM, session), coldActive=True)
    assert repository.question_event(bound["eventId"])["hint_equivalent"] is counts
    assert bound["hintEquivalent"] is counts
    # Unbound, naming the client's cold attempt: the practice link row.
    _cold_attempt(repository, vault, "att_cold_ca2", session)
    plain = ask(ctx, "what does this symbol mean?", coldActive=True, coldAttemptId="att_cold_ca2")
    assert plain["hintEquivalent"] is counts
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT hint_equivalent, question_type FROM question_events WHERE context = 'practice' "
            "AND provider = 'reader' AND attempt_id = 'att_cold_ca2'").fetchone()
    assert bool(row["hint_equivalent"]) is counts
    assert row["question_type"] == (question_type if converts else "other")


# -- K5: the practice thread is the attempt's, and so is the budget (owner 2026-10-26: B3's rule) ----


def test_the_practice_thread_and_its_budget_are_keyed_by_the_attempt(tmp_path):
    _paths, vault, repository = _vault(tmp_path)
    clock = FrozenClock(NOW)
    for key, question in (("serve-1", "Why orthogonal?"), ("serve-2", "What is a singular value?")):
        ask_question(vault, repository, FakeTutor(), context="practice", question_md=question,
                     practice_item_id=ITEM, session_id="sess_1", submission_id=key, clock=clock)
    thread = practice_thread_events(repository, practice_item_id=ITEM, session_id="sess_1", submission_id="serve-2")
    assert [event["question_md"] for event in thread] == ["What is a singular value?"]
    # The question each serve's tutor is given: only its own turns (C6).
    tutor = FakeTutor()
    ask_question(vault, repository, tutor, context="practice", question_md="And then?", practice_item_id=ITEM,
                 session_id="sess_1", submission_id="serve-2", clock=clock)
    assert [turn["question_md"] for turn in tutor.contexts[0].thread] == ["What is a singular value?"]
    # The budget is the attempt's (owner decision 2026-10-26, B3's rule kept):
    # each serve gets its own max_questions_practice, counted over its thread.
    used, limit = question_usage(vault, repository, context="practice", practice_item_id=ITEM, session_id="sess_1",
                                 submission_id="serve-2", clock=clock)
    assert (used, limit) == (2, vault.config.tutor_qa.max_questions_practice)
    used, _limit = question_usage(vault, repository, context="practice", practice_item_id=ITEM,
                                  session_id="sess_1", submission_id="serve-1", clock=clock)
    assert used == 1
    stored = repository.question_events(context="practice", practice_item_id=ITEM)
    assert [event["source_context"]["attempt_key"]["submission_id"] for event in stored] == [
        "serve-1", "serve-2", "serve-2"]


def test_panel_off_the_thread_and_budget_are_b3s(tmp_path):
    _paths, vault, repository = _vault(tmp_path, {("ask", "panel_enabled"): False})
    clock = FrozenClock(NOW)
    ask_question(vault, repository, FakeTutor(), context="practice", question_md="Why?", practice_item_id=ITEM,
                 session_id="sess_1", clock=clock)
    used, _limit = question_usage(vault, repository, context="practice", practice_item_id=ITEM, session_id="sess_1",
                                  clock=clock)
    assert used == 1
    [event] = repository.question_events(context="practice", practice_item_id=ITEM)
    assert "attempt_key" not in (event["source_context"] or {})


# -- §7.4: the help style is the answer mode -----------------------------------------------------------


def test_a_practice_answer_mode_reaches_the_prompt_and_the_row(tmp_path):
    from learnloop.tutor.ai_contracts import TUTOR_QA_ANSWER_MODE_SUFFIX, TUTOR_QA_PROMPT_VERSION

    _paths, vault, repository = _vault(tmp_path)
    tutor = FakeTutor(question_type="clarification")
    result = ask_question(vault, repository, tutor, context="practice", question_md="What does V mean?",
                          practice_item_id=ITEM, session_id="sess_1", answer_mode="ask_me_first",
                          clock=FrozenClock(NOW))
    assert result["answer_mode"] == "ask_me_first"
    context = tutor.contexts[0]
    assert context.answer_mode == "ask_me_first"
    assert "ASK ME FIRST" in tutor_qa_prompt(context)
    [event] = repository.question_events(context="practice", practice_item_id=ITEM)
    assert event["answer_mode"] == "ask_me_first"
    receipt = event["source_context"]["receipt"]
    assert receipt["model"] == "fake-model"
    assert receipt["prompt_version"] == TUTOR_QA_PROMPT_VERSION + TUTOR_QA_ANSWER_MODE_SUFFIX
    assert receipt["agent_run_id"]


def test_without_a_mode_the_practice_prompt_is_todays(tmp_path):
    from learnloop.tutor.ai_contracts import TUTOR_QA_PROMPT_VERSION

    _paths, vault, repository = _vault(tmp_path)
    tutor = FakeTutor()
    ask_question(vault, repository, tutor, context="practice", question_md="Why?", practice_item_id=ITEM,
                 session_id="sess_1", clock=FrozenClock(NOW))
    assert tutor.contexts[0].answer_mode is None
    prompt = tutor_qa_prompt(tutor.contexts[0])
    assert "Answer mode" not in prompt and TUTOR_QA_PROMPT_VERSION in prompt
    [event] = repository.question_events(context="practice", practice_item_id=ITEM)
    assert event["answer_mode"] is None


def test_the_three_styles_map_to_the_three_modes():
    assert HELP_STYLE_ANSWER_MODES == {"let_me_struggle": "ask_me_first", "balanced": "help_me_reason",
                                       "guide_me": "answer_directly"}


@pytest.fixture
def sidecar(tmp_path, monkeypatch):
    import learnloop_sidecar.handlers.tutor_qa as handler

    tutor = FakeTutor(question_type="clarification")

    class Ready:
        ready = True

    monkeypatch.setattr(handler, "ready_tutor_qa_provider", lambda vault: ("fake", Ready(), tutor))

    def build(updates: dict | None = None):
        paths, _vault_, _repository = _vault(tmp_path, updates)
        ctx = SidecarContext()
        ctx.load(paths.root)
        return paths, ctx, tutor

    return build


def test_the_sidecar_asks_in_the_help_styles_mode_unless_changed_for_one_question(sidecar):
    paths, ctx, tutor = sidecar({("hints", "help_style"): "guide_me"})
    base = {"context": "practice", "practiceItemId": ITEM, "sessionId": "sess_1", "submissionId": "k1"}
    answer = _call(ctx, "ask_tutor_question", {**base, "question": "What does this symbol mean?"})
    assert answer["answerMode"] == "answer_directly" and tutor.contexts[-1].answer_mode == "answer_directly"
    changed = _call(ctx, "ask_tutor_question", {**base, "question": "And this one?", "answerMode": "ask_me_first"})
    assert changed["answerMode"] == "ask_me_first"
    transcript = _call(ctx, "get_tutor_transcript", {"context": "practice", "practiceItemId": ITEM,
                                                     "sessionId": "sess_1", "submissionId": "k1"})
    assert [event["questionMd"] for event in transcript["events"]] == [
        "What does this symbol mean?", "And this one?"]
    other = _call(ctx, "get_tutor_transcript", {"context": "practice", "practiceItemId": ITEM,
                                                "sessionId": "sess_1", "submissionId": "k2"})
    # The default route is the subscription's: no request bound on either serve
    # (Codex review F8, kept by the owner 2026-10-26); a metered route's
    # per-attempt cap is pinned in tests/test_reader_ca2_codex_review.py.
    assert other["events"] == [] and other["remaining"] is None and transcript["remaining"] is None
    assert other["cold"] is False and other["earlierCountsAsHint"] is True


def test_panel_off_the_sidecar_asks_as_before(sidecar):
    from learnloop_sidecar.errors import SidecarError

    paths, ctx, tutor = sidecar({("ask", "panel_enabled"): False})
    base = {"context": "practice", "practiceItemId": ITEM, "sessionId": "sess_1"}
    answer = _call(ctx, "ask_tutor_question", {**base, "question": "Why?", "submissionId": "k1"})
    assert answer["answerMode"] is None and tutor.contexts[-1].answer_mode is None
    with pytest.raises(SidecarError):
        _call(ctx, "ask_tutor_question", {**base, "question": "Why?", "answerMode": "ask_me_first"})
    transcript = _call(ctx, "get_tutor_transcript", {**base, "submissionId": "other"})
    assert "earlier" not in transcript and len(transcript["events"]) == 1
    vault, _ = ctx.require_vault()
    assert "ask" not in config_dto(vault)


def test_a_steps_question_names_its_items_workbench_and_its_step(sidecar):
    from learnloop_sidecar.errors import SidecarError
    from tests.test_reader_tutor_retrieval import _bound_session

    paths, ctx, tutor = sidecar()
    _vault_, repository = ctx.require_vault()
    mine = _bound_session(repository, ITEM)
    base = {"context": "practice", "practiceItemId": ITEM, "sessionId": "sess_1", "submissionId": "k1",
            "learnerDraftMd": "1. A = U S V^T"}
    answer = _call(ctx, "ask_tutor_question", {**base, "question": "Why real?", "workbenchSessionId": mine,
                                               "aboutStep": 1})
    event = repository.question_event(answer["eventId"])
    assert event["source_context"]["attempt_key"] == {"submission_id": "k1", "workbench_session_id": mine,
                                                      "about_step": 1}
    assert "about step 1" in tutor.contexts[-1].learner_answer_md
    with repository.connection() as connection:
        connection.execute("UPDATE workbench_sessions SET practice_item_id = 'pi_other' WHERE id = ?", (mine,))
        connection.commit()
    with pytest.raises(SidecarError, match="not this item's problem"):
        _call(ctx, "ask_tutor_question", {**base, "question": "Why?", "workbenchSessionId": mine})


def test_the_snapshot_carries_the_panel_and_the_rule(sidecar):
    _paths, ctx, _tutor = sidecar({("hints", "help_style"): "let_me_struggle"})
    vault, _ = ctx.require_vault()
    assert config_dto(vault)["ask"] == {"panelEnabled": True, "helpStyle": "let_me_struggle",
                                        "coldHelpConverts": True}


def test_the_reader_asks_in_the_help_styles_mode(tmp_path, monkeypatch):
    from tests.reader_tutor_fakes import LookupTutor, ask, reader_ctx

    tutor = LookupTutor()
    _paths, ctx, _repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor,
                                                  config={"hints": {"help_style": "let_me_struggle"}})
    assert ask(ctx)["answerMode"] == "ask_me_first"
    assert ask(ctx, "and again?", answerMode="answer_directly")["answerMode"] == "answer_directly"
    _p, off_ctx, _r, _s = reader_ctx(tmp_path, monkeypatch, LookupTutor(), config={"ask": {"panel_enabled": False}},
                                     name="off")
    assert ask(off_ctx)["answerMode"] == "answer_directly"


# -- K6: earlier on this question ----------------------------------------------------------------------


def _attempt(repository, attempt_id: str, created_at: str, *, hints: int = 0) -> None:
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "learner_answer_md, hints_used, created_at, session_id, rubric_score) "
            "VALUES (?, ?, 'lo_svd_definition', 'short_answer', 'independent_attempt', 'my answer', ?, ?, 'sess_1', 3)",
            (attempt_id, ITEM, hints, created_at))
        connection.commit()


def _question(repository, event_id: str, created_at: str, *, context: str = "practice",
              attempt_id: str | None = None) -> None:
    repository.insert_question_event({
        "id": event_id, "context": context, "practice_item_id": ITEM, "session_id": "sess_1",
        "attempt_id": attempt_id, "question_md": f"question {event_id}", "answer_md": "an answer",
        "question_type": "mechanism", "hint_equivalent": True, "answer_status": "answered", "created_at": created_at,
    })


def test_earlier_threads_list_each_attempts_help_newest_first(tmp_path):
    _paths, vault, repository = _vault(tmp_path)
    _question(repository, "q_a", "2026-05-01T10:00:00Z")
    _attempt(repository, "att_a", "2026-05-01T10:05:00Z", hints=1)
    _question(repository, "q_fb", "2026-05-01T10:06:00Z", context="feedback", attempt_id="att_a")
    _attempt(repository, "att_b", "2026-05-03T10:05:00Z")
    _attempt(repository, "att_c", "2026-05-05T10:05:00Z")
    _question(repository, "q_c", "2026-05-05T10:00:00Z")
    entries = earlier_threads(vault, repository, practice_item_id=ITEM)
    # att_b had no help to show; the feedback question belongs to att_a's entry.
    assert [entry["attempt_id"] for entry in entries] == ["att_c", "att_a"]
    assert [exchange["event_id"] for exchange in entries[1]["exchanges"]] == ["q_a", "q_fb"]
    assert entries[1]["outcome"]["label"] == "with help ◌"
    assert entries[0]["outcome"]["label"] == "on your own ●"


def test_the_transcript_offers_earlier_threads_but_never_on_a_cold_check(sidecar, monkeypatch):
    import learnloop_sidecar.handlers.tutor_qa as handler

    _paths, ctx, _tutor = sidecar()
    _vault_, repository = ctx.require_vault()
    _question(repository, "q_a", "2026-05-01T10:00:00Z")
    _attempt(repository, "att_a", "2026-05-01T10:05:00Z")
    params = {"context": "practice", "practiceItemId": ITEM, "sessionId": "sess_1", "submissionId": "fresh"}
    warm = _call(ctx, "get_tutor_transcript", params)
    assert [entry["attemptId"] for entry in warm["earlier"]] == ["att_a"]
    assert warm["earlierCountsAsHint"] is True and warm["cold"] is False
    monkeypatch.setattr(handler, "_served_cold", lambda vault, repository, item_id: True)
    cold = _call(ctx, "get_tutor_transcript", params)
    assert cold["earlier"] == [] and cold["cold"] is True
    # After Submit (the feedback context) earlier attempts are free, and the
    # attempt just graded is the feedback screen itself, not "earlier".
    _question(repository, "q_b", "2026-05-02T10:00:00Z")
    _attempt(repository, "att_b", "2026-05-02T10:05:00Z")
    feedback = _call(ctx, "get_tutor_transcript", {"context": "feedback", "attemptId": "att_b",
                                                   "sessionId": "sess_1"})
    assert [entry["attemptId"] for entry in feedback["earlier"]] == ["att_a"]
    assert feedback["earlierCountsAsHint"] is False


def test_nothing_earlier_enters_the_tutors_context(tmp_path):
    _paths, vault, repository = _vault(tmp_path)
    _question(repository, "q_old", "2026-05-01T10:00:00Z")
    _attempt(repository, "att_old", "2026-05-01T10:05:00Z")
    tutor = FakeTutor()
    ask_question(vault, repository, tutor, context="practice", question_md="Now?", practice_item_id=ITEM,
                 session_id="sess_1", submission_id="new", clock=FrozenClock(NOW))
    assert tutor.contexts[0].thread == []
    assert NOW_ISO  # the frozen clock's day is after the earlier attempt
