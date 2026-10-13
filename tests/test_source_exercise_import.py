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


# -- Codex sources-build review F5: process death around both commit boundaries -------------------


class _ProcessDeath(BaseException):
    """Stands for the process exiting: nothing after it runs, nothing catches it."""


def _row(repository, import_id):
    with repository.connection() as connection:
        return import_row(connection, import_id)


def _checks(repository, item_id):
    with repository.connection() as connection:
        return key_checks_for_item(connection, item_id)


@pytest.mark.parametrize("boundary", ["after_vault_write", "inside_written_commit"])
def test_a_process_death_around_the_written_commit_never_loses_the_check(textbook, monkeypatch, boundary):
    paths, repository, spans = textbook
    llm = FakeServiceLLM()
    real = {"commit": SEI._commit_written, "insert": SEI._insert_check}
    if boundary == "after_vault_write":
        def die(*_args, **_kwargs):
            raise _ProcessDeath()

        monkeypatch.setattr(SEI, "_commit_written", die)
    else:
        def die_inserting(*_args, **_kwargs):
            raise _ProcessDeath()

        monkeypatch.setattr(SEI, "_insert_check", die_inserting)
    import_id = "sei_crash"
    with pytest.raises(_ProcessDeath):
        _import(paths, repository, spans["exercises"][1], llm, import_id=import_id)
    row = _row(repository, import_id)
    # Nothing committed "written" without its check: the write-ahead row names
    # the item and keeps the ladder's result.
    assert row["status"] == "checking" and row["practice_item_id"] and row["verification"]["ladder_result"]
    assert _checks(repository, row["practice_item_id"]) == []
    monkeypatch.setattr(SEI, "_commit_written", real["commit"])
    monkeypatch.setattr(SEI, "_insert_check", real["insert"])
    calls = len(llm.calls)
    # The job retried after the restart completes from durable state, with no model call.
    retried = _import(paths, repository, spans["exercises"][1], llm, import_id=import_id)
    assert retried["resumed"] and retried["status"] == "written" and len(llm.calls) == calls
    row = _row(repository, import_id)
    [check] = _checks(repository, row["practice_item_id"])
    assert check["content_hash"] == row["content_hash"] and check["key_status"] == row["key_status"]
    assert check["trigger"] == "import"


def test_a_retried_written_import_restores_a_missing_check(textbook, monkeypatch):
    """The old commit order: ``written`` committed, then the process died
    before the check row. Retrying used to return at once and never restore it."""

    paths, repository, spans = textbook
    llm = FakeServiceLLM()

    def old_commit(repository, import_id, item, *, clock):
        with repository.connection() as connection:
            SEI.update_import(connection, import_id, updated_at="2026-10-12T00:00:00Z", status="written",
                              practice_item_id=item.id, content_hash=reference_content_hash(item))
        raise _ProcessDeath()

    real = SEI._commit_written
    monkeypatch.setattr(SEI, "_commit_written", old_commit)
    with pytest.raises(_ProcessDeath):
        _import(paths, repository, spans["exercises"][1], llm, import_id="sei_old")
    row = _row(repository, "sei_old")
    assert row["status"] == "written" and _checks(repository, row["practice_item_id"]) == []
    monkeypatch.setattr(SEI, "_commit_written", real)
    assert SEI.pending_import_checks(repository) == ["sei_old"]
    retried = _import(paths, repository, spans["exercises"][1], llm, import_id="sei_old")
    assert retried["recovery"] == "restored_check"
    assert len(_checks(repository, row["practice_item_id"])) == 1
    assert SEI.pending_import_checks(repository) == []


def _kill_background_check(monkeypatch):
    """A ladder that outlives the time box, in a process that dies before
    anything records its result (the thread's completion never runs)."""

    import threading

    released = threading.Event()

    def outlives(*_args, **_kwargs):
        released.wait(20)
        return SEI.LadderResult("model_answer", "skipped", skip_reason="the process died")

    monkeypatch.setattr(SEI, "run_key_ladder", outlives)
    monkeypatch.setattr(SEI, "_finish_pending", lambda *_args, **_kwargs: None)
    return released


