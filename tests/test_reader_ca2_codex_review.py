"""Reader CA2, one Ask: the Codex review's findings (docs/reviews/reader-ca2-one-ask-codex-review.md), backend.

Every scenario is reproduced on real state (a real cold follow-up task, a real
workbench session, the real draft checkpoint, the hint service's own rows),
never a mocked predicate; every model is a fake.

* F1: *earlier on this question* opened before Submit costs one hint from the
  draft's checkpoint, server-side, across a restart and whichever surface
  submits the draft; once.
* F2 (K9): an Ask answer that would give the answer away is withheld and
  returns the ladder's take step; nothing counts or debits for it, and a
  restored thread never shows it.
* F3 (K7): the cold status is the server's; a cold item grounds in nothing,
  and a workbench question on it counts as the workbench's cold rule says.
* F4 (Q4): worked help taken first on a cold follow-up converts the attempt.
* F6, F10: an unfinished workbench is one attempt (one thread) in every host;
  a Reader question needs no practice session from the client and still
  counts at the submit.
* F7 (K8): the transcript's help record is what Submit folds.
* F8 (K5): no request bound on a subscription route.
* F9 (K11): citations carry their book excerpt, live and restored.
"""
from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.algorithm_versions import ONE_ASK_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.tutor.ai_contracts import TutorAnswer, TutorCitation
from learnloop.tutor.tutor_qa import (
    WITHHELD_ANSWER_MD,
    QuestionLimitReached,
    ask_question,
    hint_equivalents_for_submission,
)
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.ad23_fakes import cold_followup
from tests.helpers import NOW, create_basic_vault
from tests.structured_ai import StructuredClientFake
from tests.ux_phase1_support import set_config

ITEM = "pi_svd_define_001"
TAG = ONE_ASK_ALGORITHM_VERSION


class FakeTutor(StructuredClientFake):
    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-model"

    def __init__(self, question_type: str = "mechanism", answer_md: str = "Think about the shapes.",
                 cite_first: bool = False) -> None:
        self.question_type = question_type
        self.answer_md = answer_md
        self.cite_first = cite_first
        self.contexts: list = []

    def run_tutor_qa(self, context):
        self.contexts.append(context)
        citations = []
        if self.cite_first and context.source_spans:
            span = context.source_spans[0]
            citations = [TutorCitation(extraction_id=str(span["extraction_id"]), span_id=str(span["span_id"]))]
        return TutorAnswer(answer_md=self.answer_md, question_type=self.question_type,
                           facets=list(context.candidate_facets), citations=citations)


class PlanTutor(FakeTutor):
    """The ChatGPT plan's transport, as the spend module recognises it."""

    provider_type = "chatgpt_plan"


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _vault(tmp_path, updates: dict | None = None):
    paths = create_basic_vault(tmp_path / "vault")
    set_config(paths.root, {("algorithms", "algorithm_version"): TAG, **(updates or {})})
    return paths, load_vault(paths.root), Repository(paths.sqlite_path)


@pytest.fixture
def sidecar(tmp_path, monkeypatch):
    import learnloop_sidecar.handlers.tutor_qa as handler

    holder: dict = {"tutor": FakeTutor(question_type="clarification")}

    class Ready:
        ready = True

    monkeypatch.setattr(handler, "ready_tutor_qa_provider", lambda vault: ("fake", Ready(), holder["tutor"]))

    def build(updates: dict | None = None, tutor: FakeTutor | None = None, name: str = "vault"):
        if tutor is not None:
            holder["tutor"] = tutor
        paths, _vault_, _repository = _vault(tmp_path / name, updates)
        ctx = SidecarContext()
        ctx.load(paths.root)
        return paths, ctx, holder["tutor"]

    return build


def _workbench(repository, item_id: str = ITEM) -> str:
    from tests.test_reader_tutor_retrieval import _bound_session

    return _bound_session(repository, item_id)


# -- F3: the cold status and the cold rule are the server's, on every host ---------------------------


