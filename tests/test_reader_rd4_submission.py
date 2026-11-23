"""Submitting a pad block (spec §10.9): an explicit act, the only way a pad's words become evidence, handed to the
existing attempt and teach-back entry points (no new grading path) and recorded in ``pad_block_submissions``.

The attempt path runs end to end through ``submit_attempt_on`` with manual grading (no model). The teach-back path's
entry point (``submit_teach_back_turn``) needs a naive-student provider, so it is replaced by a recorder that checks
what it was handed; the conversation guard reads a real session checkpoint.
"""

from __future__ import annotations

import json
from contextlib import closing
import sqlite3

import pytest

from learnloop.db.repositories import Repository
from learnloop.pads import submission
from learnloop.tutor.teach_back import TeachBackState, TeachBackTurn
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from tests.hint_fakes import ITEM, hint_vault
from tests.workbench_help_fakes import call

PAD = "pad_p"


@pytest.fixture(autouse=True)
def grader(monkeypatch):
    """A blind grader fake behind the sidecar's grading provider (the attempt entry point grades as for any
    answer)."""

    import learnloop_sidecar.handlers.practice as practice
    from tests.split_live_helpers import ReadyRuntime
    from tests.stuck_prompt_helpers import StuckFake

    client = StuckFake()
    monkeypatch.setattr(practice, "ready_grading_provider",
                        lambda vault, override=None: ("fake", ReadyRuntime(), client))
    return client


def _sidecar(tmp_path):
    paths = hint_vault(tmp_path)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.post_attempt_worker.autostart = False
    session = call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    return paths, ctx, session


def _problem_pad(ctx, *blocks: dict) -> str:
    view = call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen", "practiceItemId": ITEM,
                                        "stemMd": "Find P(X <= 1/2)."})["session"]
    call(ctx, "pad.apply", {"clientId": "c", "seq": 1, "padId": PAD, "ops": [
        {"op": "create_pad", "kind": "problem", "title": "the CDF", "workbenchSessionId": view["sessionId"]},
        *blocks]})
    return view["sessionId"]


def _block(block_id: str, body: str, *, version_id: str, kind: str = "text", provenance: str = "learner",
           position: str = "a0", payload: dict | None = None) -> dict:
    return {"op": "insert_block", "blockId": block_id, "versionId": version_id, "kind": kind,
            "provenance": provenance, "positionKey": position, "bodyMd": body, "payload": payload or {}}


def _submit(ctx, session, *, submission_id="sub_1", block_id="b1", version_id="v1", as_="attempt", item=ITEM):
    return call(ctx, "pad.submit_block", {"submissionId": submission_id, "blockId": block_id, "versionId": version_id,
                                          "as": as_, "target": {"sessionId": session, "practiceItemId": item}})


def _rows(paths, sql, params=()):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        return [tuple(row) for row in connection.execute(sql, params)]


