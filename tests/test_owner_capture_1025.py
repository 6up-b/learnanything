"""The owner's 2026-10-25 capture (docs/reviews/owner-capture-2026-10-25-fixes.md), sidecar side.

B4: the practice screen's draft is bound to the queue's offer; the learner
goes into "Work in steps" and submits there (the offer is answered by that
attempt); the answer box's draft, its retry key and its hints stayed in the
session checkpoint, so the item opened again restored them, and its submit
failed with "The scheduler offer does not belong to this item/session or
was already consumed." B3: the Ask thread of an item is the current
attempt's, never a previous serving's. B2: the help style changes the next
hint the fallback serves. Fakes only.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.hint_fakes import ITEM, WORK, WriterFake, hint_vault
from tests.split_live_helpers import ReadyRuntime
from tests.test_stuck_prompt import StuckFake

STALE = "The scheduler offer does not belong to this item/session or was already consumed."


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _rows(paths, sql, params=()):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(sql, params)]


@pytest.fixture
def grader(monkeypatch):
    import learnloop.attempts.attempts as attempts_module
    import learnloop_sidecar.handlers.practice as practice

    monkeypatch.setattr(attempts_module, "AUTO_PRIME_REVEAL_THRESHOLD", 10.0)
    client = StuckFake()
    monkeypatch.setattr(practice, "ready_grading_provider",
                        lambda vault, override=None: ("fake", ReadyRuntime(), client))
    return client


def _sidecar(tmp_path, config: str = ""):
    paths = hint_vault(tmp_path, config=config)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.hints_inline = True
    ctx.hint_seed = "e"
    ctx.hint_writer_client = WriterFake()
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    return paths, ctx, session


def _offer(ctx, session):
    snapshot = _call(ctx, "get_today_queue", {"sessionId": session})
    return next(item["schedulerCandidateId"] for section in snapshot["sections"] for item in section["items"]
                if item["practiceItemId"] == ITEM)


def _steps_submit(ctx, session, offer):
    """The practice screen's "Work in steps", one step, Submit (the
    workbench names the screen's serve, as Workbench.tsx does)."""

    view = _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen", "practiceItemId": ITEM,
                                         "stemMd": "Find P.", "schedulerCandidateId": offer,
                                         "planPresentationId": None})["session"]
    _call(ctx, "workbench.save_step", {"sessionId": view["sessionId"], "clientIdempotencyKey": "s1", "op": "add",
                                       "bodyMd": WORK})
    return _call(ctx, "workbench.submit", {"sessionId": view["sessionId"], "practiceSessionId": session,
                                           "schedulerCandidateId": offer, "planPresentationId": None})["attempt"]


def _draft(ctx, session, key, offer, *, hints=0, answer="F(x) = x^2"):
    _call(ctx, "save_practice_draft", {"sessionId": session, "practiceItemId": ITEM, "answerMd": answer,
                                       "hintsUsed": hints, "submissionId": key, "schedulerCandidateId": offer})


# -- B4 -------------------------------------------------------------------------------------------


def test_b4_a_steps_submit_closes_the_answer_boxs_draft(tmp_path, grader):
    """Root cause: the steps submit answered the item, but the answer box's
    checkpoint (its retry key, hints and offer binding) stayed, so the item
    opened again restored it as if it were the same attempt."""

    paths, ctx, session = _sidecar(tmp_path)
    offer = _offer(ctx, session)
    _draft(ctx, session, "box-key", offer, hints=1)
    _steps_submit(ctx, session, offer)
    _vault, repository = ctx.require_vault()
    checkpoint = repository.fetch_session_checkpoint(session)
    assert (checkpoint or {}).get("current_practice_item_id") != ITEM


def test_b4_a_submit_under_a_key_whose_offer_another_attempt_answered_still_grades(tmp_path, grader):
    """Fail soft: the retry key's offer was answered by the steps attempt,
    so this submit answers no open offer. It is graded, unattributed (never
    linked to the consumed offer), and the offer keeps its one attempt."""

    paths, ctx, session = _sidecar(tmp_path)
    offer = _offer(ctx, session)
    _draft(ctx, session, "box-key", offer)
    steps = _steps_submit(ctx, session, offer)
    result = _call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": "P = 1/4",
                                           "hintsUsed": 0, "attemptType": "independent_attempt", "submissionId": "box-key"})
    assert result["attemptId"] and result["attemptId"] != steps["attemptId"]
    [row] = _rows(paths, "SELECT scheduler_candidate_id FROM practice_attempts WHERE id = ?", (result["attemptId"],))
    assert row["scheduler_candidate_id"] is None
    [candidate] = _rows(paths, "SELECT chosen_attempt_id FROM scheduler_slate_candidates WHERE id = ?", (offer,))
    assert candidate["chosen_attempt_id"] == steps["attemptId"]
    # The retry is the same attempt (the key's receipt answers it).
    again = _call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": "P = 1/4",
                                          "hintsUsed": 0, "attemptType": "independent_attempt", "submissionId": "box-key"})
    assert again["attemptId"] == result["attemptId"]