@pytest.mark.parametrize("converts", [True, False])
def test_a_workbench_question_on_a_cold_item_grounds_nothing_and_follows_the_workbench_rule(sidecar, converts):
    paths, ctx, tutor = sidecar({("ask", "cold_help_converts"): converts})
    _vault_, repository = ctx.require_vault()
    cold_followup(paths, ITEM)  # a real open cold retry holds the item
    wb = _workbench(repository)
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    answer = _call(ctx, "ask_tutor_question", {
        "context": "practice", "practiceItemId": ITEM, "sessionId": session, "workbenchSessionId": wb,
        "question": "What does this symbol mean?"})
    event = repository.question_event(answer["eventId"])
    # Nothing is grounded during a cold administration (reader.ask's policy).
    assert tutor.contexts[-1].source_spans == []
    assert (event["source_context"].get("source_retrieval") or {}).get("policy") == "cold_attempt"
    # The predecessor's workbench cold rule counts every question; the one
    # help rule (mvp-0.34) counts only a substantive one.
    assert bool(event["hint_equivalent"]) is (not converts)
    assert answer["hintEquivalent"] is (not converts)


def test_the_answer_box_on_a_cold_item_grounds_nothing_too_and_counts_as_practice_does(sidecar):
    paths, ctx, tutor = sidecar({("ask", "cold_help_converts"): False})
    _vault_, repository = ctx.require_vault()
    cold_followup(paths, ITEM)
    answer = _call(ctx, "ask_tutor_question", {
        "context": "practice", "practiceItemId": ITEM, "sessionId": "sess_1", "submissionId": "k1",
        "question": "What does this symbol mean?"})
    assert tutor.contexts[-1].source_spans == []
    event = repository.question_event(answer["eventId"])
    assert (event["source_context"].get("source_retrieval") or {}).get("policy") == "cold_attempt"
    # The answer box keeps practice's own rule (a clarification is free).
    assert repository.question_event(answer["eventId"])["hint_equivalent"] is False


def test_off_a_cold_item_the_answer_box_grounds_as_before(sidecar):
    _paths, ctx, tutor = sidecar()
    _call(ctx, "ask_tutor_question", {"context": "practice", "practiceItemId": ITEM, "sessionId": "sess_1",
                                      "submissionId": "k1", "question": "Why?"})
    assert tutor.contexts[-1].source_spans is not None
    _vault_, repository = ctx.require_vault()
    [event] = repository.question_events(context="practice", practice_item_id=ITEM)
    assert (event["source_context"].get("source_retrieval") or {}).get("policy") != "cold_attempt"


# -- F6, F10: one unfinished workbench, one attempt, in every host -----------------------------------


def test_a_workbench_thread_is_the_same_from_the_practice_steps_and_the_reader(sidecar):
    _paths, ctx, _tutor = sidecar()
    _vault_, repository = ctx.require_vault()
    wb = _workbench(repository)
    practice_session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    # Asked in practice's Work in Steps: the answer box's key and the workbench.
    _call(ctx, "ask_tutor_question", {"context": "practice", "practiceItemId": ITEM, "sessionId": practice_session,
                                      "submissionId": "answer-box-key", "workbenchSessionId": wb,
                                      "question": "Why is step 2 allowed?", "aboutStep": 2})
    # Resumed in the Reader: no key, no practice session from the client.
    reader = _call(ctx, "get_tutor_transcript", {"context": "practice", "practiceItemId": ITEM,
                                                  "workbenchSessionId": wb})
    assert [event["questionMd"] for event in reader["events"]] == ["Why is step 2 allowed?"]
    _call(ctx, "ask_tutor_question", {"context": "practice", "practiceItemId": ITEM, "workbenchSessionId": wb,
                                      "question": "And step 3?", "aboutStep": 3})
    back = _call(ctx, "get_tutor_transcript", {"context": "practice", "practiceItemId": ITEM,
                                                "sessionId": practice_session, "submissionId": "answer-box-key",
                                                "workbenchSessionId": wb})
    assert [event["questionMd"] for event in back["events"]] == ["Why is step 2 allowed?", "And step 3?"]
    steps = [event["sourceContext"]["attemptKey"].get("aboutStep") for event in back["events"]]
    assert steps == [2, 3]
    # The Reader's question carries the workbench submit's own key.
    reader_event = repository.question_event(back["events"][1]["id"])
    assert reader_event["source_context"]["attempt_key"]["submission_id"] == f"workbench:{wb}"
    # Another serving's answer box sees neither.
    other = _call(ctx, "get_tutor_transcript", {"context": "practice", "practiceItemId": ITEM,
                                                 "sessionId": practice_session, "submissionId": "another-key"})
    assert other["events"] == []