def test_a_problem_pads_block_becomes_an_attempt_through_the_ordinary_submit(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    _problem_pad(ctx, _block("b1", "P(X <= 1/2) = F(1/2) = 1/4", version_id="v1"))
    reply = _submit(ctx, session)
    assert reply["version"] == 1 and reply["as"] == "attempt" and reply["duplicate"] is False
    attempt_id = reply["attemptId"]
    assert reply["entry"]["attemptId"] == attempt_id
    # The block version's words, frozen, recorded as any answer is, on the scratchpad's surface.
    assert _rows(paths, "SELECT learner_answer_md, practice_item_id, session_id, entry_surface FROM practice_attempts "
                        "WHERE id = ?", (attempt_id,)) == [("P(X <= 1/2) = F(1/2) = 1/4", ITEM, session,
                                                             submission.ENTRY_SURFACE)]
    assert _rows(paths, "SELECT submission_id, block_id, version_id, submitted_as, attempt_id, teach_back_id "
                        "FROM pad_block_submissions") == [("sub_1", "b1", "v1", "attempt", attempt_id, None)]
    # The tag on the block: this version, its current words.
    block = call(ctx, "pad.get", {"padId": PAD})["blocks"][0]
    assert [(tag["as"], tag["attemptId"], tag["current"]) for tag in block["submissions"]] == [
        ("attempt", attempt_id, True)]


def test_a_retry_hands_nothing_over_again_and_a_reused_id_is_refused(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    _problem_pad(ctx, _block("b1", "F(1/2) = 1/4", version_id="v1"))
    first = _submit(ctx, session)
    again = _submit(ctx, session)
    assert again["duplicate"] is True and again["attemptId"] == first["attemptId"] and again["entry"] is None
    assert len(_rows(paths, "SELECT id FROM practice_attempts")) == 1
    with pytest.raises(SidecarError) as refused:
        _submit(ctx, session, as_="teach_back")
    assert refused.value.code == "submission_reused"


def test_an_edit_after_submitting_keeps_the_submitted_version_and_its_tag_says_so(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    _problem_pad(ctx, _block("b1", "F(1/2) = 1/4", version_id="v1"))
    _submit(ctx, session)
    call(ctx, "pad.apply", {"clientId": "c", "seq": 2, "padId": PAD, "ops": [
        {"op": "edit_block", "blockId": "b1", "expectedHead": "v1", "bodyMd": "F(1/2) = 0.25", "versionId": "v2"}]})
    block = call(ctx, "pad.get", {"padId": PAD})["blocks"][0]
    assert block["headVersionId"] == "v2" and block["submissions"][0]["current"] is False
    # Submitting the old words now is a conflict naming the head, never a submission of words no longer there.
    with pytest.raises(SidecarError) as refused:
        _submit(ctx, session, submission_id="sub_2")
    assert refused.value.code == "stale_version" and refused.value.details["head_version_id"] == "v2"


@pytest.mark.parametrize(("blocks", "version_id", "code"), [
    # Quoted text: a whole sentence of one of the pad's quote blocks.
    ([_block("q1", "The distribution function at a point is the probability below it.", version_id="vq",
             kind="source_quote", provenance="source"),
      _block("b1", "the distribution function at a point is the probability below it", version_id="v1",
             position="a1")], "v1", "includes_quote"),
    # Someone else's words.
    ([_block("b1", "Look at F first.", version_id="v1", kind="tutor_quote", provenance="tutor")], "v1",
     "not_learners_words"),
    ([_block("b1", "   ", version_id="v1")], "v1", "empty_block"),
])
def test_what_is_refused(tmp_path, blocks, version_id, code):
    paths, ctx, session = _sidecar(tmp_path)
    _problem_pad(ctx, *blocks)
    with pytest.raises(SidecarError) as refused:
        _submit(ctx, session, version_id=version_id)
    assert refused.value.code == code
    if code == "includes_quote":
        assert refused.value.message == "this includes quoted text · submit only your own words"
    assert _rows(paths, "SELECT COUNT(*) FROM practice_attempts") == [(0,)]
    assert _rows(paths, "SELECT COUNT(*) FROM pad_block_submissions") == [(0,)]


def test_an_answer_only_from_its_problem_pad_or_check_cell(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    call(ctx, "pad.apply", {"clientId": "c", "seq": 1, "padId": "pad_r", "ops": [
        {"op": "create_pad", "kind": "running"}, _block("b1", "F(1/2) = 1/4", version_id="v1"),
        _block("k1", "1/4", version_id="vk", kind="check_cell", provenance="tutor", position="a1",
               payload={"practice_item_id": ITEM, "prompt_md": "What is P(X <= 1/2)?"})]})
    with pytest.raises(SidecarError) as refused:
        _submit(ctx, session)
    assert refused.value.code == "not_an_answer"
    reply = _submit(ctx, session, submission_id="sub_k", block_id="k1", version_id="vk")
    assert _rows(paths, "SELECT learner_answer_md FROM practice_attempts WHERE id = ?", (reply["attemptId"],)) == [
        ("1/4",)]


def test_a_teach_back_hands_the_block_to_the_teach_back_entry_and_opens_its_conversation(tmp_path, monkeypatch):
    paths, ctx, session = _sidecar(tmp_path)
    call(ctx, "pad.apply", {"clientId": "c", "seq": 1, "padId": "pad_r", "ops": [
        {"op": "create_pad", "kind": "running"},
        _block("b1", "The CDF at x is the chance of landing at or below x.", version_id="v1")]})
    handed = []

    def entry(ctx_, params):
        handed.append((params.session_id, params.practice_item_id, params.answer_md))
        return {"version": 1, "done": False, "questionMd": "Why at or below?", "state": {"conversationId": "conv_1"}}

    import learnloop_sidecar.handlers.teach_back as teach_back_handlers

    monkeypatch.setattr(teach_back_handlers, "submit_teach_back_turn", entry)
    reply = _submit(ctx, session, as_="teach_back", item="pi_teach")
    assert handed == [(session, "pi_teach", "The CDF at x is the chance of landing at or below x.")]
    assert (reply["teachBackId"], reply["attemptId"], reply["entry"]["questionMd"]) == ("conv_1", None,
                                                                                         "Why at or below?")
    assert _rows(paths, "SELECT submitted_as, teach_back_id, attempt_id FROM pad_block_submissions") == [
        ("teach_back", "conv_1", None)]


def test_a_teach_back_already_opened_by_this_submission_is_found_and_another_under_way_is_refused(tmp_path,
                                                                                                  monkeypatch):
    paths, ctx, session = _sidecar(tmp_path)
    words = "The CDF at x is the chance of landing at or below x."
    call(ctx, "pad.apply", {"clientId": "c", "seq": 1, "padId": "pad_r", "ops": [
        {"op": "create_pad", "kind": "running"}, _block("b1", words, version_id="v1")]})

    def entry(ctx_, params):
        raise AssertionError("handed over twice")

    import learnloop_sidecar.handlers.teach_back as teach_back_handlers

    monkeypatch.setattr(teach_back_handlers, "submit_teach_back_turn", entry)
    repository = Repository.attach(paths.sqlite_path)

    def checkpoint(opening: str) -> None:
        state = TeachBackState(practice_item_id="pi_teach", turns=[TeachBackTurn(role="learner", content_md=opening)],
                               conversation_id="conv_9")
        call(ctx, "update_session_checkpoint", {"sessionId": session, "currentPracticeItemId": "pi_teach",
                                              "currentAnswer": json.dumps({"mode": "teach_back",
                                                                           "state": state.to_dict()})})

    # The reply was lost after the conversation opened: the retry finds it and hands nothing over.
    checkpoint(words)
    assert _submit(ctx, session, as_="teach_back", item="pi_teach")["teachBackId"] == "conv_9"
    # Another conversation on the item is under way: the block would be taken as its next answer.
    checkpoint("something else entirely")
    with pytest.raises(SidecarError) as refused:
        _submit(ctx, session, submission_id="sub_2", as_="teach_back", item="pi_teach")
    assert refused.value.code == "teach_back_in_progress"
    assert repository.fetch_session_checkpoint(session) is not None
