"""Learner-blindness relax, Codex review fixes (docs/reviews/learner-blindness-relax-codex-review.md).

F1: closed structurally (orchestrator ruling R1): the Reader tutor's learner
state never re-shows stored tutor answer text, so no provenance chain can
carry exam-derived text into it; the learner's own questions and outcomes
still show.

F2: with both RW1c switches off, a question naming a workbench session bound
to an item carries no learner state (nothing guards the call or attaches its
help to the item), whatever the client's cold flag.

F3: an earlier workbench trace shown in the prior-analysis arm counts its
item as a solution read and leaves the diagnosis's input record incomplete.

Fakes only; no model call anywhere.
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

from learnloop import reader_learner_state as RLS
from learnloop.vault.loader import load_vault
from tests.learner_blindness_relax_helpers import _ask, _attempt, _reader, _seed_learner

NOW = "2026-10-01T00:00:00Z"


def _hold_out(monkeypatch, *keys: tuple[str, str]) -> None:
    """From now on the exam predicate holds these spans out (a unit marked held out since)."""

    from learnloop.content.sources import exam_material as EM

    real = EM.exam_material
    extra = EM.Material(spans=frozenset(keys))

    def patched(vault_or_sets: Any, repository: Any) -> Any:
        found = real(vault_or_sets, repository)
        return EM.ExamMaterial(material=found.material.union(extra), held_out=found.held_out.union(extra),
                               runs=found.runs)

    monkeypatch.setattr(EM, "exam_material", patched)


def _closed_window_vault(tmp_path):
    from tests.library_ask_fixtures import build_library_vault

    paths, repository, _spans = build_library_vault(tmp_path / "vault")
    seeded = _seed_learner(paths, repository)
    _attempt(paths.sqlite_path, "att_now_right", item_id=seeded["plain"], lo_id="lo_matrices",
             at="2026-09-04T09:00:00Z", correctness=1.0)
    return paths, repository, seeded


def _exchange(state: RLS.ReaderLearnerState) -> dict[str, Any]:
    [topic] = state.state["topics"]
    [exchange] = topic["recent_tutor_questions"]
    return exchange


# -- F1 ----------------------------------------------------------------------------------------------
#
# Closed structurally (orchestrator ruling R1): the Reader learner state never
# re-shows stored tutor answer text, so no provenance chain (a held-out
# passage, a retrieval, an earlier turn of the thread, a cross-item feedback
# chain) can carry exam-derived text into it. The earlier reproductions are
# kept: each now passes because the answer text is absent, before and after
# the protection changes, while the learner's own question still shows.


def _texts(state: RLS.ReaderLearnerState) -> str:
    return json.dumps(state.state)


def _entries(state: RLS.ReaderLearnerState) -> list[dict[str, Any]]:
    return state.state["topics"][0]["recent_tutor_questions"]


def _assert_questions_only(state: RLS.ReaderLearnerState) -> None:
    for entry in _entries(state):
        assert set(entry) == {"date", "when", "learner_question"}, entry


def test_a_stored_answer_whose_linked_passage_is_held_out_since_is_never_shown(tmp_path, monkeypatch):
    paths, repository, _seeded = _closed_window_vault(tmp_path)
    vault = load_vault(paths.root)
    before = RLS.build(vault, repository, learning_object_ids=["lo_matrices"], now_iso=NOW)
    assert "SECRET_WORKED_SOLUTION" not in _texts(before)
    assert "MY_OWN_FEEDBACK_QUESTION" in _exchange(before)["learner_question"]
    _hold_out(monkeypatch, ("ext_book", "s2"))  # the item's topic's linked passage
    after = RLS.build(vault, repository, learning_object_ids=["lo_matrices"], now_iso=NOW)
    # The item is still ordinary practice: the learner's own question shows; no answer text ever does.
    assert "MY_OWN_FEEDBACK_QUESTION" in _exchange(after)["learner_question"]
    assert "SECRET_WORKED_SOLUTION" not in _texts(after)
    _assert_questions_only(after)
    assert set(after.counts) == {"topics", "attempts", "exchanges"}


def test_a_stored_answer_retrieved_from_a_passage_held_out_since_is_never_shown(tmp_path, monkeypatch):
    paths, repository, seeded = _closed_window_vault(tmp_path)
    repository.insert_question_event({
        "context": "practice", "practice_item_id": seeded["plain"], "attempt_id": None,
        "question_md": "RETRIEVED_QUESTION", "answer_md": "RETRIEVED_ANSWER_TEXT", "answer_status": "answered",
        "created_at": "2026-09-05T09:00:00Z",
        "source_context": {"source_retrieval": {"basis": "retrieved_verified", "span_keys": ["ext_book/s11"]}},
    })
    vault = load_vault(paths.root)
    for held_out in (False, True):
        if held_out:
            _hold_out(monkeypatch, ("ext_book", "s11"))
        state = RLS.build(vault, repository, learning_object_ids=["lo_matrices"], now_iso=NOW)
        assert "RETRIEVED_ANSWER_TEXT" not in _texts(state) and "SECRET_WORKED_SOLUTION" not in _texts(state)
        assert any("RETRIEVED_QUESTION" in entry["learner_question"] for entry in _entries(state))
        _assert_questions_only(state)


def _retrieved_turn(repository: Any, item_id: str, *, context: str, attempt_id: str | None, question: str,
                    answer: str, at: str, span_key: str) -> None:
    repository.insert_question_event({
        "context": context, "practice_item_id": item_id, "attempt_id": attempt_id, "question_md": question,
        "answer_md": answer, "answer_status": "answered", "created_at": at,
        "source_context": {"source_retrieval": {"basis": "retrieved_verified", "span_keys": [span_key]}},
    })


def test_a_later_turn_given_an_earlier_turn_from_a_passage_held_out_since_shows_no_answer(tmp_path, monkeypatch):
    """Codex re-review F1 (Q1 from S, Q2 from clean T with Q1 in its thread):
    neither answer is in the state, before or after S is held out."""

    paths, repository, seeded = _closed_window_vault(tmp_path)
    plain = seeded["plain"]
    _retrieved_turn(repository, plain, context="practice", attempt_id=None, question="Q1_THREAD_QUESTION",
                    answer="Q1_ANSWER_FROM_S", at="2026-09-05T09:00:00Z", span_key="ext_book/s11")
    _retrieved_turn(repository, plain, context="practice", attempt_id=None, question="Q2_THREAD_QUESTION",
                    answer="Q2_ANSWER_RESTATING_Q1", at="2026-09-05T09:05:00Z", span_key="ext_book/s12")
    vault = load_vault(paths.root)
    for held_out in (False, True):
        if held_out:
            _hold_out(monkeypatch, ("ext_book", "s11"))
        state = RLS.build(vault, repository, learning_object_ids=["lo_matrices"], now_iso=NOW)
        text = _texts(state)
        assert "Q1_ANSWER_FROM_S" not in text and "Q2_ANSWER_RESTATING_Q1" not in text
        assert "Q1_THREAD_QUESTION" in text and "Q2_THREAD_QUESTION" in text
        _assert_questions_only(state)


def test_an_earlier_feedback_turn_of_the_attempt_carries_no_answer(tmp_path, monkeypatch):
    paths, repository, seeded = _closed_window_vault(tmp_path)
    plain = seeded["plain"]
    _retrieved_turn(repository, plain, context="feedback", attempt_id="att_last_wrong",
                    question="EARLIER_FEEDBACK_QUESTION", answer="EARLIER_FEEDBACK_FROM_S",
                    at="2026-09-02T09:30:00Z", span_key="ext_book/s11")
    _retrieved_turn(repository, plain, context="practice", attempt_id=None, question="LATER_PRACTICE",
                    answer="LATER_PRACTICE_ANSWER", at="2026-09-05T09:00:00Z", span_key="ext_book/s12")
    _hold_out(monkeypatch, ("ext_book", "s11"))
    vault = load_vault(paths.root)
    state = RLS.build(vault, repository, learning_object_ids=["lo_matrices"], now_iso=NOW)
    text = _texts(state)
    for answer in ("SECRET_WORKED_SOLUTION", "EARLIER_FEEDBACK_FROM_S", "LATER_PRACTICE_ANSWER"):
        assert answer not in text
    assert "MY_OWN_FEEDBACK_QUESTION" in text and "LATER_PRACTICE" in text
    _assert_questions_only(state)


def test_a_cross_item_feedback_chain_carries_no_answer(tmp_path, monkeypatch):
    """Codex job 20261101-160205-68yc5y: attempt A, an explicit item B, a later
    turn restating B's solution, then B exam-protected. No answer text from any
    turn is in the state; B's own exchanges leave with B's protection."""

    from learnloop import learner_protection

    paths, repository, seeded = _closed_window_vault(tmp_path)
    vault = load_vault(paths.root)
    plain = seeded["plain"]
    other = next(item_id for item_id, item in sorted(vault.practice_items.items())
                 if item.learning_object_id == "lo_matrices" and item_id not in (plain, seeded["probe"]))
    _retrieved_turn(repository, other, context="practice", attempt_id=None, question="ASK_ABOUT_B",
                    answer="B_WORKED_SOLUTION", at="2026-09-05T09:00:00Z", span_key="ext_book/s12")
    _retrieved_turn(repository, plain, context="feedback", attempt_id="att_now_right",
                    question="LATER_ASK_ON_A", answer="RESTATES_B_WORKED_SOLUTION", at="2026-09-05T09:10:00Z",
                    span_key="ext_book/s12")
    before = RLS.build(vault, repository, learning_object_ids=["lo_matrices"], now_iso=NOW)
    assert "ASK_ABOUT_B" in _texts(before) and "LATER_ASK_ON_A" in _texts(before)
    real = learner_protection.withheld_items

    def protect_b(*args: Any, **kwargs: Any) -> Any:
        found = real(*args, **kwargs)
        return replace(found, reasons={**found.reasons, other: learner_protection.WITHHELD_EXAM})

    monkeypatch.setattr(learner_protection, "withheld_items", protect_b)
    after = RLS.build(vault, repository, learning_object_ids=["lo_matrices"], now_iso=NOW)
    for state in (before, after):
        text = _texts(state)
        assert "B_WORKED_SOLUTION" not in text and "SECRET_WORKED_SOLUTION" not in text
        _assert_questions_only(state)
    assert "ASK_ABOUT_B" not in _texts(after)  # B's exchange leaves with B's protection
    assert "LATER_ASK_ON_A" in _texts(after)  # the learner's own words on A stay


def test_the_module_never_reads_stored_answer_text():
    """Structural pin for ruling R1: the Reader learner state selects no answer
    column and imports none of the tutor's answer readers."""

    import inspect

    source = inspect.getsource(RLS)
    for name in ("answer_md", "delivered_answer_md", "SELECT *", "tutor_qa", "source_context_json"):
        assert name not in source, name


