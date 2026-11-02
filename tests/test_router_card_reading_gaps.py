"""The router card checks the passage a reading-derived gap was written on
(followups-nov1c E: exam-material protection, not privacy).

The card's open problems show a named gap's learner words (G5), withheld when
the words were written about protected work: the shared leakage rule checked
the gap's own answer and item only. A gap named from a reading (a question the
learner asked in the Reader, an active-reading answer, a figure prediction) was
written on a passage that the rule never looked at, so a question asked on an
exam paper's passage reached the router model in the learner's words. The card
now also checks that passage through the one exam predicate
(``learner_protection.PastWork.reading_reason``, the chat's
``source_ref_protected``): exam or held-out material, or a passage that cannot
be established, keeps the entry and withholds the words. Every other gap is
shown exactly as before.
"""

from __future__ import annotations

import json

from learnloop import learner_protection as protection
from learnloop.content.sources import exam_material as EM

from tests.daily_plan_fakes import iso
from tests.test_mcp_c1a_landing import A, LAST, _card_inputs, _world

EXAM_WORDS = "MY_QUESTION_ON_THE_EXAM_PAPER_PASSAGE_5521"
BOOK_WORDS = "MY_QUESTION_ON_THE_TEXTBOOK_PASSAGE_8812"
PRACTICE_WORDS = "MY_QUESTION_DURING_PRACTICE_4410"
FORMATIVE_WORDS = "MY_ACTIVE_READING_ANSWER_ON_THE_EXAM_6603"


def _exam_passage(monkeypatch, *spans) -> None:
    """The exam predicate: these (extraction, span) passages are exam material."""

    material = EM.Material(spans=frozenset(spans))
    monkeypatch.setattr(EM, "exam_material",
                        lambda _vault, _repo: EM.ExamMaterial(material=material, held_out=EM.Material()))


def _question(env, question_id: str, *, extraction_id: str | None, span_id: str | None) -> None:
    context = {"extraction_id": extraction_id, "span_id": span_id} if extraction_id else None
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO question_events(id, context, question_md, answer_status, source_context_json, created_at) "
            "VALUES (?, ?, 'a question', 'answered', ?, ?)",
            (question_id, "library" if extraction_id else "practice",
             json.dumps(context) if context else None, iso(LAST)))
        connection.commit()


def _gap(env, gap_id: str, source_kind: str, source_id: str, words: str) -> None:
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO learner_text_gaps(id, source_kind, source_id, attempt_id, practice_item_id, "
            "anchor_learning_object_id, learner_text, chooser, context_judge, kind, action, algorithm_version, "
            "pipeline_version, created_at) VALUES (?, ?, ?, NULL, NULL, 'lo_m1', ?, 'context_model', ?, "
            "'misconception', 'unplaced', ?, 'v1', ?)",
            (gap_id, source_kind, source_id, words, "tutor" if source_kind == "tutor_question" else "gap_reader",
             A, iso(LAST)))
        connection.commit()


def _gaps(env) -> dict[str, dict]:
    entries = [entry for entry in _card_inputs(env).open_hypotheses if entry["kind"] == "learner_named_misconception"]
    return {entry["statement"] or entry["withheld"]: entry for entry in entries}


def test_a_reader_question_asked_on_an_exam_passage_keeps_its_entry_and_never_its_words(tmp_path, monkeypatch):
    env = _world(tmp_path, monkeypatch)
    _exam_passage(monkeypatch, ("ext_exam", "s1"))
    _question(env, "q_exam", extraction_id="ext_exam", span_id="s1")
    _question(env, "q_book", extraction_id="ext_book", span_id="s2")
    _question(env, "q_practice", extraction_id=None, span_id=None)
    _gap(env, "gap_exam", "tutor_question", "q_exam", EXAM_WORDS)
    _gap(env, "gap_book", "tutor_question", "q_book", BOOK_WORDS)
    _gap(env, "gap_practice", "tutor_question", "q_practice", PRACTICE_WORDS)
    inputs = _card_inputs(env)
    entries = [entry for entry in inputs.open_hypotheses if entry["kind"] == "learner_named_misconception"]
    assert len(entries) == 3  # every gap keeps its entry
    statements = sorted(entry["statement"] for entry in entries if entry["statement"])
    assert statements == sorted([BOOK_WORDS, PRACTICE_WORDS])  # a textbook passage and practice: as before
    [withheld] = [entry for entry in entries if entry["statement"] is None]
    assert withheld["withheld"] == protection.WITHHELD_EXAM and withheld["topic"]
    assert EXAM_WORDS not in json.dumps(list(inputs.open_hypotheses), default=str)


def test_an_active_reading_answer_on_an_exam_passage_is_withheld(tmp_path, monkeypatch):
    env = _world(tmp_path, monkeypatch)
    _exam_passage(monkeypatch, ("ext_exam", "s3"))
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO reader_authored_questions (id, extraction_id, section_id, question_md, expected_answer_md, "
            "span_ids_json, prompt_version, created_at, updated_at) VALUES ('raq_exam', 'ext_exam', 'u1', 'Q?', "
            "'A.', '[\"s3\"]', 'v1', ?, ?)", (iso(LAST), iso(LAST)))
        connection.commit()
    _gap(env, "gap_formative", "reader_formative", "raq_exam", FORMATIVE_WORDS)
    [entry] = _gaps(env).values()
    assert entry["statement"] is None and entry["withheld"] == protection.WITHHELD_EXAM


def test_a_reading_derived_gap_whose_passage_cannot_be_established_fails_closed(tmp_path, monkeypatch):
    """The question (or the active-reading question) is not on record: which
    passage it was written on is unknown, so its words are withheld."""

    env = _world(tmp_path, monkeypatch)
    _gap(env, "gap_question_gone", "tutor_question", "q_never_recorded", EXAM_WORDS)
    _gap(env, "gap_formative_gone", "reader_formative", "raq_never_recorded", FORMATIVE_WORDS)
    entries = [entry for entry in _card_inputs(env).open_hypotheses if entry["kind"] == "learner_named_misconception"]
    assert len(entries) == 2
    assert all(entry["statement"] is None and entry["withheld"] == protection.WITHHELD_UNREADABLE
               for entry in entries)


def test_an_unreadable_exam_predicate_withholds_a_reading_gaps_words(tmp_path, monkeypatch):
    env = _world(tmp_path, monkeypatch)
    _question(env, "q_book", extraction_id="ext_book", span_id="s2")
    _gap(env, "gap_book", "tutor_question", "q_book", BOOK_WORDS)

    def unreadable(_vault, _repo):
        raise RuntimeError("source sets unreadable")

    monkeypatch.setattr(EM, "exam_material", unreadable)
    entries = [entry for entry in _card_inputs(env).open_hypotheses if entry["kind"] == "learner_named_misconception"]
    assert [entry["statement"] for entry in entries] == [None]
    assert BOOK_WORDS not in json.dumps(entries, default=str)
