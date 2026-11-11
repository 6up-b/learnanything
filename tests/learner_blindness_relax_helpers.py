"""What other test files use from ``tests/test_learner_blindness_relax.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
from typing import Any

import pytest

from learnloop.db.connection import connect
from learnloop.vault.loader import load_vault


READER_SWITCHES = {"retrieval_enabled": False, "offers_enabled": False}
EVIDENCE_TABLE_HINTS = ("mastery", "claim", "certification", "facet_capability", "fsrs", "grading_evidence")


def _items_on(vault: Any, lo_id: str) -> list[str]:
    return sorted(item_id for item_id, item in vault.practice_items.items() if item.learning_object_id == lo_id)


def _attempt(sqlite_path: Path, attempt_id: str, *, item_id: str, lo_id: str, at: str, correctness: float | None,
             attempt_type: str = "independent_attempt", hints: int = 0, answer: str = "my answer",
             tap: int | None = None) -> None:
    with closing(connect(sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO practice_attempts (id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "learner_answer_md, correctness, rubric_score, hints_used, created_at, answer_confidence) "
            "VALUES (?, ?, ?, 'short_answer', ?, ?, ?, ?, ?, ?, ?)",
            (attempt_id, item_id, lo_id, attempt_type, answer, correctness,
             None if correctness is None else correctness * 4, hints, at, tap))
        connection.commit()


def _question(repository: Any, *, context: str, item_id: str, attempt_id: str | None, question: str, answer: str,
              at: str) -> str:
    return repository.insert_question_event({
        "context": context, "practice_item_id": item_id, "attempt_id": attempt_id, "question_md": question,
        "answer_md": answer, "answer_status": "answered", "created_at": at,
    })


def _evidence_counts(sqlite_path: Path) -> dict[str, int]:
    with closing(connect(sqlite_path, read_only=True)) as connection:
        tables = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
        wanted = [name for name in tables if name == "practice_attempts"
                  or any(hint in name for hint in EVIDENCE_TABLE_HINTS)]
        return {name: connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0] for name in sorted(wanted)}


def _reader(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, learner_state: bool | None = None):
    import learnloop_sidecar.handlers.reader as reader_handler
    from tests.library_ask_fixtures import build_library_vault, context, set_config
    from tests.source_service_fakes import tool_tutor

    paths, repository, _spans = build_library_vault(tmp_path / "vault")
    set_config(paths, "reader_tutor", **READER_SWITCHES)
    if learner_state is not None:
        set_config(paths, "reader_tutor", learner_state_enabled=learner_state)
    tutor = tool_tutor(answer_md="The determinant vanishes there, so t is a root.")

    class Ready:
        ready = True

    monkeypatch.setattr(reader_handler, "ready_tutor_qa_provider", lambda vault: ("fake", Ready(), tutor))
    return paths, repository, tutor, context


def _seed_learner(paths: Any, repository: Any) -> dict[str, str]:
    vault = load_vault(paths.root)
    items = _items_on(vault, "lo_matrices")
    assert len(items) >= 2, items
    plain, probe = items[0], items[1]
    sqlite = paths.sqlite_path
    _attempt(sqlite, "att_old_right", item_id=plain, lo_id="lo_matrices", at="2026-09-01T09:00:00Z",
             correctness=1.0, hints=2, tap=4)
    _attempt(sqlite, "att_last_wrong", item_id=plain, lo_id="lo_matrices", at="2026-09-02T09:00:00Z",
             correctness=0.0, tap=5)
    # A diagnostic probe: protected, so neither it nor anything asked about it shows.
    _attempt(sqlite, "att_probe", item_id=probe, lo_id="lo_matrices", at="2026-09-03T09:00:00Z",
             correctness=1.0, attempt_type="diagnostic_probe", tap=1)
    _question(repository, context="feedback", item_id=plain, attempt_id="att_last_wrong",
              question="MY_OWN_FEEDBACK_QUESTION why the eigenvalue?", answer="SECRET_WORKED_SOLUTION 42",
              at="2026-09-02T10:00:00Z")
    _question(repository, context="practice", item_id=probe, attempt_id="att_probe",
              question="PROBE_QUESTION_TEXT", answer="PROBE_ANSWER_TEXT", at="2026-09-03T09:30:00Z")
    return {"plain": plain, "probe": probe}


def _ask(ctx_factory, paths, counts: dict[str, Any] | None = None, **extra):
    from tests.library_ask_fixtures import call

    ctx = ctx_factory(paths.root)
    try:
        ctx.require_vault()  # opening the vault syncs its state; the Ask is measured after it
        if counts is not None:
            counts["before"] = _evidence_counts(paths.sqlite_path)
        answer = call(ctx, "reader.ask", {"extractionId": "ext_text", "spanId": "t2",
                                          "question": "why is an eigenvalue a root?", **extra})
        if counts is not None:
            counts["after"] = _evidence_counts(paths.sqlite_path)
        return answer
    finally:
        ctx.close()


def _assembled(vault: Any, repository: Any, prior: Any):
    from learnloop.diagnosis.split.context import assemble_diagnosis_context
    from learnloop.diagnosis.split.history import VaultHistoryStore
    from learnloop.diagnosis.split.settings import DiagnosisSettings
    from tests.diagnosis_context_helpers import _current

    store = VaultHistoryStore(vault, repository)
    return assemble_diagnosis_context(vault, store, _current(vault, store), DiagnosisSettings(), mode="full",
                                      prior_analysis=prior)