def test_a_reader_question_with_no_practice_session_still_counts_at_the_submit(sidecar):
    _paths, ctx, _tutor = sidecar(tutor=FakeTutor(question_type="mechanism"))
    _vault_, repository = ctx.require_vault()
    wb = _workbench(repository)
    assert repository.most_recent_open_session() is None
    answer = _call(ctx, "ask_tutor_question", {"context": "practice", "practiceItemId": ITEM,
                                               "workbenchSessionId": wb, "question": "Why is it orthogonal?"})
    event = repository.question_event(answer["eventId"])
    # The workbench submit's own session rule: a session is opened for it.
    opened = repository.most_recent_open_session()
    assert opened is not None and event["session_id"] == opened["id"]
    assert event["hint_equivalent"] is True
    assert hint_equivalents_for_submission(repository, ITEM, opened["id"]) == 1


def test_a_workbench_of_another_item_is_refused(sidecar):
    from learnloop_sidecar.errors import SidecarError

    _paths, ctx, _tutor = sidecar()
    _vault_, repository = ctx.require_vault()
    wb = _workbench(repository)
    with repository.connection() as connection:
        connection.execute("UPDATE workbench_sessions SET practice_item_id = 'pi_other' WHERE id = ?", (wb,))
        connection.commit()
    with pytest.raises(SidecarError, match="not this item's problem"):
        _call(ctx, "get_tutor_transcript", {"context": "practice", "practiceItemId": ITEM, "workbenchSessionId": wb})


# -- F2 (K9): worked help is never served on the spot --------------------------------------------------


def _expected(vault) -> str:
    expected = vault.practice_items[ITEM].expected_answer
    return expected if isinstance(expected, str) else str(expected)


def test_an_answer_that_gives_the_answer_away_is_withheld_with_the_take_step(sidecar):
    _paths, ctx, tutor = sidecar(tutor=FakeTutor(question_type="strategy"))
    vault, repository = ctx.require_vault()
    tutor.answer_md = _expected(vault)
    answer = _call(ctx, "ask_tutor_question", {"context": "practice", "practiceItemId": ITEM, "sessionId": "sess_1",
                                               "submissionId": "k1", "question": "Just show me the final answer"})
    assert answer["answerMd"] == WITHHELD_ANSWER_MD
    assert answer["takeOffer"] == {"levels": [4, 5], "reason": "worked_help"}
    assert answer["hintEquivalent"] is False and answer["leakSuspected"] is False and answer["citations"] == []
    event = repository.question_event(answer["eventId"])
    assert event["source_context"]["withheld"]["reason"] == "worked_help"
    assert event["hint_equivalent"] is False
    with closing(sqlite3.connect(_paths.sqlite_path)) as connection:
        amounts = [row[0] for row in connection.execute(
            "SELECT amount FROM reveal_events WHERE question_event_id = ?", (answer["eventId"],))]
    assert all(amount == 0 for amount in amounts)
    # Restored after a remount, the thread shows the take step, never the text.
    transcript = _call(ctx, "get_tutor_transcript", {"context": "practice", "practiceItemId": ITEM,
                                                     "sessionId": "sess_1", "submissionId": "k1"})
    assert [event["answerMd"] for event in transcript["events"]] == [WITHHELD_ANSWER_MD]
    # Nothing was delivered, so Submit folds nothing for it.
    assert hint_equivalents_for_submission(repository, ITEM, "sess_1") == 0


def test_panel_off_the_answer_is_delivered_as_before(tmp_path):
    _paths, vault, repository = _vault(tmp_path, {("ask", "panel_enabled"): False})
    tutor = FakeTutor(question_type="strategy", answer_md=_expected(vault))
    result = ask_question(vault, repository, tutor, context="practice", question_md="Just show me",
                          practice_item_id=ITEM, session_id="sess_1", clock=FrozenClock(NOW))
    assert result["answer_md"] == _expected(vault) and "take_offer" not in result


def test_an_ordinary_answer_is_delivered(sidecar):
    _paths, ctx, _tutor = sidecar(tutor=FakeTutor(question_type="mechanism"))
    answer = _call(ctx, "ask_tutor_question", {"context": "practice", "practiceItemId": ITEM, "sessionId": "sess_1",
                                               "submissionId": "k1", "question": "Why orthogonal?"})
    assert answer["answerMd"] == "Think about the shapes." and "takeOffer" not in answer
    assert answer["hintEquivalent"] is True


# -- F8 (K5): no request bound on a subscription route --------------------------------------------------