def test_b4_a_submit_naming_an_answered_offer_still_grades(tmp_path, grader):
    """Fail soft: a new attempt naming an offer an earlier attempt answered
    (a stale offer the screen still held) is graded, unattributed."""

    paths, ctx, session = _sidecar(tmp_path)
    offer = _offer(ctx, session)
    first = _call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": "P = 1/2",
                                          "hintsUsed": 0, "attemptType": "independent_attempt", "submissionId": "first", "schedulerCandidateId": offer})
    _draft(ctx, session, "second", offer)
    second = _call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": "P = 1/4",
                                           "hintsUsed": 0, "attemptType": "independent_attempt", "submissionId": "second", "schedulerCandidateId": offer})
    assert second["attemptId"] != first["attemptId"]
    [row] = _rows(paths, "SELECT scheduler_candidate_id FROM practice_attempts WHERE id = ?", (second["attemptId"],))
    assert row["scheduler_candidate_id"] is None


# -- B3: a reattempt starts a fresh Ask thread -----------------------------------------------------


def _question(ctx, session, event_id, *, hint=True):
    _vault, repository = ctx.require_vault()
    from learnloop.clock import utc_now_iso

    repository.insert_question_event({
        "id": event_id, "context": "practice", "practice_item_id": ITEM, "session_id": session,
        "question_md": f"question {event_id}", "answer_md": "an answer", "answer_status": "answered",
        "hint_equivalent": 1 if hint else 0, "created_at": utc_now_iso(),
    })


def test_b3_a_reattempt_starts_a_fresh_ask_thread(tmp_path, grader):
    import time

    from learnloop.tutor.tutor_qa import hint_equivalents_for_submission, question_usage

    paths, ctx, session = _sidecar(tmp_path)
    _question(ctx, session, "q_first")
    transcript = {"context": "practice", "practiceItemId": ITEM, "sessionId": session}
    assert [event["id"] for event in _call(ctx, "get_tutor_transcript", transcript)["events"]] == ["q_first"]
    time.sleep(1.1)  # timestamps have one-second resolution
    _call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": "P = 1/2",
                                  "hintsUsed": 0, "attemptType": "independent_attempt", "submissionId": "first"})
    time.sleep(1.1)
    # The item served again: the thread, the turns the tutor is given and
    # the budget are this attempt's.
    fresh = _call(ctx, "get_tutor_transcript", transcript)
    vault, repository = ctx.require_vault()
    assert fresh["events"] == []
    # Reader CA2 (K5) supersedes B3's per-attempt budget while the Ask panel
    # is on: the budget is a money bound per item per UTC day, which a new
    # serve never resets (the thread still starts fresh). The panel off keeps
    # B3's rule (tests/test_reader_ca2_one_ask.py pins both).
    assert fresh["remaining"] == vault.config.tutor_qa.max_questions_practice - 1
    used, _limit = question_usage(vault, repository, context="practice", practice_item_id=ITEM, session_id=session)
    assert used == 1
    _question(ctx, session, "q_second")
    assert [event["id"] for event in _call(ctx, "get_tutor_transcript", transcript)["events"]] == ["q_second"]
    # Evidence is unchanged: the earlier question was counted on the first
    # attempt, never on this one.
    assert hint_equivalents_for_submission(repository, ITEM, session) == 1
    # The earlier turn stays on record.
    assert {row["id"] for row in _rows(paths, "SELECT id FROM question_events")} == {"q_first", "q_second"}


# -- B2: the help style moves the next hint without a Decider ------------------------------------


def _press(ctx, session, key):
    return _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": key,
                                                "answerMd": WORK})["result"]