# -- F2 ----------------------------------------------------------------------------------------------


def _bound_session(repository: Any, item_id: str | None) -> str:
    from learnloop.ids import new_ulid

    session_id = "wbs_" + new_ulid()
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO workbench_sessions (id, practice_item_id, stem_md, import_status, origin, entry, "
            "extraction_id, span_ids_json, source_visible, created_at, updated_at) "
            "VALUES (?, ?, 'Solve it', ?, 'reader', 'work_through', 'ext_text', '[\"t3\"]', 1, ?, ?)",
            (session_id, item_id, "bound" if item_id else "none", NOW, NOW))
        connection.commit()
    return session_id


def test_with_both_rw1c_switches_off_a_bound_session_carries_no_learner_state(tmp_path, monkeypatch):
    paths, repository, tutor, ctx_factory = _reader(tmp_path, monkeypatch)  # both RW1c switches off
    seeded = _seed_learner(paths, repository)
    _attempt(paths.sqlite_path, "att_now_right", item_id=seeded["plain"], lo_id="lo_matrices",
             at="2026-09-04T09:00:00Z", correctness=1.0)
    session = _bound_session(repository, seeded["plain"])
    # The client omits coldActive; nothing on the server binds the question to its item.
    answer = _ask(ctx_factory, paths, workbenchSessionId=session)
    [prompt] = tutor.prompts
    assert "learner_state" not in prompt and "learner_confidence" not in prompt
    assert "SECRET_WORKED_SOLUTION" not in prompt and "MY_OWN_FEEDBACK_QUESTION" not in prompt
    state = answer["manifest"]["learnerState"]
    assert state["given"] is False and state["omitted"] == RLS.OMITTED_UNGUARDED_BINDING