def test_a_subscription_route_has_no_request_bound_and_a_metered_route_keeps_it(tmp_path):
    _paths, vault, repository = _vault(tmp_path, {("tutor_qa", "max_questions_practice"): 2})
    clock = FrozenClock(NOW)
    for index in range(4):
        result = ask_question(vault, repository, PlanTutor(), context="practice", question_md=f"Why {index}?",
                              practice_item_id=ITEM, session_id="sess_1", submission_id="k1", clock=clock)
        assert result["remaining"] is None
    with pytest.raises(QuestionLimitReached):
        ask_question(vault, repository, FakeTutor(), context="practice", question_md="Metered?",
                     practice_item_id=ITEM, session_id="sess_1", submission_id="k1", clock=clock)


# -- F7 (K8): the help record is what Submit folds ------------------------------------------------------


def test_the_help_record_lists_what_submit_folds_including_an_earlier_serves_question(sidecar):
    _paths, ctx, _tutor = sidecar(tutor=FakeTutor(question_type="mechanism"))
    _vault_, repository = ctx.require_vault()
    _call(ctx, "ask_tutor_question", {"context": "practice", "practiceItemId": ITEM, "sessionId": "sess_1",
                                      "submissionId": "serve-1", "question": "Why orthogonal?"})
    # The item skipped and served again: a fresh thread, but the window's
    # question still folds into the next attempt, and the record says so.
    fresh = _call(ctx, "get_tutor_transcript", {"context": "practice", "practiceItemId": ITEM,
                                                "sessionId": "sess_1", "submissionId": "serve-2"})
    assert fresh["events"] == []
    record = fresh["helpRecord"]
    assert [(item["kind"], item["counts"], item["thisAttempt"]) for item in record["items"]] == [
        ("question", True, False)]
    assert record["counted"] == hint_equivalents_for_submission(repository, ITEM, "sess_1") == 1
    # The same record after a remount: it is stored state, never the panel's.
    again = _call(ctx, "get_tutor_transcript", {"context": "practice", "practiceItemId": ITEM,
                                                "sessionId": "sess_1", "submissionId": "serve-2"})
    assert again["helpRecord"] == record


def test_a_free_clarification_is_listed_for_its_own_attempt_only(sidecar):
    _paths, ctx, _tutor = sidecar(tutor=FakeTutor(question_type="clarification"))
    _call(ctx, "ask_tutor_question", {"context": "practice", "practiceItemId": ITEM, "sessionId": "sess_1",
                                      "submissionId": "k1", "question": "What does V mean?"})
    mine = _call(ctx, "get_tutor_transcript", {"context": "practice", "practiceItemId": ITEM,
                                               "sessionId": "sess_1", "submissionId": "k1"})["helpRecord"]
    assert [(item["kind"], item["counts"]) for item in mine["items"]] == [("question", False)]
    assert mine["counted"] == 0
    other = _call(ctx, "get_tutor_transcript", {"context": "practice", "practiceItemId": ITEM,
                                                "sessionId": "sess_1", "submissionId": "k2"})["helpRecord"]
    assert other["items"] == []


# -- F9 (K11): citations carry their excerpt, live and restored ----------------------------------------


def test_a_cited_passage_carries_its_excerpt_as_provided_and_stores_it(tmp_path):
    from tests.test_tutor_citations import _CLOCK, _ITEM_ID, _CitingTutorClient, _mapped_vault

    vault, repository = _mapped_vault(tmp_path)
    assert vault.config.ask.panel_enabled
    client = _CitingTutorClient([TutorCitation(extraction_id="ext_text", span_id="s1")])
    result = ask_question(vault, repository, client, context="practice", question_md="Why symmetric?",
                          practice_item_id=_ITEM_ID, session_id="s1", submission_id="k1", clock=_CLOCK)
    provided = next(span for span in client.contexts[0].source_spans
                    if (span["extraction_id"], span["span_id"]) == ("ext_text", "s1"))
    [citation] = result["citations"]
    assert citation["excerpt"] and str(provided["text"]).startswith(citation["excerpt"].rstrip("…"))
    [event] = repository.question_events(context="practice", practice_item_id=_ITEM_ID)
    assert event["source_context"]["citations"][0]["excerpt"] == citation["excerpt"]


# -- F1 (K6, Q2): the earlier attempt's cost is the server's, from the draft ---------------------------