@pytest.mark.parametrize("style, first", [
    ("balanced", ("authored", 3)),
    ("let_me_struggle", ("approach_question", 1)),
    ("guide_me", ("next_step", 3)),
])
def test_b2_the_help_style_changes_the_first_hint_the_fallback_serves(tmp_path, style, first):
    """The owner's vault routes no Decider, so every press took the
    fallback, whose order (the item's own hints first) never read the style."""

    paths, ctx, session = _sidecar(tmp_path, "[hints]\nchooser_enabled = false\n")
    assert _call(ctx, "practice.set_help_style", {"helpStyle": style})["helpStyle"] == style
    hint = _press(ctx, session, f"key-{style}")
    assert hint["status"] == "ready"
    assert (hint["kind"], hint["level"]) == first
    [row] = _rows(paths, "SELECT contract_failures_json FROM help_assists")
    import json

    assert json.loads(row["contract_failures_json"])["state_at_request"]["help_style"] == style


def test_b2_let_me_struggle_still_goes_up(tmp_path):
    _paths, ctx, session = _sidecar(tmp_path, "[hints]\nchooser_enabled = false\n")
    _call(ctx, "practice.set_help_style", {"helpStyle": "let_me_struggle"})
    served = [(hint["kind"], hint["level"]) for hint in (_press(ctx, session, "k") for _ in range(3))]
    assert served == [("approach_question", 1), ("localize", 2), ("authored", 3)]


def test_b2_the_workbench_fallback_suggestion_reads_the_style():
    from learnloop.hints.workbench import styled_level

    assert [styled_level(level, "balanced") for level in (1, 2, 3, 4, 5)] == [1, 2, 3, 4, 5]
    assert [styled_level(level, "let_me_struggle") for level in (1, 2, 3, 4, 5)] == [1, 2, 3, 3, 3]
    assert [styled_level(level, "guide_me") for level in (1, 2, 3, 4, 5)] == [3, 3, 3, 4, 5]


def test_b2_a_suggestion_judged_under_another_style_is_not_reused(tmp_path):
    """The ladder's suggestion is a Decider draw under the style of that
    moment; taking its rung after the style changed draws again."""

    import json

    from tests.hint_fakes import ChooserFake, prefer
    from tests.workbench_help_fakes import call, help_rows, open_problem, run_job, sidecar

    chooser = ChooserFake(prefer("error_specific@L3", 0.8))
    paths, wctx, _session = sidecar(tmp_path, chooser=chooser)
    wb, _chains = open_problem(wctx)
    suggestion = run_job(wctx, call(wctx, "workbench.suggest_help", {"sessionId": wb}))["suggestion"]
    assert len(chooser.calls) == 1 and chooser.calls[0]["state"]["help_style"] == "balanced"
    call(wctx, "workbench.set_help_style", {"sessionId": wb, "helpStyle": "guide_me"})
    run_job(wctx, call(wctx, "workbench.request_help", {"sessionId": wb, "takenLevel": suggestion["level"],
                                                        "offeredLevel": suggestion["level"],
                                                        "suggestionId": suggestion["suggestionId"]}))
    assert len(chooser.calls) == 2 and chooser.calls[1]["state"]["help_style"] == "guide_me"
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "hint"]
    assert json.loads(row["contract_failures_json"])["state_at_request"]["help_style"] == "guide_me"


# -- Fix round 2 (Codex verify 20261025-145037-Wyei9F) ------------------------------------------


def test_fix2_a_key_from_another_session_is_refused_not_succeeded(tmp_path, grader):
    """Item 1: the answer box's key belongs to session A and a steps attempt
    there answered its offer. Submitted for the same item in session B with
    no offer, it is refused as another session's key, as before B4: the
    successor key is only ever derived inside the key's own session."""

    from learnloop_sidecar.errors import SidecarError

    paths, ctx, session_a = _sidecar(tmp_path)
    offer = _offer(ctx, session_a)
    _draft(ctx, session_a, "box-key", offer)
    _steps_submit(ctx, session_a, offer)
    _call(ctx, "end_session", {"sessionId": session_a})
    session_b = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    assert session_b != session_a
    before = _rows(paths, "SELECT id FROM practice_attempts")
    with pytest.raises(SidecarError) as raised:
        _call(ctx, "submit_attempt", {"sessionId": session_b, "practiceItemId": ITEM, "answerMd": "P = 1/4",
                                      "hintsUsed": 0, "attemptType": "independent_attempt",
                                      "submissionId": "box-key"})
    assert raised.value.code == "validation_error"
    assert "different item or session" in str(raised.value)
    assert _rows(paths, "SELECT id FROM practice_attempts") == before
    assert _rows(paths, "SELECT submission_id FROM submission_intents WHERE submission_id LIKE 'box-key~%'") == []
    # recover_practice_submission resolves no successor in session B either.
    recovered = _call(ctx, "recover_practice_submission", {"sessionId": session_b, "practiceItemId": ITEM,
                                                           "submissionId": "box-key"})
    assert recovered["status"] == "pending"


