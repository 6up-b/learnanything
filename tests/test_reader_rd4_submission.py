"""Submitting a pad block (spec §10.9): an explicit act, the only way a pad's words become evidence, handed to the
existing attempt and teach-back entry points (no new grading path) and recorded in ``pad_block_submissions``.

The attempt path runs end to end through ``submit_attempt_on`` with a grader fake. The teach-back path's entry point
(``submit_teach_back_turn_on``) needs a naive-student provider, so it is replaced by a recorder that checks what it
was handed and leaves what the real one leaves (a checkpointed state, or an attempt whose evidence carries the
conversation's id); the conversation guard reads the real session checkpoint and attempts.
"""

from __future__ import annotations

import json
from contextlib import closing
import sqlite3

import pytest

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


class _TeachBackEntry:
    """The teach-back entry point as a recorder: it opens the conversation it is asked to (the session's checkpoint
    holds its state, as the real one leaves it), or grades it at once (an attempt whose evidence carries the
    conversation's id), and may crash after either, before the pad's reply is written."""

    def __init__(self, paths, *, done: bool = False, crash: bool = False) -> None:
        self.paths, self.done, self.crash = paths, done, crash
        self.calls: list[tuple[str, str, str, str | None]] = []

    def __call__(self, ctx, params, *, conversation_id=None):
        self.calls.append((params.session_id, params.practice_item_id, params.answer_md, conversation_id))
        if self.done:
            with closing(sqlite3.connect(self.paths.sqlite_path)) as connection:
                connection.execute(
                    "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, "
                    "attempt_type, created_at) VALUES (?, ?, 'lo', 'teach_back', 'teach_back', "
                    "'2026-11-23T10:00:00Z')", (f"att_{conversation_id}", params.practice_item_id))
                connection.execute(
                    "INSERT INTO grading_evidence(id, attempt_id, criterion_id, points_awarded, agent_run_id, "
                    "grader_tier, created_at) VALUES (?, ?, 'c1', 1, ?, 1, '2026-11-23T10:00:00Z')",
                    (f"ge_{conversation_id}", f"att_{conversation_id}", conversation_id))
                connection.commit()
            reply = {"version": 1, "done": True, "attemptId": f"att_{conversation_id}", "agentRunId": conversation_id}
        else:
            state = TeachBackState(practice_item_id=params.practice_item_id,
                                   turns=[TeachBackTurn(role="learner", content_md=params.answer_md)],
                                   conversation_id=conversation_id)
            call(ctx, "update_session_checkpoint", {
                "sessionId": params.session_id, "currentPracticeItemId": params.practice_item_id,
                "currentAnswer": json.dumps({"mode": "teach_back", "state": state.to_dict()})})
            reply = {"version": 1, "done": False, "questionMd": "Why at or below?",
                     "state": {"conversationId": conversation_id}}
        if self.crash:
            raise RuntimeError("the process died before the pad's reply was written")
        return reply


WORDS = "The CDF at x is the chance of landing at or below x."


def _patch_entry(monkeypatch, entry):
    import learnloop_sidecar.handlers.teach_back as teach_back_handlers

    monkeypatch.setattr(teach_back_handlers, "submit_teach_back_turn_on", entry, raising=False)
    # The RPC face too, for the code before conversation ids were reserved (the fail-first runs).
    monkeypatch.setattr(teach_back_handlers, "submit_teach_back_turn", lambda ctx, params: entry(ctx, params))


def _teach_back_pad(ctx, monkeypatch, entry, *blocks):
    _patch_entry(monkeypatch, entry)
    call(ctx, "pad.apply", {"clientId": "c", "seq": 1, "padId": "pad_r", "ops": [
        {"op": "create_pad", "kind": "running"}, *(blocks or [_block("b1", WORDS, version_id="v1")])]})


def test_a_teach_back_hands_the_block_to_the_teach_back_entry_and_opens_its_conversation(tmp_path, monkeypatch):
    paths, ctx, session = _sidecar(tmp_path)
    entry = _TeachBackEntry(paths)
    _teach_back_pad(ctx, monkeypatch, entry)
    reply = _submit(ctx, session, as_="teach_back", item="pi_teach")
    [(handed_session, handed_item, handed_words, conversation_id)] = entry.calls
    assert (handed_session, handed_item, handed_words) == (session, "pi_teach", WORDS)
    # The conversation takes the id the submission reserved before handing its words over.
    assert conversation_id and reply["teachBackId"] == conversation_id
    assert (reply["attemptId"], reply["entry"]["questionMd"], reply["teachBack"]["status"]) == (
        None, "Why at or below?", "ongoing")
    assert _rows(paths, "SELECT submitted_as, teach_back_id, attempt_id FROM pad_block_submissions") == [
        ("teach_back", conversation_id, None)]


