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

import json

import pytest

from learnloop.ai.errors import AIInterrupted, AITurnTimeout
from learnloop.clock import FrozenClock, utc_now_iso
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
from tests.ux_phase1_support import BOOK_MARKDOWN, CLOCK, FakeBookSynthesisClient, fake_services, fresh_library, grant_consent, write_book


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)


def _book(tmp_path, *, synthesis=None, name="probability_book.md", root=None, services=None, text=BOOK_MARKDOWN):
    root = root or fresh_library(tmp_path)
    grant_consent(root)
    overrides = {"synthesis_client_factory": synthesis} if synthesis else {}
    repo, jobs = _jobs(root, services or fake_services(**overrides))
    item = _add(root, jobs, write_book(tmp_path, name, text))
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
    # Another book: the same bytes under another name are the first book again (UX-57).
    root, repo, _jobs_, item, batch_id = _book(tmp_path, name="second_book.md", root=root,
                                               text=BOOK_MARKDOWN + "\nA second book's own closing line.\n")
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
                         "to_look_at": 0, "section_count": len(_section_ids(repo, item)), "none_needed": []}


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
    _set_section_job(repo, section_batch, status="running", done=2, total=8)

    line = _line(root, repo, item)
    assert line["questions"]["count"] == 1
    assert line["questions"]["progress"] == {"done": 2, "total": 8}
    assert line["progress"] == {"done": 2, "total": 3}


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


@pytest.mark.parametrize(("status", "done"), [
    ("queued", 0), ("running", 0), ("running", 2), ("failed", 2), ("queued", 2), ("completed", 6),
])
def test_section_writing_progress_counts_saved_parts(tmp_path, status, done):
    root, repo, _jobs_, item, _batch = _book(tmp_path)
    (section_id, _label), *_ = _section_ids(repo, item)
    batch_id = _finish_section(repo, item, section_id)
    job = repo.ingest_jobs_for_batch(batch_id)[0]
    _set(repo, "ingest_jobs", job["id"], status=status, current_window=done,
         total_windows=6, payload_json=json.dumps({"learning_object_ids": [f"lo_{i}" for i in range(6)]}))
    line = _line(root, repo, item)
    if status in {"queued", "running"}:
        assert line["questions"]["progress"] == {"done": done, "total": 6}
        assert line["progress"] == {"done": done, "total": 6}
    else:
        assert "progress" not in line["questions"]
        assert "progress" not in line


@pytest.mark.parametrize("status,done,failed", [
    ("running", 1, False), ("running", 4, True), ("failed", 7, True), ("completed", 8, False),
])
def test_landed_parts_are_counted_while_writing_or_failed(tmp_path, status, done, failed):
    root, repo, _jobs_, item, _batch = _book(tmp_path)
    (section_id, label), *_ = [(unit, label) for unit, label in _section_ids(repo, item) if label]
    batch = _finish_section(repo, item, section_id)
    ids = _write_questions(root, repo, batch, applied=done)
    job = repo.ingest_jobs_for_batch(batch)[0]
    repo.update_ingest_job_payload(job["id"], {**job["payload"], "question_parts": [
        {"topic_id": "lo_one", "patch_id": job["result"]["patch_id"]},
        *([{"topic_id": "lo_five", "error": "invalid JSON"}] if failed else []),
    ]})
    _set(repo, "ingest_jobs", job["id"], status=status, current_window=done, total_windows=8)
    fact = _line(root, repo, item)["questions"]
    assert fact["item_ids"] == ids
    assert fact["count"] == done
    if status == "running":
        assert fact["progress"] == {"done": done, "total": 8}
    else:
        assert "progress" not in fact
    assert fact["sections"] == [label]
    assert fact["writing"] == ([label] if status == "running" else [])
    assert fact["failed"] == ([{"label": f"{label}: lo_five", "resume_id": batch}] if failed else [])


