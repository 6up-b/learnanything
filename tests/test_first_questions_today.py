"""First questions arrive, the screen half (UX audit P11, F20): the facts a book
card's status line carries so Today can offer a new learner's first questions,
or say truthfully what must happen first.

- while a book is being built: how far along it is, in the build's own windows
  and passes, and a typical duration only where this library measured one;
- after a build stopped: whether it already tried a failed step again on its own;
- once the learner finished sections: how many questions they gave and which
  sections, or that they are being written, stopped, or wait for a look;
- a build that ends, however it ends, bumps the revision every screen reads.

Every model call is a house fake.
"""

from __future__ import annotations

import pytest

from learnloop.ai.errors import AIInterrupted, AITurnTimeout
from learnloop.clock import utc_now_iso
from learnloop.content.pipeline.add_source import (
    build_progress,
    latest_auto_outcome,
    source_status_line,
)
from learnloop.content.pipeline.runner import retried_on_its_own
from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.ux_phase1_review_fixes_helpers import _add, _jobs
from tests.ux_phase1_support import CLOCK, FakeBookSynthesisClient, fake_services, fresh_library, grant_consent, write_book


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)


def _book(tmp_path, *, synthesis=None, name="probability_book.md", root=None, services=None):
    root = root or fresh_library(tmp_path)
    grant_consent(root)
    overrides = {"synthesis_client_factory": synthesis} if synthesis else {}
    repo, jobs = _jobs(root, services or fake_services(**overrides))
    item = _add(root, jobs, write_book(tmp_path, name))
    outcome = latest_auto_outcome(repo, item["source_id"])
    assert outcome["outcome"] == "building", outcome
    return root, repo, jobs, item, outcome["build_batch_id"]


def _line(root, repo, item):
    return source_status_line(repo, load_vault(root), item["source_id"])


def _set(repo, table, row_id, **fields):
    assignments = ", ".join(f"{name} = ?" for name in fields)
    with repo.connection() as connection:
        connection.execute(f"UPDATE {table} SET {assignments} WHERE id = ?", (*fields.values(), row_id))
        connection.commit()


def _as_running(repo, batch_id, *, synthesis_window=None):
    """The build caught part-way: its inventory done, its synthesis on its pass."""

    _set(repo, "ingest_batches", batch_id, status="running", finished_at=None)
    for job in repo.ingest_jobs_for_batch(batch_id):
        if job["job_type"] in {"bootstrap_synthesis", "append_synthesis"}:
            _set(repo, "ingest_jobs", job["id"], status="running", finished_at=None,
                 current_window=synthesis_window, total_windows=1 if synthesis_window else None)


class _FailingSynthesis(FakeBookSynthesisClient):
    def run_source_set_synthesis(self, context):
        raise AITurnTimeout("The model took too long.")


class _InterruptedSynthesis(FakeBookSynthesisClient):
    def run_source_set_synthesis(self, context):
        raise AIInterrupted("Stopped.")


# -- A1: how far a build is ---------------------------------------------------------


def _job(job_type, status, current=None, total=None):
    return {"job_type": job_type, "status": status, "current_window": current, "total_windows": total}


def test_build_progress_counts_the_builds_windows_and_passes():
    # A first document: one window, one pass. The synthesis's total is known
    # once it starts; until then it counts one step.
    assert build_progress([_job("inventory", "queued"), _job("bootstrap_synthesis", "queued")]) == {"done": 0, "total": 2}
    assert build_progress([_job("inventory", "running", 0, 1), _job("bootstrap_synthesis", "queued")]) == {"done": 0, "total": 2}
    assert build_progress([_job("inventory", "completed", 1, 1), _job("bootstrap_synthesis", "queued")]) == {"done": 1, "total": 2}
    # The synthesis reports the pass it is on, so a pass is done only after it.
    assert build_progress([_job("inventory", "completed", 1, 1), _job("bootstrap_synthesis", "running", 1, 1)]) == {"done": 1, "total": 2}
    # A larger book: windows across units, passes across shards.
    assert build_progress([_job("inventory", "running", 4, 6), _job("bootstrap_synthesis", "queued")]) == {"done": 4, "total": 7}
    assert build_progress([_job("inventory", "completed", 6, 6), _job("bootstrap_synthesis", "running", 3, 4)]) == {"done": 8, "total": 10}
    # Every window already kept: the inventory has no model step left.
    assert build_progress([_job("inventory", "completed", 0, 0), _job("append_synthesis", "running", 1, 1)]) == {"done": 0, "total": 1}
    # A stopped step leaves nothing under way to measure; other jobs are not steps.
    assert build_progress([_job("inventory", "failed", 0, 1), _job("bootstrap_synthesis", "blocked")]) is None
    assert build_progress([_job("import", "running")]) is None


