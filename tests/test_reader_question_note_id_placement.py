"""A Reader question recorded before its source context was (followups after
nov1c: the provenance follow-up of reading-derived gaps).

``reading_sources`` places the passage a Reader question was asked on from its
``question_events.source_context_json``. Questions recorded before migration 117
kept only the synthetic ``note_id`` span key (``tutor_qa.reader_span_key``:
``span:<extraction>/<span>``), so their context is NULL and they failed closed as
unreadable even though the key names the passage exactly. Such a question is now
placed from its ``note_id`` and checked against exam material like any other
placed span; anything still unplaceable (no key, a key that names no block, a
recorded context that names nothing) keeps failing closed.
"""

from __future__ import annotations

import json

from learnloop import learner_protection as protection
from learnloop.diagnosis.text_gaps.provenance import reading_sources

from tests.daily_plan_fakes import iso
from tests.mcp_c1a_landing_helpers import LAST, _card_inputs, _world
from tests.router_card_reading_gaps_helpers import _exam_passage, _gap


def _question(env, question_id: str, *, context: str, note_id: str | None,
              source_context_json: str | None = None) -> None:
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO question_events(id, context, note_id, question_md, answer_status, source_context_json, "
            "created_at) VALUES (?, ?, ?, 'a question', 'answered', ?, ?)",
            (question_id, context, note_id, source_context_json, iso(LAST)))
        connection.commit()


def _entries(env) -> list[dict]:
    return [entry for entry in _card_inputs(env).open_hypotheses if entry["kind"] == "learner_named_misconception"]


def test_a_reader_question_with_no_source_context_is_placed_from_its_note_id(tmp_path, monkeypatch):
    env = _world(tmp_path, monkeypatch)
    _question(env, "q_legacy", context="reader", note_id="span:ext_book/s2")
    with env.repository.connection() as connection:
        sources, complete = reading_sources(connection, "tutor_question", "q_legacy")
    assert complete is True
    assert [dict(source) for source in sources] == [{"extraction_id": "ext_book", "span_ids": ["s2"]}]


def test_a_legacy_reader_question_is_checked_against_exam_material(tmp_path, monkeypatch):
    env = _world(tmp_path, monkeypatch)
    _exam_passage(monkeypatch, ("ext_exam", "s1"))
    _question(env, "q_exam", context="reader", note_id="span:ext_exam/s1")
    _question(env, "q_book", context="reader", note_id="span:ext_book/s2")
    _gap(env, "gap_exam", "tutor_question", "q_exam", "WORDS_ON_THE_EXAM_PASSAGE_7310")
    _gap(env, "gap_book", "tutor_question", "q_book", "WORDS_ON_THE_TEXTBOOK_PASSAGE_7311")
    entries = _entries(env)
    assert len(entries) == 2
    assert [entry["statement"] for entry in entries if entry["statement"]] == ["WORDS_ON_THE_TEXTBOOK_PASSAGE_7311"]
    [withheld] = [entry for entry in entries if not entry["statement"]]
    assert withheld["withheld"] == protection.WITHHELD_EXAM
    assert "WORDS_ON_THE_EXAM_PASSAGE_7310" not in json.dumps(entries, default=str)


def test_a_reader_question_that_still_cannot_be_placed_fails_closed(tmp_path, monkeypatch):
    env = _world(tmp_path, monkeypatch)
    _exam_passage(monkeypatch, ("ext_exam", "s1"))
    cases = {
        "q_no_key": (None, None),
        "q_note_key": ("note_vectors", None),
        "q_no_block": ("span:ext_book", None),
        "q_empty_block": ("span:ext_book/", None),
        "q_empty_reading": ("span:/s2", None),
        # A context that was recorded (here naming nothing) is what the question was
        # asked on: the key never stands in for it.
        "q_recorded_empty": ("span:ext_book/s2", json.dumps({})),
        "q_recorded_unreadable": ("span:ext_book/s2", "{not json"),
    }
    for question_id, (note_id, raw) in cases.items():
        _question(env, question_id, context="reader", note_id=note_id, source_context_json=raw)
        _gap(env, f"gap_{question_id}", "tutor_question", question_id, f"WORDS_{question_id.upper()}")
    entries = _entries(env)
    assert len(entries) == len(cases)
    assert all(entry["statement"] is None and entry["withheld"] == protection.WITHHELD_UNREADABLE
               for entry in entries)
    with env.repository.connection() as connection:
        for question_id in cases:
            assert reading_sources(connection, "tutor_question", question_id) == ((), False)


def test_a_question_outside_the_reader_is_unchanged(tmp_path, monkeypatch):
    """Only the Reader keys its questions by span: a library or practice question
    with no recorded context reads no passage, as before."""

    env = _world(tmp_path, monkeypatch)
    _question(env, "q_library", context="library", note_id="note_vectors")
    _question(env, "q_practice", context="practice", note_id=None)
    with env.repository.connection() as connection:
        assert reading_sources(connection, "tutor_question", "q_library") == ((), True)
        assert reading_sources(connection, "tutor_question", "q_practice") == ((), True)