def _reveal(ctx, session, key, index):
    result = _call(ctx, "practice.record_hint_reveal", {"sessionId": session, "practiceItemId": ITEM,
                                                        "submissionId": key, "authoredIndex": index,
                                                        "answerMd": "F(x)"})
    assert result["recorded"], result


def _hints_of(paths, attempt_id):
    [row] = _rows(paths, "SELECT hints_used, attempt_type FROM practice_attempts WHERE id = ?", (attempt_id,))
    return row["hints_used"]


def test_fix2_an_already_stale_checkpoints_hint_is_not_counted_again(tmp_path, grader):
    """Item 2: a checkpoint the owner's bug already left behind restores
    ``hintsUsed: 1`` under the answer box's key; that hint was shown before
    the steps attempt, which counted it. The successor attempt, with no new
    help, records no hint: the client's count is not its base, only the
    item's help since its last attempt is."""

    paths, ctx, session = _sidecar(tmp_path)
    offer = _offer(ctx, session)
    _draft(ctx, session, "box-key", offer, hints=1)
    _reveal(ctx, session, "box-key", 0)
    _steps_submit(ctx, session, offer)
    result = _call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": "P = 1/4",
                                           "hintsUsed": 1, "authoredHints": 1, "firstHintProgress": "no_draft",
                                           "attemptType": "independent_attempt", "submissionId": "box-key"})
    assert _hints_of(paths, result["attemptId"]) == 0


def test_fix2_a_hint_revealed_after_the_earlier_attempt_still_counts(tmp_path, grader):
    """Item 2's guard: an authored hint revealed on the restored draft after
    the steps attempt is inside the item's window and counts once; the
    stale one does not."""

    import time

    paths, ctx, session = _sidecar(tmp_path)
    offer = _offer(ctx, session)
    _draft(ctx, session, "box-key", offer, hints=1)
    _reveal(ctx, session, "box-key", 0)
    _steps_submit(ctx, session, offer)
    time.sleep(1.1)  # practice_attempts.created_at has one-second resolution
    _reveal(ctx, session, "box-key", 1)
    result = _call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": "P = 1/4",
                                           "hintsUsed": 2, "authoredHints": 2,
                                           "attemptType": "independent_attempt", "submissionId": "box-key"})
    assert _hints_of(paths, result["attemptId"]) == 1


def test_fix2_a_stale_offers_carried_hint_is_not_counted_again(tmp_path, grader):
    """Item 2, the fail-soft path: a screen still holding an answered offer
    (and the hint count it carried into the earlier attempt) under a new key;
    the earlier attempt counted that hint, so this one records none."""

    paths, ctx, session = _sidecar(tmp_path)
    offer = _offer(ctx, session)
    _draft(ctx, session, "first", offer, hints=1)
    _reveal(ctx, session, "first", 0)
    first = _call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": "P = 1/2",
                                          "hintsUsed": 1, "authoredHints": 1, "attemptType": "independent_attempt",
                                          "submissionId": "first", "schedulerCandidateId": offer})
    assert _hints_of(paths, first["attemptId"]) == 1
    second = _call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": "P = 1/4",
                                           "hintsUsed": 1, "authoredHints": 1, "attemptType": "independent_attempt",
                                           "submissionId": "second", "schedulerCandidateId": offer})
    assert _hints_of(paths, second["attemptId"]) == 0


def test_fix2_a_changed_fallback_names_its_new_policy_version(tmp_path):
    """Item 3: the style-aware fallback changes decisions, so its receipts
    name a new hint-choice policy version; the Decider's stays v1."""

    from learnloop.hints import chooser

    _paths, ctx, session = _sidecar(tmp_path, "[hints]\nchooser_enabled = false\n")
    _press(ctx, session, "key")
    [row] = _rows(_paths, "SELECT policy_version, chooser FROM help_assists WHERE counted_by = 'server'")
    assert row["chooser"] == "fallback"
    assert row["policy_version"] == "hint-choice-policy-v2:fallback"
    assert chooser.policy_version("sample") == "hint-choice-policy-v1:sample"