def test_a_background_check_lost_with_its_process_is_resumed_at_startup(textbook, monkeypatch):
    paths, repository, spans = textbook
    llm = FakeServiceLLM()
    real_ladder, real_finish = SEI.run_key_ladder, SEI._finish_pending
    released = _kill_background_check(monkeypatch)
    result = _import(paths, repository, spans["exercises"][1], llm, time_box_seconds=0.05)
    assert result["key_status"] == "checking"
    released.set()
    row = _row(repository, result["import_id"])
    assert row["status"] == "written" and row["verification"]["pending_check"]["trigger"] == "background"
    # This process's own pending check is never taken over.
    assert SEI.pending_import_checks(repository) == []
    # A new process starts: another token, the real ladder. A different token
    # alone is not a dead process: the old lease must have lapsed (F9).
    monkeypatch.setattr(SEI, "PROCESS_TOKEN", "proc_next")
    monkeypatch.setattr(SEI, "run_key_ladder", real_ladder)
    monkeypatch.setattr(SEI, "_finish_pending", real_finish)
    assert SEI.pending_import_checks(repository) == []
    assert SEI.pending_import_checks(repository, include_held=True) == [result["import_id"]]
    _later_lease_clock(monkeypatch)
    assert SEI.pending_import_checks(repository) == [result["import_id"]]
    report = SEI.recover_import_checks(paths.root, repository, clients=service_clients(llm))
    assert report["actions"] == {"resumed_check": 1}
    row = _row(repository, result["import_id"])
    [check] = _checks(repository, result["practice_item_id"])
    assert check["trigger"] == "background" and check["content_hash"] == row["content_hash"]
    assert "pending_check" not in row["verification"] and row["key_status"] == check["key_status"]
    assert row["verification"]["background_check_id"] == check["id"]
    assert SEI.pending_import_checks(repository) == []


def test_a_resumed_check_never_verifies_content_edited_since(textbook, monkeypatch):
    from learnloop.content.authoring.item_authoring import edit_item

    paths, repository, spans = textbook
    llm = FakeServiceLLM()
    released = _kill_background_check(monkeypatch)
    result = _import(paths, repository, spans["exercises"][1], llm, time_box_seconds=0.05)
    released.set()
    edit_item(paths.root, repository, practice_item_id=result["practice_item_id"], expected_answer="6")
    monkeypatch.setattr(SEI, "PROCESS_TOKEN", "proc_next")
    _later_lease_clock(monkeypatch)
    calls = len(llm.calls)
    report = SEI.recover_import_checks(paths.root, repository, clients=service_clients(llm))
    assert report["actions"] == {"superseded_by_edit": 1} and len(llm.calls) == calls
    row = _row(repository, result["import_id"])
    assert row["reason"] == "superseded_by_edit" and _checks(repository, result["practice_item_id"]) == []
    item = loaded(paths).practice_items[result["practice_item_id"]]
    with repository.connection() as connection:
        assert effective_key_status(connection, item) == "model_answer"


def test_a_reader_imports_background_check_is_durable_too(textbook, monkeypatch):
    paths, repository, spans = textbook
    llm = FakeServiceLLM()
    result = _import(paths, repository, spans["exercises"][2], llm, caller="reader")
    item_id = result["practice_item_id"]
    rows = SEI.record_reader_import(paths.root, repository, {"items": [{"practice_item_id": item_id}]},
                                    extraction_id="ext_text", span_ids=[spans["exercises"][2]], source_id="src_text",
                                    revision_id="rev_text", pending_check=True)
    assert "pending_check" in _row(repository, rows[0]["import_id"])["verification"]
    monkeypatch.setattr(SEI, "PROCESS_TOKEN", "proc_next")  # its thread died with the old process
    report = SEI.recover_import_checks(paths.root, repository, clients=service_clients(llm))
    assert report["actions"].get("resumed_check") == 1
    assert "pending_check" not in _row(repository, rows[0]["import_id"])["verification"]