def _hint_sidecar(tmp_path, updates: dict | None = None):
    from tests.hint_fakes import hint_vault, store_map

    paths = hint_vault(tmp_path, config='[hints]\nchoice_policy = "argmax"\n')
    store_map(paths)
    set_config(paths.root, {("algorithms", "algorithm_version"): TAG, **(updates or {})})
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    ctx.hints_inline = True
    ctx.hint_seed = "e"
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    return paths, ctx, session


def _submit(ctx, session, *, key: str, hints: int = 0):
    from tests.hint_fakes import ITEM as HINT_ITEM, WORK

    return _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": HINT_ITEM, "answerMd": WORK, "attemptType": "independent_attempt",
        "hintsUsed": hints, "selfGrade": {"criterionPoints": {"cdf": 2, "value": 0}, "confidence": 3},
        "submissionId": key})


def _attempt_row(paths, attempt_id: str) -> dict:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return dict(connection.execute("SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone())


def _save_draft(ctx, session, *, key: str, **extra):
    from tests.hint_fakes import ITEM as HINT_ITEM, WORK

    _call(ctx, "save_practice_draft", {"sessionId": session, "practiceItemId": HINT_ITEM, "answerMd": WORK,
                                       "hintsUsed": 0, "submissionId": key, **extra})


def test_an_earlier_attempt_opened_before_submit_costs_one_hint_across_a_restart(tmp_path):
    paths, ctx, session = _hint_sidecar(tmp_path)
    _save_draft(ctx, session, key="k1", earlierOpened=True)
    # The app restarts: the checkpoint names it, and the client sends no count.
    restarted = SidecarContext()
    restarted.load(paths.root)
    restarted.grading_provider_override = "manual"
    checkpoint = _call(restarted, "get_session", {"sessionId": session})["checkpoint"]
    assert checkpoint["earlierOpened"] is True
    # A later save without the flag keeps it (only a new draft drops it).
    _save_draft(restarted, session, key="k1")
    attempt = _attempt_row(paths, _submit(restarted, session, key="k1", hints=0)["attemptId"])
    assert attempt["hints_used"] == 1


def test_the_draft_moved_into_steps_is_counted_once_by_its_submit_whatever_its_key(tmp_path):
    paths, ctx, session = _hint_sidecar(tmp_path)
    _save_draft(ctx, session, key="k1", earlierOpened=True)
    # The steps submit carries the workbench's own key; the draft's opening counts.
    attempt = _attempt_row(paths, _submit(ctx, session, key="workbench:wb_x", hints=0)["attemptId"])
    assert attempt["hints_used"] == 1


def test_a_new_draft_never_inherits_an_earlier_opening(tmp_path):
    paths, ctx, session = _hint_sidecar(tmp_path)
    _save_draft(ctx, session, key="k1", earlierOpened=True)
    _save_draft(ctx, session, key="k2")
    attempt = _attempt_row(paths, _submit(ctx, session, key="k2", hints=0)["attemptId"])
    assert attempt["hints_used"] == 0


# -- F4 (Q4): worked help taken first on a cold follow-up converts the attempt -----------------------


@pytest.mark.parametrize("level, option", [(4, "worked_chunk@L4"), (5, "walkthrough@L5")])
@pytest.mark.parametrize("converts", [True, False])
def test_worked_help_taken_first_on_a_cold_follow_up_is_practice_with_help(tmp_path, level, option, converts):
    from learnloop_sidecar.errors import SidecarError
    from tests.hint_fakes import ITEM as HINT_ITEM, WORK, ChooserFake, WriterFake, prefer

    paths, ctx, session = _hint_sidecar(tmp_path, {("ask", "cold_help_converts"): converts})
    task_id = cold_followup(paths, HINT_ITEM)
    ctx.hint_writer_client = WriterFake()
    ctx.hint_chooser_client = ChooserFake(prefer(option, 0.9))
    job = _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": HINT_ITEM,
                                              "submissionId": "k1", "answerMd": WORK, "takenLevel": level})
    assert job["result"]["level"] == level and job["result"]["evidence"]["primed"] is True
    if not converts:
        with pytest.raises(SidecarError):
            _submit(ctx, session, key="k1", hints=0)
        return
    attempt = _attempt_row(paths, _submit(ctx, session, key="k1", hints=0)["attemptId"])
    assert (attempt["hints_used"], attempt["primed"]) == (0, 1)
    repository = Repository(paths.sqlite_path)
    # Never the cold measurement: the task is not consumed by this attempt.
    assert repository.followup_task(task_id)["status"] != "consumed"
