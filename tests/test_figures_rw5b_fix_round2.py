"""RW5b fix round 2 (orchestrator re-review; docs/reviews/reader-workbench-RW5b.md).

F8: a library offer on a repeated or forked ask builds when pressed (the
ledger rows the ask's notes name were written under the first ask's id: a
second identical ask is answered from the ledger, and RW4d's fork copies the
notes under a new id). F10: the tutor's ``figure_explorable`` rows hash only
their input, so a later owner or verifier label can pair with them, and keep
the verdict in a small JSON rationale. Fakes only: no model is called.
"""

from __future__ import annotations

import json

import pytest

from learnloop.ai.execution import content_key
from learnloop.figure_admission import TUTOR_EXPLORABLE_TASK, tutor_explorable_judgment_id
from learnloop.ids import new_ulid
from learnloop.source_retrieval import library_ask as LA
from learnloop.tutor import ai_contracts as C
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from tests.figure_fixtures import EXTRACTION, AuthorFake, build, call, context, rows
from tests.test_figure_offers import ExplorableOrganizer, _ask, _tutor_event, _vault


def _press(paths, offer_ref: str, span: str = "p3") -> tuple[dict, AuthorFake]:
    author = AuthorFake()
    ctx = context(paths.root, author=author)
    return build(ctx, {"extractionId": EXTRACTION, "spanIds": [span], "origin": "library", "offerRef": offer_ref}), author


# --- F8: a repeated or forked ask's offer builds ----------------------------------------------------

def test_the_same_question_asked_twice_offers_and_builds_on_the_second_ask(tmp_path):
    paths, repository = _vault(tmp_path)
    organizer = ExplorableOrganizer()
    first = _ask(repository)
    LA.organize(load_vault(paths.root), repository, first, client=organizer)
    second = _ask(repository)
    LA.organize(load_vault(paths.root), repository, second, client=organizer)
    # The second ask was answered from the ledger (no second call), so its notes
    # name the rows written under the first ask's id.
    assert len(organizer.prompts) == 1
    notes = {note["key"]: note for note in LA.ask_row(repository, second)["organizer"]["notes"]}
    assert notes[f"{EXTRACTION}:p3"]["explorable"] is True
    ledger = {row["id"]: row for row in rows(repository, "judgment_ledger")}
    assert ledger[notes[f"{EXTRACTION}:p3"]["ledger_id"]]["left_id"] == first
    result, author = _press(paths, second)
    assert result["figure"]["origin"] == "library" and author.calls == 1


def test_a_forked_ask_offers_and_builds_on_the_fork(tmp_path):
    paths, repository = _vault(tmp_path)
    ask_id = _ask(repository)
    LA.organize(load_vault(paths.root), repository, ask_id, client=ExplorableOrganizer())
    fork = "la_" + new_ulid()
    with repository.connection() as connection:
        # RW4d: a second comparison of a kept question forks the ask (kept_comparisons._fork_for).
        LA.ask_store.fork_ask(connection, ask_id, new_id=fork, created_at="2026-10-23T11:00:00Z")
        connection.commit()
    assert LA.ask_row(repository, fork)["organizer"]["notes"] == LA.ask_row(repository, ask_id)["organizer"]["notes"]
    result, author = _press(paths, fork, span="p4")
    assert result["figure"]["origin"] == "library" and author.calls == 1


def test_a_library_note_pointing_at_another_tasks_yes_row_is_refused(tmp_path):
    """Without the left id the press still names one judgment: the note's ledger
    row must be the organizer's own (``library_contribution``) for this block. A
    tutor ``figure_explorable`` yes on the same block (whose rationale now
    carries the verdict, F10) does not stand in for it."""

    paths, repository = _vault(tmp_path)
    ask_id = _ask(repository)
    LA.organize(load_vault(paths.root), repository, ask_id, client=ExplorableOrganizer(say_yes=()))
    event_id = _tutor_event(repository, [{"extraction_id": EXTRACTION, "span_id": "p3"}])
    tutor_row = tutor_explorable_judgment_id(event_id, EXTRACTION, "p3")
    organizer = LA.ask_row(repository, ask_id)["organizer"]
    organizer["notes"] = [{**note, "explorable": True, "ledger_id": tutor_row} if note["key"] == f"{EXTRACTION}:p3"
                          else note for note in organizer["notes"]]
    with repository.connection() as connection:
        connection.execute("UPDATE library_asks SET organizer_json = ? WHERE id = ?", (json.dumps(organizer), ask_id))
        connection.commit()
    author = AuthorFake()
    ctx = context(paths.root, author=author)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_request", {"extractionId": EXTRACTION, "spanIds": ["p3"], "origin": "library",
                                            "offerRef": ask_id})
    assert caught.value.code == "not_offered" and author.calls == 0


# --- F10: the tutor's ledger rows hash their input only ---------------------------------------------

def _tutor_rows(repository):
    return {row["right_id"]: row for row in rows(repository, "judgment_ledger") if row["task"] == TUTOR_EXPLORABLE_TASK}


def test_the_tutors_explorable_rows_hash_the_input_not_the_verdict(tmp_path):
    from types import SimpleNamespace

    from learnloop.tutor import tutor_qa as TQ

    paths, repository = _vault(tmp_path)
    version = C.READER_TUTOR_EXPLORABLE_PROMPT_VERSION
    for verdict in ("yes", "no"):
        event_id = repository.insert_question_event({
            "context": "reader", "note_id": f"span:{EXTRACTION}/p2", "question_md": "what is f?", "answer_md": "a",
            "source_context": {}, "created_at": "2026-10-23T10:00:00Z"})
        answer = SimpleNamespace(explorable=[C.ExplorableCitation(extraction_id=EXTRACTION, span_id="p4",
                                                                  explorable=verdict)])
        TQ._record_explorable_verdicts(repository, event_id, answer, model="fake-tutor-model",
                                       prompt_version=version, clock=None)
        row = next(row for row in rows(repository, "judgment_ledger") if row["left_id"] == event_id)
        assert row["verdict"] == verdict
        # The input only: the prompt version, the answer's question event and the block.
        assert row["input_hash"] == content_key([version, event_id, EXTRACTION, "p4"])[:40]
        assert json.loads(row["rationale"]) == {"explorable": verdict}


def test_the_tutor_press_still_reads_its_rows(tmp_path):
    paths, repository = _vault(tmp_path)
    event_id = _tutor_event(repository, [{"extraction_id": EXTRACTION, "span_id": "p4"}])
    assert json.loads(_tutor_rows(repository)[f"{EXTRACTION}:p4"]["rationale"]) == {"explorable": "yes"}
    author = AuthorFake()
    ctx = context(paths.root, author=author)
    result = build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p4"], "origin": "tutor", "offerRef": event_id})
    assert result["figure"]["origin"] == "tutor" and author.calls == 1
