"""S1: importing a picked textbook exercise: the book's solution, authoring, the ladder, the write."""
from __future__ import annotations

import json
import time

import pytest

from learnloop.content.authoring import pf_sandbox
from learnloop.content.authoring import source_exercise_import as SEI
from learnloop.db.stores.source_service import effective_key_status, import_row, key_checks_for_item
from learnloop.vault.hashes import practice_item_hash, reference_content_hash
from tests.source_service_fakes import (
    FakeServiceLLM, build_textbook_vault, loaded, service_clients, set_config,
)

needs_bwrap = pytest.mark.skipif(not pf_sandbox.sandbox_available(), reason="bubblewrap is not installed")


@pytest.fixture
def textbook(tmp_path):
    return build_textbook_vault(tmp_path / "vault")


def _import(paths, repository, span, llm, **kwargs):
    return SEI.import_source_exercise(paths.root, repository, extraction_id="ext_text", span_ids=[span],
                                      caller=kwargs.pop("caller", "learner"), clients=service_clients(llm), **kwargs)


def test_the_books_solution_writes_and_verifies_the_key(textbook):
    paths, repository, spans = textbook
    span = spans["exercises"][1]  # exercise 1
    result = _import(paths, repository, span, FakeServiceLLM(), label="Exercise 1")
    assert result["status"] == "written" and result["key_status"] == "book_solution"
    vault = loaded(paths)
    item = vault.practice_items[result["practice_item_id"]]
    # The stem stays verbatim; the item points at its canonical exercise.
    assert item.prompt.startswith("1. An eigenvalue t satisfies")
    assert item.canonical_exercise.extraction_id == "ext_text"
    assert item.canonical_exercise.span_ids == [span] and item.canonical_exercise.relation == "verbatim"
    assert item.expected_answer == "5"
    with repository.connection() as connection:
        row = import_row(connection, result["import_id"])
        checks = key_checks_for_item(connection, item.id)
        assert effective_key_status(connection, item) == "book_solution"
    assert row["status"] == "written" and row["content_hash"] == reference_content_hash(item)
    assert row["verification"]["solution_search"]["status"] == "found"
    assert [check["key_status"] for check in checks] == ["book_solution"]
    assert checks[0]["content_hash"] == reference_content_hash(item) and checks[0]["trigger"] == "import"
    with repository.connection() as connection:
        events = connection.execute("SELECT payload_json FROM interaction_events WHERE kind='learner_item_authored'"
                                    " AND subject_id=?", (item.id,)).fetchall()
    assert json.loads(events[0][0])["mechanism"] == "source_exercise_import"


def test_a_prose_exercise_without_a_solution_is_checked_by_the_panel(textbook):
    paths, repository, spans = textbook
    llm = FakeServiceLLM(panel_answers={"determinant changes sign": "the determinant is multiplied by -1"})
    result = _import(paths, repository, spans["exercises"][3], llm)
    assert result["status"] == "written" and result["key_status"] == "panel_agrees"


def test_an_unverified_key_is_written_labelled_or_refused_by_the_switch(textbook, monkeypatch):
    paths, repository, spans = textbook
    monkeypatch.setattr(pf_sandbox, "_sandbox_bwrap_path", lambda: None)
    llm = FakeServiceLLM(drop_cited_quote=True)
    written = _import(paths, repository, spans["exercises"][2], llm)  # exercise 2, numeric, no quote
    assert written["status"] == "written" and written["key_status"] == "panel_agrees_unconfirmed"
    set_config(paths, "source_service", unverified_imports=False)
    refused = _import(paths, repository, spans["exercises"][4], llm)  # exercise 4: "2 and 3" via quote dropped
    assert refused["status"] == "rejected" and refused["practice_item_id"] is None
    assert "couldn't check this answer key" in refused["reason"]


def test_a_need_is_never_fulfilled_by_an_unverified_key(textbook, monkeypatch):
    paths, repository, spans = textbook
    monkeypatch.setattr(pf_sandbox, "_sandbox_bwrap_path", lambda: None)
    result = _import(paths, repository, spans["exercises"][2], FakeServiceLLM(drop_cited_quote=True), caller="need")
    assert result["status"] == "rejected" and "verified key" in result["reason"]


def test_verification_off_imports_as_today_labelled_model_answer(textbook):
    paths, repository, spans = textbook
    set_config(paths, "source_service", exercise_verification=False)
    llm = FakeServiceLLM()
    result = _import(paths, repository, spans["exercises"][1], llm)
    assert result["status"] == "written" and result["key_status"] == "model_answer"
    assert [name for _purpose, name in llm.calls] == ["ExerciseAuthoring"]  # no ladder calls
    item = loaded(paths).practice_items[result["practice_item_id"]]
    with repository.connection() as connection:
        assert effective_key_status(connection, item) == "model_answer"


def test_the_time_box_writes_checking_and_the_check_lands_later(textbook, monkeypatch):
    paths, repository, spans = textbook
    llm = FakeServiceLLM()
    real = SEI.run_key_ladder

    def slow(*args, **kwargs):
        time.sleep(1.0)
        return real(*args, **kwargs)

    monkeypatch.setattr(SEI, "run_key_ladder", slow)
    result = _import(paths, repository, spans["exercises"][1], llm, time_box_seconds=0.05)
    assert result["status"] == "written" and result["key_status"] == "checking"
    item = loaded(paths).practice_items[result["practice_item_id"]]
    with repository.connection() as connection:
        assert effective_key_status(connection, item) in ("checking", "book_solution")
    deadline = time.time() + 20
    while time.time() < deadline:
        with repository.connection() as connection:
            if key_checks_for_item(connection, item.id):
                break
        time.sleep(0.1)
    with repository.connection() as connection:
        checks = key_checks_for_item(connection, item.id)
        assert checks and checks[0]["trigger"] == "background"
        # The time box also bounded rung 1's search, so the panel may have decided.
        assert effective_key_status(connection, item) in ("book_solution", "checked", "panel_agrees_unconfirmed")


def test_a_duplicate_exercise_is_rejected_as_already_in_practice(textbook):
    paths, repository, spans = textbook
    llm = FakeServiceLLM()
    first = _import(paths, repository, spans["exercises"][1], llm)
    second = _import(paths, repository, spans["exercises"][1], llm)
    assert second["status"] == "rejected" and second["reason"] == "already in your practice"
    assert first["practice_item_id"]


def test_items_without_a_canonical_exercise_serialize_byte_identically(textbook):
    paths, _repository, _spans = textbook
    vault = loaded(paths)
    item = vault.practice_items["pi_eigen_1"]
    assert "canonical_exercise" not in item.model_dump(mode="json")
    assert practice_item_hash(item) == practice_item_hash(item.model_copy(update={"canonical_exercise": None}))


def test_a_model_failure_while_authoring_fails_the_import_and_is_receipted(textbook):
    paths, repository, spans = textbook
    result = _import(paths, repository, spans["exercises"][1], FakeServiceLLM(fail_purposes={"ExerciseAuthoring"}))
    assert result["status"] == "failed" and "authoring failed" in result["reason"]
    with repository.connection() as connection:
        assert import_row(connection, result["import_id"])["status"] == "failed"  # never left "authoring"
    written = _import(paths, repository, spans["exercises"][1], FakeServiceLLM(), label="Exercise 1")
    with repository.connection() as connection:
        purposes = {row[0] for row in connection.execute(
            "SELECT purpose FROM model_call_receipts WHERE owner_kind='source_exercise_import' AND owner_id=?",
            (written["import_id"],))}
    assert "exercise_authoring" in purposes or "authoring" in purposes, purposes