def test_a_crash_after_the_hand_off_is_recovered_by_the_reserved_conversation_id(tmp_path, monkeypatch):
    """The conversation opened, then the process died before the pad's reply: the retry finds the conversation by
    the id reserved before the hand-off and hands nothing over again."""

    paths, ctx, session = _sidecar(tmp_path)
    entry = _TeachBackEntry(paths, crash=True)
    _teach_back_pad(ctx, monkeypatch, entry)
    with pytest.raises(RuntimeError):
        _submit(ctx, session, as_="teach_back", item="pi_teach")
    reserved = _rows(paths, "SELECT teach_back_id FROM pad_block_submissions")[0][0]
    entry.crash = False
    again = _submit(ctx, session, as_="teach_back", item="pi_teach")
    assert len(entry.calls) == 1 and entry.calls[0][3] == reserved
    assert (again["duplicate"], again["teachBackId"], again["teachBack"]["status"]) == (True, reserved, "ongoing")
    assert again["teachBack"]["state"]["conversation_id"] == reserved


def test_a_teach_back_graded_at_once_then_a_crash_is_found_completed_never_started_again(tmp_path, monkeypatch):
    """The student could not ask, the transcript was graded at once (its attempt recorded, the checkpoint cleared),
    then the process died before the pad's reply: the retry finds the attempt by the conversation's id."""

    paths, ctx, session = _sidecar(tmp_path)
    entry = _TeachBackEntry(paths, done=True, crash=True)
    _teach_back_pad(ctx, monkeypatch, entry)
    with pytest.raises(RuntimeError):
        _submit(ctx, session, as_="teach_back", item="pi_teach")
    entry.crash = False
    again = _submit(ctx, session, as_="teach_back", item="pi_teach")
    reserved = again["teachBackId"]
    assert len(entry.calls) == 1
    assert (again["teachBack"]["status"], again["attemptId"]) == ("completed", f"att_{reserved}")
    assert _rows(paths, "SELECT COUNT(*) FROM practice_attempts") == [(1,)]
    # The tag reads the attempt the conversation became.
    block = call(ctx, "pad.get", {"padId": "pad_r"})["blocks"][0]
    assert block["submissions"][0]["attemptId"] == f"att_{reserved}"


def test_a_crash_before_the_hand_off_hands_the_frozen_words_over_under_the_same_id(tmp_path, monkeypatch):
    """The entry point refused, or the process died before it opened anything: the retry hands the submission's
    frozen words over again, under the id it reserved, even after the block was edited."""

    paths, ctx, session = _sidecar(tmp_path)

    class Refusing(_TeachBackEntry):
        def __call__(self, ctx_, params, *, conversation_id=None):
            self.calls.append((params.session_id, params.practice_item_id, params.answer_md, conversation_id))
            raise SidecarError("provider_unavailable", "The student is unavailable.", retryable=True)

    refusing = Refusing(paths)
    _teach_back_pad(ctx, monkeypatch, refusing)
    with pytest.raises(SidecarError):
        _submit(ctx, session, as_="teach_back", item="pi_teach")
    call(ctx, "pad.apply", {"clientId": "c", "seq": 2, "padId": "pad_r", "ops": [
        {"op": "edit_block", "blockId": "b1", "expectedHead": "v1", "bodyMd": "reworded", "versionId": "v2"}]})
    entry = _TeachBackEntry(paths)
    _patch_entry(monkeypatch, entry)
    again = _submit(ctx, session, as_="teach_back", item="pi_teach")
    assert entry.calls[0][2:] == (WORDS, refusing.calls[0][3]) and again["teachBack"]["status"] == "ongoing"


def test_two_submissions_with_the_same_words_are_never_taken_for_one_conversation(tmp_path, monkeypatch):
    """Recovery is by the conversation's id, not its words: a second submission of identical words, while the first's
    conversation is under way, is refused (its words would be taken as the first conversation's next answer),
    not reported as the first conversation."""

    paths, ctx, session = _sidecar(tmp_path)
    entry = _TeachBackEntry(paths)
    _teach_back_pad(ctx, monkeypatch, entry, _block("b1", WORDS, version_id="v1"),
                    _block("b2", WORDS, version_id="v2", position="a1"))
    first = _submit(ctx, session, as_="teach_back", item="pi_teach")
    with pytest.raises(SidecarError) as refused:
        _submit(ctx, session, submission_id="sub_2", block_id="b2", version_id="v2", as_="teach_back",
                item="pi_teach")
    assert refused.value.code == "teach_back_in_progress"
    assert len(entry.calls) == 1 and first["teachBack"]["status"] == "ongoing"
    assert _rows(paths, "SELECT submission_id FROM pad_block_submissions") == [("sub_1",)]