def _written_by_the_section_job(tmp_path, topics, **held):
    """A finished section of a built book whose questions the real section job writes, every one
    grounded and audited, those ``held`` names marked review_required; the facts are read while it
    writes (at each call after the first) and after."""

    from learnloop.content.pipeline.runner import RunnerServices
    from tests.section_question_parts_helpers import held_writer, topics_in
    from tests.ux_phase1_review_fixes_helpers import _drain

    root, repo, _jobs_, item, _batch = _book(tmp_path)
    lo_ids, facet = topics_in(root, "probability-book", "lo_diagonalize_symmetric", topics)
    writer = held_writer(facet=facet, **held)
    (section_id, label), *_ = [(unit, label) for unit, label in _section_ids(repo, item) if label]
    extraction_id = resolve_extraction_id(repo, item["source_id"])
    repo.upsert_reader_section_progress(extraction_id=extraction_id, section_id=section_id,
                                        spans_seen=3, span_count=3, completed=True, clock=CLOCK)
    _repo, jobs = _jobs(root, RunnerServices(synthesis_client_factory=lambda ctx: writer), hold=True)
    batch_id = jobs.enqueue_practice_expansion(learning_object_ids=lo_ids, source_refs=[],
                                               reason=f"reader_section_completed:{section_id}")
    repo.mark_section_generation(extraction_id=extraction_id, section_id=section_id, batch_id=batch_id, clock=CLOCK)
    seen = []
    writer.before = lambda: seen.append(_line(root, repo, item)["questions"]) if len(writer.calls) > 1 else None
    _drain(jobs)
    return root, repo, item, label, batch_id, seen


def test_a_topic_whose_questions_wait_for_a_look_is_finished_not_failed(tmp_path):
    root, repo, item, label, batch_id, seen = _written_by_the_section_job(tmp_path, 3)

    # While the second and third topics are written, the first counts as finished.
    assert [fact["progress"] for fact in seen] == [{"done": 1, "total": 3}, {"done": 2, "total": 3}]
    assert [fact["failed"] for fact in seen] == [[], []]
    assert [fact["to_look_at"] for fact in seen] == [3, 6]
    job = repo.ingest_jobs_for_batch(batch_id)[0]
    assert job["status"] == "completed", job["error"]
    fact = _line(root, repo, item)["questions"]
    assert fact["failed"] == []
    assert fact["writing"] == []
    assert fact["to_look_at"] == 9
    assert fact["count"] == 0
    assert "progress" not in fact


def test_two_questions_applied_and_one_to_look_at(tmp_path):
    root, repo, item, label, batch_id, _seen = _written_by_the_section_job(tmp_path, 1, held=(2,))

    assert repo.ingest_jobs_for_batch(batch_id)[0]["status"] == "completed"
    fact = _line(root, repo, item)["questions"]
    assert (fact["count"], fact["to_look_at"], fact["failed"]) == (2, 1, [])
    assert fact["sections"] == [label]


def _set_section_job(repo, batch_id, *, status, done, total):
    job = repo.ingest_jobs_for_batch(batch_id)[0]
    _set(repo, "ingest_jobs", job["id"], status=status, current_window=done,
         total_windows=total, payload_json=json.dumps({"learning_object_ids": [f"lo_{i}" for i in range(total)]}))


def test_finished_empty_section_does_not_dilute_the_section_being_written(tmp_path):
    root, repo, _jobs_, item, _batch = _book(tmp_path)
    first, second = _section_ids(repo, item)[:2]
    empty = _finish_section(repo, item, first[0])
    writing = _finish_section(repo, item, second[0])
    _set_section_job(repo, empty, status="completed", done=0, total=3)
    _set_section_job(repo, writing, status="running", done=2, total=8)

    fact = _line(root, repo, item)["questions"]
    assert fact["writing"] == [second[1]]
    assert fact["progress"] == {"done": 2, "total": 8}


def test_two_sections_being_written_contribute_their_combined_parts(tmp_path):
    root, repo, _jobs_, item, _batch = _book(tmp_path)
    first, second, third = _section_ids(repo, item)[:3]
    one = _finish_section(repo, item, first[0])
    two = _finish_section(repo, item, second[0])
    finished = _finish_section(repo, item, third[0])
    _set_section_job(repo, one, status="running", done=2, total=8)
    _set_section_job(repo, two, status="queued", done=1, total=3)
    _set_section_job(repo, finished, status="completed", done=0, total=4)

    fact = _line(root, repo, item)["questions"]
    assert fact["writing"] == [first[1], second[1]]
    assert fact["progress"] == {"done": 3, "total": 11}


def test_completed_empty_job_leaves_no_unfinished_progress(tmp_path):
    root, repo, _jobs_, item, _batch = _book(tmp_path)
    section_id, _label = _section_ids(repo, item)[0]
    batch = _finish_section(repo, item, section_id)
    _set_section_job(repo, batch, status="completed", done=0, total=3)

    fact = _line(root, repo, item)["questions"]
    assert fact["writing"] == []
    assert "progress" not in fact