def test_the_sidecar_resumes_pending_checks_at_startup(textbook, monkeypatch):
    import threading

    from learnloop_sidecar.context import SidecarContext

    paths, repository, _spans = textbook
    seen: list[str] = []
    done = threading.Event()
    monkeypatch.setattr(SEI, "pending_import_checks", lambda _repository, **_kwargs: ["sei_dead"])

    def recover(root, _repository, **_kwargs):
        seen.append(str(root))
        done.set()
        return {"imports": 1, "actions": {}}

    monkeypatch.setattr(SEI, "recover_import_checks", recover)
    context = SidecarContext()
    context.load(paths.root)
    assert done.wait(10) and seen == [str(paths.root)]


@pytest.mark.parametrize("recovery", ["job_retry", "startup"])
def test_recovery_never_binds_a_verdict_to_content_edited_before_the_commit(textbook, monkeypatch, recovery):
    """Codex re-review F1: the ladder verified the draft, the item was written,
    the process died before ``_commit_written``, and the item was edited before
    recovery. The persisted verdict belongs to the draft's content only."""

    from learnloop.content.authoring.item_authoring import edit_item

    paths, repository, spans = textbook
    llm = FakeServiceLLM()
    real = SEI._commit_written

    def die(*_args, **_kwargs):
        raise _ProcessDeath()

    monkeypatch.setattr(SEI, "_commit_written", die)
    import_id = "sei_edit_before_commit"
    with pytest.raises(_ProcessDeath):
        _import(paths, repository, spans["exercises"][1], llm, import_id=import_id)
    monkeypatch.setattr(SEI, "_commit_written", real)
    row = _row(repository, import_id)
    item_id = row["practice_item_id"]
    checked_hash = reference_content_hash(loaded(paths).practice_items[item_id])
    assert row["verification"]["ladder_result"]["key_status"] == "book_solution"
    # The write-ahead record names the content the verdict is for.
    assert row["verification"]["ladder_result"]["content_hash"] == checked_hash
    edit_item(paths.root, repository, practice_item_id=item_id, expected_answer="6")
    calls = len(llm.calls)
    if recovery == "job_retry":
        _import(paths, repository, spans["exercises"][1], llm, import_id=import_id)
    else:
        SEI.recover_import_checks(paths.root, repository, clients=service_clients(llm))
    assert len(llm.calls) == calls  # recovery makes no model call
    edited = loaded(paths).practice_items[item_id]
    with repository.connection() as connection:
        # The unchecked "6" is never verified by the draft's verdict.
        assert effective_key_status(connection, edited) not in ("book_solution", "checked", "panel_agrees")
    row = _row(repository, import_id)
    assert row["status"] == "written" and row["reason"] == "superseded_by_edit"
    assert row["content_hash"] == checked_hash
    # The verdict stays bound to the content it checked, and only to it.
    assert [check["content_hash"] for check in _checks(repository, item_id)] == [checked_hash]


