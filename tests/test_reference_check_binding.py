"""S1 (G19, D20): a key check verifies the content it checked, never a later edit."""
from __future__ import annotations

import time

import pytest

from learnloop.content.authoring import source_exercise_import as SEI
from learnloop.content.authoring.item_authoring import edit_item
from learnloop.db.stores.source_service import effective_key_status, import_row, key_checks_for_item
from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, call, loaded, service_clients


@pytest.fixture
def imported(tmp_path):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    result = SEI.import_source_exercise(paths.root, repository, extraction_id="ext_text",
                                       span_ids=[spans["exercises"][1]], caller="learner",
                                       clients=service_clients(FakeServiceLLM()))
    assert result["key_status"] == "book_solution"
    return paths, repository, result


def _status(paths, repository, item_id):
    item = loaded(paths).practice_items[item_id]
    with repository.connection() as connection:
        return effective_key_status(connection, item)


@pytest.mark.parametrize("change", [{"prompt": "Solve 3x + 5 = 20 for x."}, {"expected_answer": "6"}])
def test_an_edited_prompt_or_key_is_unverified_until_rechecked(imported, change):
    paths, repository, result = imported
    item_id = result["practice_item_id"]
    edit_item(paths.root, repository, practice_item_id=item_id, **change)
    assert _status(paths, repository, item_id) == "changed_since_check"
    report = SEI.verify_item_key(paths.root, repository, item_id, trigger="edit",
                                 clients=service_clients(FakeServiceLLM()))
    assert report["check_id"]
    status = _status(paths, repository, item_id)
    assert status != "changed_since_check"
    if "expected_answer" in change:  # the book says 5: the new key is disputed
        assert status == "disputed"


def test_a_hints_only_edit_keeps_the_verification(imported):
    paths, repository, result = imported
    edit_item(paths.root, repository, practice_item_id=result["practice_item_id"], hints=["A new hint."])
    assert _status(paths, repository, result["practice_item_id"]) == "book_solution"


def test_a_late_background_check_never_verifies_an_edit(tmp_path, monkeypatch):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    real = SEI.run_key_ladder
    release = {"go": False}

    def slow(*args, **kwargs):
        while not release["go"]:
            time.sleep(0.02)
        return real(*args, **kwargs)

    monkeypatch.setattr(SEI, "run_key_ladder", slow)
    result = SEI.import_source_exercise(paths.root, repository, extraction_id="ext_text",
                                       span_ids=[spans["exercises"][1]], caller="learner",
                                       clients=service_clients(FakeServiceLLM()), time_box_seconds=0.05)
    assert result["key_status"] == "checking"
    item_id = result["practice_item_id"]
    edit_item(paths.root, repository, practice_item_id=item_id, expected_answer="6")
    release["go"] = True
    deadline = time.time() + 20
    while time.time() < deadline:
        with repository.connection() as connection:
            if key_checks_for_item(connection, item_id):
                break
        time.sleep(0.05)
    time.sleep(0.2)
    with repository.connection() as connection:
        row = import_row(connection, result["import_id"])
        checks = key_checks_for_item(connection, item_id)
    assert checks and checks[0]["trigger"] == "background"
    assert row["reason"] == "superseded_by_edit"
    assert _status(paths, repository, item_id) == "changed_since_check"


def test_the_edit_rpc_queues_a_recheck(imported, monkeypatch):
    from learnloop.content.authoring import source_exercise_import as module

    paths, _repository, result = imported
    queued = []
    monkeypatch.setattr(module, "verify_item_key", lambda *a, **k: queued.append(k.get("trigger")) or {})
    response = call(paths.root, "edit_practice_item", {"practiceItemId": result["practice_item_id"],
                                                         "expectedAnswer": "6"})
    assert response["result"]["keyRecheck"] == "queued"
    deadline = time.time() + 5
    while not queued and time.time() < deadline:
        time.sleep(0.02)
    assert queued == ["edit"]
