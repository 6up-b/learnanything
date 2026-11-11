"""What other test files use from ``tests/test_reference_gate_imports.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from contextlib import closing

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.content.authoring import source_exercise_import as SEI
from learnloop.db.connection import connect
from learnloop.db.stores.source_service import reference_status_for_item

from tests.source_service_fakes import FakeServiceLLM, loaded, service_clients


def _attempt(paths, repository, item_id, *, points=2, criterion="answer"):
    vault = loaded(paths)
    return complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=item_id, learner_answer_md="x = 5", attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={criterion: points}, fatal_errors=[], confidence=3),
    )


def _status(repository, attempt_id):
    with repository.connection() as connection:
        return connection.execute("SELECT reference_status FROM practice_attempts WHERE id=?",
                                  (attempt_id,)).fetchone()[0]


def _regrade(paths, repository, attempt_id):
    from learnloop.attempts.regrade import regrade_attempt
    from tests.diagnosis_fakes import ReviewFakeClient
    from tests.split_live_helpers import ReadyRuntime

    regrade_attempt(loaded(paths), repository, repository.fetch_practice_attempt(attempt_id),
                    runtime=ReadyRuntime(), client=ReviewFakeClient(), grading_source="ai", clock=None)


def _bindings(repository, attempt_id):
    from learnloop.db.stores.source_service import REFERENCE_BINDING_TASK

    with closing(connect(repository.sqlite_path)) as connection:
        connection.row_factory = __import__("sqlite3").Row
        return [dict(row) for row in connection.execute(
            "SELECT * FROM judgment_ledger WHERE task=? AND left_id=? ORDER BY created_at, id",
            (REFERENCE_BINDING_TASK, attempt_id))]


def _verified_import(paths, repository, spans):
    result = SEI.import_source_exercise(
        paths.root, repository, extraction_id="ext_text", span_ids=[spans["exercises"][1]], caller="learner",
        clients=service_clients(FakeServiceLLM()))
    assert result["key_status"] == "book_solution"
    return result["practice_item_id"]


def _edit_key(paths, repository, item_id):
    from learnloop.content.authoring.item_authoring import edit_item

    edit_item(paths.root, repository, practice_item_id=item_id, expected_answer="x = 6", reason="test edit")
    with closing(connect(repository.sqlite_path)) as connection:
        assert reference_status_for_item(connection, loaded(paths).practice_items[item_id]) == "unverified"