def _later_lease_clock(monkeypatch, hours=1):
    """Leases are wall-clock process liveness: move their clock past every lease."""

    from datetime import UTC, datetime, timedelta

    later = (datetime.now(UTC) + timedelta(hours=hours)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    monkeypatch.setattr(SEI, "_lease_now", lambda: later, raising=False)


def test_a_live_check_in_another_process_is_never_taken_over(textbook, monkeypatch):
    """Codex re-review F9: one sidecar is still checking an import when another
    process opens the vault. A different process token is not a dead process."""

    paths, repository, spans = textbook
    llm = FakeServiceLLM()
    real_ladder = SEI.run_key_ladder
    released = _kill_background_check(monkeypatch)
    result = _import(paths, repository, spans["exercises"][1], llm, time_box_seconds=0.05)
    try:
        # Another process (another token, the real ladder) opens the vault
        # while process A's check is still running.
        monkeypatch.setattr(SEI, "PROCESS_TOKEN", "proc_other")
        monkeypatch.setattr(SEI, "run_key_ladder", real_ladder)
        calls = len(llm.calls)
        report = SEI.recover_import_checks(paths.root, repository, clients=service_clients(llm))
        assert len(llm.calls) == calls, report
        assert _checks(repository, result["practice_item_id"]) == []
        assert "pending_check" in _row(repository, result["import_id"])["verification"]
    finally:
        released.set()


def test_overlapping_recoveries_run_one_check(textbook, monkeypatch):
    """Codex re-review F9: a recovery that runs while another recovery of the
    same import is still checking never launches a second ladder."""

    import threading

    paths, repository, spans = textbook
    llm = FakeServiceLLM()
    real_ladder, real_finish = SEI.run_key_ladder, SEI._finish_pending
    released = _kill_background_check(monkeypatch)
    result = _import(paths, repository, spans["exercises"][1], llm, time_box_seconds=0.05)
    released.set()
    for thread in threading.enumerate():
        if thread.name == "source-key-ladder":
            thread.join(20)  # the dead process's thread is gone before the next one starts
    # A new process; the dead process's lease (if any) has long expired.
    monkeypatch.setattr(SEI, "PROCESS_TOKEN", "proc_next")
    monkeypatch.setattr(SEI, "_finish_pending", real_finish)
    _later_lease_clock(monkeypatch)
    entered, gate, runs = threading.Event(), threading.Event(), []

    def slow_ladder(*args, **kwargs):
        runs.append(1)
        entered.set()
        gate.wait(20)
        return real_ladder(*args, **kwargs)

    monkeypatch.setattr(SEI, "run_key_ladder", slow_ladder)
    first = threading.Thread(target=SEI.recover_import_checks, args=(paths.root, repository),
                             kwargs={"clients": service_clients(llm)})
    first.start()
    assert entered.wait(20)
    second = SEI.recover_import_checks(paths.root, repository, clients=service_clients(llm))
    gate.set()
    first.join(30)
    assert len(runs) == 1, second
    assert len(_checks(repository, result["practice_item_id"])) == 1
    assert "pending_check" not in _row(repository, result["import_id"])["verification"]


def test_a_late_check_whose_lease_was_taken_over_records_nothing(textbook, monkeypatch):
    """Codex re-review F9: a check whose lease expired (its process hung) and
    was re-claimed by recovery is fenced out: one check row, the recovery's."""

    import threading

    paths, repository, spans = textbook
    llm = FakeServiceLLM()
    real_ladder = SEI.run_key_ladder
    monkeypatch.setattr(SEI, "CHECK_HEARTBEAT_SECONDS", 3600, raising=False)  # the hung process stops renewing
    hung, gate = threading.Event(), threading.Event()

    def hangs(*args, **kwargs):
        hung.set()
        gate.wait(20)
        return real_ladder(*args, **kwargs)

    monkeypatch.setattr(SEI, "run_key_ladder", hangs)
    result = _import(paths, repository, spans["exercises"][1], llm, time_box_seconds=0.05)
    assert hung.wait(20) and result["key_status"] == "checking"
    # Much later, another process recovers it (the hung lease has expired).
    monkeypatch.setattr(SEI, "PROCESS_TOKEN", "proc_next")
    monkeypatch.setattr(SEI, "run_key_ladder", real_ladder)
    _later_lease_clock(monkeypatch)
    report = SEI.recover_import_checks(paths.root, repository, clients=service_clients(llm))
    assert report["actions"] == {"resumed_check": 1}
    # The hung check wakes up and finishes: fenced out.
    gate.set()
    deadline = time.time() + 20
    while time.time() < deadline and len(_checks(repository, result["practice_item_id"])) < 2:
        time.sleep(0.2)
        if not any(thread.name == "source-key-ladder" and thread.is_alive() for thread in threading.enumerate()):
            break
    assert len(_checks(repository, result["practice_item_id"])) == 1