def test_a_building_books_line_says_how_far_along_it_is(tmp_path):
    root, repo, _jobs_, item, batch_id = _book(tmp_path)
    _as_running(repo, batch_id, synthesis_window=1)

    line = _line(root, repo, item)

    assert line["tone"] == "working"
    assert line["text"] == "Writing questions for Ch. 1–2"  # the card's words are unchanged
    # Two chapters: two inventory windows kept, then the synthesis on its one pass.
    inventory = next(job for job in repo.ingest_jobs_for_batch(batch_id) if job["job_type"] == "inventory")
    assert (inventory["current_window"], inventory["total_windows"]) == (2, 2)
    assert line["progress"] == {"done": 2, "total": 3}
    # This library has finished no other build: no duration is claimed.
    assert "minutes" not in line


def test_the_duration_is_this_librarys_own_measured_one(tmp_path):
    root, repo, jobs, _first, _first_batch = _book(tmp_path)
    root, repo, _jobs_, item, batch_id = _book(tmp_path, name="second_book.md", root=root)
    _as_running(repo, batch_id)

    line = _line(root, repo, item)

    # The first build took no time on the frozen clock: under a minute, as the words say.
    assert line["text"] == "Questions for Ch. 1–2 in under a minute"
    assert line["minutes"] == 0.0


# -- A2: whether a stopped build already tried again on its own ----------------------


def _row(status="failed", code="AITurnTimeout", job_type="bootstrap_synthesis", auto=True, reuse=False):
    payload = {"auto_build": {"source_id": "src"}} if auto else {}
    if reuse:
        payload["reuse_candidate"] = True
    return {"job_type": job_type, "status": status, "payload": payload, "error": {"code": code}}


def test_retried_on_its_own_reads_the_retry_rule_back_from_the_stored_row():
    assert retried_on_its_own(_row()) is True
    assert retried_on_its_own(_row(code="InventoryValidationError", job_type="inventory")) is True
    assert retried_on_its_own(_row(code="budget_exceeded")) is True
    assert retried_on_its_own(_row(code="timeout")) is True
    # Not curable: no second try was made.
    assert retried_on_its_own(_row(code="AIInterrupted")) is False
    assert retried_on_its_own(_row(code="spend_paused")) is False
    assert retried_on_its_own(_row(code="cancelled", status="cancelled")) is False
    # Not an automatic build's model step.
    assert retried_on_its_own(_row(auto=False)) is False
    assert retried_on_its_own(_row(reuse=True)) is False
    assert retried_on_its_own(_row(job_type="import")) is False
    assert retried_on_its_own(_row(status="completed")) is False


def test_a_build_that_stopped_after_its_own_retry_says_so(tmp_path):
    root, repo, _jobs_, item, batch_id = _book(tmp_path, synthesis=lambda ctx=None: _FailingSynthesis())
    assert repo.get_ingest_batch(batch_id)["status"] == "failed"

    line = _line(root, repo, item)

    assert line["action"] == {"kind": "retry", "label": "Retry"}
    assert line["retried"] is True


def test_a_build_that_stopped_without_a_retry_says_so_too(tmp_path):
    root, repo, _jobs_, item, batch_id = _book(tmp_path, synthesis=lambda ctx=None: _InterruptedSynthesis())
    assert repo.get_ingest_batch(batch_id)["status"] == "failed"

    line = _line(root, repo, item)

    assert line["action"] == {"kind": "retry", "label": "Retry"}
    assert line["retried"] is False


# -- A3: the questions the learner's finished sections gave --------------------------


def _finish_section(repo, item, section_id):
    extraction_id = resolve_extraction_id(repo, item["source_id"])
    repo.upsert_reader_section_progress(extraction_id=extraction_id, section_id=section_id,
                                        spans_seen=3, span_count=3, completed=True, clock=CLOCK)
    batch_id = f"batch_section_{section_id}"
    repo.insert_ingest_batch(id=batch_id, workflow_type="practice_expansion", clock=CLOCK)
    repo.insert_ingest_job(id=f"ijob_section_{section_id}", batch_id=batch_id, ordinal=0,
                           job_type="practice_expansion", payload={"learning_object_ids": ["lo"]}, clock=CLOCK)
    repo.mark_section_generation(extraction_id=extraction_id, section_id=section_id, batch_id=batch_id, clock=CLOCK)
    return batch_id


def _section_ids(repo, item):
    extraction_id = resolve_extraction_id(repo, item["source_id"])
    with repo.connection() as connection:
        return [(row["unit_id"], row["label"]) for row in connection.execute(
            "SELECT unit_id, label FROM source_document_units WHERE extraction_id = ? ORDER BY ordinal",
            (extraction_id,)).fetchall()]


