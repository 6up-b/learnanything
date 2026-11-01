"""Learner-blindness relax, Codex review fixes (docs/reviews/learner-blindness-relax-codex-review.md).

F1: a stored tutor answer the Reader tutor's learner state re-shows is checked
against today's protection by the passages it may have been written from
(the item's linked passage pool, the provider's recorded spans, followed
references, citations); a passage marked held out since withholds it, and so
do passages that cannot be established.

F2: with both RW1c switches off, a question naming a workbench session bound
to an item carries no learner state (nothing guards the call or attaches its
help to the item), whatever the client's cold flag.

F3: an earlier workbench trace shown in the prior-analysis arm counts its
item as a solution read and leaves the diagnosis's input record incomplete.

Fakes only; no model call anywhere.
"""

from __future__ import annotations

import json
from typing import Any

from learnloop import reader_learner_state as RLS
from learnloop.vault.loader import load_vault
from tests.test_learner_blindness_relax import _ask, _attempt, _reader, _seed_learner

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


def test_a_stored_answer_whose_linked_passage_is_held_out_since_is_withheld(tmp_path, monkeypatch):
    from learnloop import learner_protection

    paths, repository, _seeded = _closed_window_vault(tmp_path)
    vault = load_vault(paths.root)
    shown = RLS.build(vault, repository, learning_object_ids=["lo_matrices"], now_iso=NOW)
    assert "SECRET_WORKED_SOLUTION" in _exchange(shown)["answer_shown"]
    # The item's learning object is linked to ext_book/s2; that passage is marked held out since.
    _hold_out(monkeypatch, ("ext_book", "s2"))
    held = RLS.build(vault, repository, learning_object_ids=["lo_matrices"], now_iso=NOW)
    exchange = _exchange(held)
    # The item itself is still ordinary practice: the learner's own question shows ...
    assert "MY_OWN_FEEDBACK_QUESTION" in exchange["learner_question"]
    # ... and the answer, which may have been written from the held-out passage, does not.
    assert "answer_shown" not in exchange
    assert exchange["answer_left_out"] == learner_protection.WITHHELD_EXAM
    assert "SECRET_WORKED_SOLUTION" not in json.dumps(held.state)
    assert held.counts["answers_left_out"] == 1


def test_a_stored_answer_retrieved_from_a_passage_held_out_since_is_withheld(tmp_path, monkeypatch):
    from learnloop import learner_protection

    paths, repository, seeded = _closed_window_vault(tmp_path)
    repository.insert_question_event({
        "context": "practice", "practice_item_id": seeded["plain"], "attempt_id": None,
        "question_md": "RETRIEVED_QUESTION", "answer_md": "RETRIEVED_ANSWER_TEXT", "answer_status": "answered",
        "created_at": "2026-09-05T09:00:00Z",
        "source_context": {"source_retrieval": {"basis": "retrieved_verified", "span_keys": ["ext_book/s11"]}},
    })
    vault = load_vault(paths.root)
    before = RLS.build(vault, repository, learning_object_ids=["lo_matrices"], now_iso=NOW)
    assert "RETRIEVED_ANSWER_TEXT" in json.dumps(before.state)
    _hold_out(monkeypatch, ("ext_book", "s11"))  # not a link of the item's topic: only the record names it
    after = RLS.build(vault, repository, learning_object_ids=["lo_matrices"], now_iso=NOW)
    entries = after.state["topics"][0]["recent_tutor_questions"]
    retrieved = next(entry for entry in entries if "RETRIEVED_QUESTION" in entry["learner_question"])
    assert retrieved["answer_left_out"] == learner_protection.WITHHELD_EXAM
    assert "RETRIEVED_ANSWER_TEXT" not in json.dumps(after.state)
    # The other answer (linked passages only, none held out) still shows.
    assert "SECRET_WORKED_SOLUTION" in json.dumps(after.state)


def test_an_answer_whose_passages_cannot_be_established_is_withheld():
    linked = [{"extraction_id": "ext_a", "span_ids": ["a1"]}]
    # Nothing recorded: the linked pool is what it was drawn from.
    assert RLS.answer_source_refs(None, linked) == linked
    refs = RLS.answer_source_refs({
        "source_retrieval": {"basis": "pinned", "span_keys": ["ext_p:p1"],
                             "references": {"resolved": [{"extraction_id": "ext_r", "span_id": "r1",
                                                          "spans": ["r1", "r2"]}], "unresolved": []}},
        "delivery": {"references": {"resolved": [{"extraction_id": "ext_d", "span_id": "d1", "spans": []}]}},
        "citations": [{"extraction_id": "ext_c", "span_id": "c1", "label": "x"}],
    }, linked)
    assert {(ref["extraction_id"], tuple(ref["span_ids"])) for ref in refs} == {
        ("ext_a", ("a1",)), ("ext_p", ("p1",)), ("ext_r", ("r1", "r1", "r2")), ("ext_d", ("d1",)),
        ("ext_c", ("c1",))}
    # A retrieval that delivered passages without naming them, or an unreadable record: nothing established.
    assert RLS.answer_source_refs({"source_retrieval": {"basis": "retrieved_verified"}}, linked) is None
    assert RLS.answer_source_refs({"source_retrieval": {"basis": "pinned", "span_keys": ["nokey"]}}, linked) is None
    assert RLS.answer_source_refs({"source_retrieval": "garbled"}, linked) is None
    assert RLS.answer_source_refs({"citations": [{"label": "no span"}]}, linked) is None
    assert RLS.answer_source_refs("garbled", linked) is None
    # A failed retrieval fell back to the linked passages: the pool covers it.
    assert RLS.answer_source_refs({"source_retrieval": {"basis": "lo_provenance", "reason": "x"}}, linked) == linked


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
    from tests.test_learner_blindness_relax import _assembled

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