def test_with_both_rw1c_switches_off_a_cold_bound_session_carries_none_as_cold(tmp_path, monkeypatch):
    paths, repository, tutor, ctx_factory = _reader(tmp_path, monkeypatch)
    seeded = _seed_learner(paths, repository)
    repository.create_followup_task(kind="cold_retry", case_kind="diagnosis", case_ref="case-cold",
                                    not_before="2026-01-01T00:00:00Z", selected_item_id=seeded["plain"])
    session = _bound_session(repository, seeded["plain"])
    answer = _ask(ctx_factory, paths, workbenchSessionId=session)
    [prompt] = tutor.prompts
    assert "learner_state" not in prompt and "MY_OWN_FEEDBACK_QUESTION" not in prompt
    assert answer["manifest"]["learnerState"]["omitted"] == RLS.OMITTED_COLD


def test_an_unbound_workbench_session_still_carries_the_learner_state(tmp_path, monkeypatch):
    paths, repository, tutor, ctx_factory = _reader(tmp_path, monkeypatch)
    _seed_learner(paths, repository)
    session = _bound_session(repository, None)
    answer = _ask(ctx_factory, paths, workbenchSessionId=session)
    [prompt] = tutor.prompts
    assert "MY_OWN_FEEDBACK_QUESTION" in prompt
    assert answer["manifest"]["learnerState"]["given"] is True