def test_chapters_found_does_not_borrow_question_progress(tmp_path, monkeypatch):
    from learnloop.content.pipeline import add_source

    root, repo, _jobs_, item, _batch = _book(tmp_path)
    section_id, _label = _section_ids(repo, item)[0]
    batch = _finish_section(repo, item, section_id)
    _set_section_job(repo, batch, status="running", done=2, total=8)
    monkeypatch.setattr(add_source, "latest_planner", lambda _repo, _source_id: ({"status": "running"}, None))

    line = _line(root, repo, item)
    assert line["text"] == "Chapters found"
    assert line["questions"]["progress"] == {"done": 2, "total": 8}
    assert "progress" not in line


# -- UX-44: which of a book's questions can be asked now ---------------------------------------------------------------


def _answer(root, repo, item_id, *, clock=None):
    """One right, self-graded answer (no model), as the learner's own; ``clock`` None is now."""

    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt

    complete_self_graded_attempt(
        load_vault(root), repo,
        AttemptDraft(practice_item_id=item_id, learner_answer_md="An answer.", attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"c": 1}, confidence=4, fatal_errors=[]),
        clock=clock,
    )


def _keep_for_a_later_check(repo, item_id, not_before, *, clock=None):
    """The question a certified topic keeps for its check on your own, as the certification step reserves it."""

    return repo.create_followup_task(kind="certification_cold_probe", case_kind="certification", case_ref="cert_first",
                                     not_before=not_before, selected_item_id=item_id, clock=clock)


def _the_walk(tmp_path, *, clock=None):
    """The measured sequence: a section's first three questions applied, two answered, the third kept for a later
    check (two weeks on), then six more applied from a second finished section."""

    from datetime import timedelta

    from learnloop.clock import SystemClock

    root, repo, _jobs_, item, _batch = _book(tmp_path)
    first, second = _section_ids(repo, item)[:2]
    one, two, three = _write_questions(root, repo, _finish_section(repo, item, first[0]), applied=3)
    _answer(root, repo, one, clock=clock)
    _answer(root, repo, two, clock=clock)
    now = (clock or SystemClock()).now()
    _keep_for_a_later_check(repo, three, utc_now_iso(FrozenClock(now + timedelta(days=14))), clock=clock)
    newer = _write_questions(root, repo, _finish_section(repo, item, second[0]), applied=6)
    return root, repo, item, (one, two, three), newer


def test_answered_and_reserved_questions_are_named_as_not_askable_now(tmp_path):
    from datetime import timedelta

    from learnloop.content.pipeline.add_source import reading_questions

    root, repo, item, (one, two, three), newer = _the_walk(tmp_path, clock=CLOCK)
    soon = FrozenClock(CLOCK.now() + timedelta(minutes=5))

    fact = reading_questions(repo, load_vault(root), item["source_id"], clock=soon)

    # Written ever: all nine, as before.
    assert fact["count"] == 9
    assert fact["item_ids"] == [one, two, three, *newer]
    # Not askable now: the two answered (not due again yet) and the one kept for the later check.
    assert fact["later_item_ids"] == [one, two, three]


def test_questions_come_back_into_the_askable_set_once_due(tmp_path):
    from datetime import timedelta

    from learnloop.content.pipeline.add_source import reading_questions

    root, repo, item, _first_three, _newer = _the_walk(tmp_path, clock=CLOCK)
    # A month on, both answers are due again and the check's day has come: nothing is held back.
    month = FrozenClock(CLOCK.now() + timedelta(days=30))

    fact = reading_questions(repo, load_vault(root), item["source_id"], clock=month)

    assert "later_item_ids" not in fact
    assert fact["count"] == 9


def test_the_book_card_line_carries_them_now(tmp_path):
    root, repo, item, (one, two, three), _newer = _the_walk(tmp_path)

    questions = _line(root, repo, item)["questions"]

    assert questions["later_item_ids"] == [one, two, three]
    assert questions["count"] == 9


def test_nothing_answered_or_kept_says_nothing_new(tmp_path):
    root, repo, _jobs_, item, _batch = _book(tmp_path)
    (section_id, _label), *_ = _section_ids(repo, item)
    _write_questions(root, repo, _finish_section(repo, item, section_id), applied=3)

    assert "later_item_ids" not in _line(root, repo, item)["questions"]