def _write_questions(root, repo, batch_id, *, applied: int, pending: int = 0):
    vault = load_vault(root)
    lo_id = sorted(vault.learning_objects)[0]
    now = utc_now_iso(CLOCK)
    items = []
    for index in range(applied + pending):
        item_id = f"pi_first_{batch_id[-2:]}_{index}"
        payload = {
            "id": item_id,
            "learning_object_id": lo_id,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "prompt": f"Question {index} from the section.",
            "expected_answer": "An answer.",
            "grading_rubric": {"max_points": 1, "criteria": [{"id": "c", "points": 1, "description": "Right."}],
                               "fatal_errors": []},
            "created_at": now,
            "updated_at": now,
        }
        accepted = index < applied
        if accepted:
            upsert_practice_item(root, payload, clock=CLOCK)
        items.append({"client_item_id": f"c{index}", "item_type": "practice_item", "operation": "create",
                      "payload": payload, "decision": "accepted" if accepted else "pending",
                      "applied_change_batch_id": "chg_1" if accepted else None, "created_at": now})
    with repo.connection() as connection:
        # The build's own run stands in for the section's (a proposal names the run that wrote it).
        run_id = connection.execute("SELECT agent_run_id FROM proposed_patches LIMIT 1").fetchone()[0]
    patch_id = repo.persist_proposal_batch({"agent_run_id": run_id, "purpose": "practice_expansion", "created_at": now}, items)
    job = repo.ingest_jobs_for_batch(batch_id)[0]
    assert repo.transition_unleased_ingest_job(job["id"], status="completed",
                                               result={"patch_id": patch_id, "generated": applied + pending})
    return [item["payload"]["id"] for item in items[:applied]]


def test_a_built_book_with_no_section_finished_says_none_came_yet(tmp_path):
    root, repo, _jobs_, item, _batch = _book(tmp_path)

    line = _line(root, repo, item)

    assert line["text"] == "Questions for Ch. 1–2 come up as you read"
    questions = line["questions"]
    assert questions == {"count": 0, "item_ids": [], "sections": [], "writing": [], "waiting": [], "failed": [],
                         "to_look_at": 0, "section_count": len(_section_ids(repo, item))}


def test_a_finished_sections_questions_are_named_while_written_and_once_written(tmp_path):
    root, repo, _jobs_, item, _batch = _book(tmp_path)
    (section_id, label), *_ = [(unit, label) for unit, label in _section_ids(repo, item) if label]
    batch_id = _finish_section(repo, item, section_id)

    writing = _line(root, repo, item)["questions"]
    assert writing["writing"] == [label]
    assert writing["count"] == 0

    item_ids = _write_questions(root, repo, batch_id, applied=2, pending=1)
    questions = _line(root, repo, item)["questions"]

    assert questions["count"] == 2
    assert questions["item_ids"] == item_ids
    assert questions["sections"] == [label]
    assert questions["writing"] == []
    assert questions["to_look_at"] == 1


def test_a_section_whose_writing_stopped_names_the_batch_to_resume(tmp_path):
    root, repo, _jobs_, item, _batch = _book(tmp_path)
    (section_id, label), *_ = [(unit, label) for unit, label in _section_ids(repo, item) if label]
    batch_id = _finish_section(repo, item, section_id)
    job = repo.ingest_jobs_for_batch(batch_id)[0]
    assert repo.transition_unleased_ingest_job(job["id"], status="failed", error={"code": "AITurnTimeout", "message": "late"})

    questions = _line(root, repo, item)["questions"]

    assert questions["failed"] == [{"label": label, "resume_id": batch_id}]
    assert questions["count"] == 0


def test_a_line_of_another_state_carries_questions_only_once_there_are_some(tmp_path):
    root, repo, _jobs_, item, batch_id = _book(tmp_path)
    _as_running(repo, batch_id, synthesis_window=1)
    assert "questions" not in _line(root, repo, item)

    (section_id, _label), *_ = [(unit, label) for unit, label in _section_ids(repo, item) if label]
    section_batch = _finish_section(repo, item, section_id)
    _write_questions(root, repo, section_batch, applied=1)

    assert _line(root, repo, item)["questions"]["count"] == 1


# -- A4: a build's end is a revision every screen reads ------------------------------


def test_a_build_that_stops_bumps_the_revision_the_shell_reads(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services(synthesis_client_factory=lambda ctx=None: _FailingSynthesis()))
    before = repo.queue_revision()["revision"]

    item = _add(root, jobs, write_book(tmp_path))

    batch = repo.get_ingest_batch(latest_auto_outcome(repo, item["source_id"])["build_batch_id"])
    assert batch["status"] == "failed"
    assert repo.queue_revision()["revision"] > before


def test_a_build_that_finishes_bumps_it_too(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services())
    before = repo.queue_revision()["revision"]

    item = _add(root, jobs, write_book(tmp_path))

    batch = repo.get_ingest_batch(latest_auto_outcome(repo, item["source_id"])["build_batch_id"])
    assert batch["status"] == "completed"
    assert repo.queue_revision()["revision"] > before