# -- F3 ----------------------------------------------------------------------------------------------


def test_an_earlier_workbench_trace_counts_its_item_and_leaves_the_record_incomplete(tmp_path):
    from learnloop.diagnosis.split import prior_analysis as PA
    from learnloop.diagnosis.split.provenance import diagnosis_record
    from tests.diagnosis_split_helpers import build_diagnosis_vault, seed_history
    from tests.learner_blindness_relax_helpers import _assembled

    paths = build_diagnosis_vault(tmp_path / "vault")
    vault, repository = seed_history(paths)
    base = _assembled(vault, repository, None)
    rows = base.blocks["history"]
    # A prior attempt that passed: no grader text, so its item is not otherwise a solution read.
    target = next((row for row in rows if not row.get("failed_criteria") and not row.get("fatal_errors")), rows[0])
    attempt = base.attempts[target["attempt_id"]]

    def reader(ids, before):  # a trace and no earlier diagnosis
        return {attempt.attempt_id: {"workbench_trace": {"note": "n", "assists": [
            {"order": 1, "assist": "hint", "text": "HINT_FROM_THE_SOLUTION"}]}}}

    on = _assembled(vault, repository, PA.PriorAnalysis(arm=PA.assign("on", "x"), read=reader))
    assert "HINT_FROM_THE_SOLUTION" in on.rendered()
    assert attempt.practice_item_id in on.reads.solution_items
    assert any(reason.startswith(PA.TRACE_UNRECORDED) and attempt.attempt_id in reason
               for reason in on.reads.unaccounted)
    with repository.connection() as connection:
        record = diagnosis_record(connection, on.reads)
        base_record = diagnosis_record(connection, base.reads)
    # Nothing is released from a diagnosis that read an earlier trace (even
    # with its item's window closed: what the assists' writers read is unknown).
    assert record.complete is False and base_record.complete is True
    assert attempt.practice_item_id in record.inputs.solution_items
    # The off arm (and no arm) records exactly what it did before.
    off = _assembled(vault, repository, PA.PriorAnalysis(arm=PA.assign("off", "x"), read=reader))
    assert off.reads == base.reads
