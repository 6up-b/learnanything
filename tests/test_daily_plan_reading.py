"""Daily-loop DL1 §6.10: reading blocks (as-you-read, no pre-questions in DL1).

The words-left estimate; a partial block when the section exceeds the minutes
left; each ``block_ended`` outcome advancing the plan and consuming the
estimate; ``reading_progress`` events from ``reader.mark_section_progress``;
resuming an interrupted block; the next day continuing the same section;
``next_plan_item`` returning a typed reading step.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

import learnloop.clock as clock_module
import learnloop_sidecar.handlers  # noqa: F401
from learnloop.clock import FrozenClock
from learnloop.content.sources.source_library import register_source_revision
from learnloop.daily_plan.reading import as_you_read_extraction_ids, next_reading_target
from learnloop.db.repositories import Repository
from learnloop.ingest.extractors.normalizers import markdown_to_ir
from learnloop.ingest.hashing import extraction_request_hash, extraction_result_hash
from learnloop.ingest.ir import IR_SCHEMA_VERSION
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.helpers import create_daily_plan_vault

DAY1 = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
_SECTION_ONE = " ".join(f"word{i}" for i in range(1200))  # 10 minutes at 120 wpm
_SECTION_TWO = " ".join(f"term{i}" for i in range(3000))  # 25 minutes
_MD = f"# Vectors\n{_SECTION_ONE}\n\n# Matrices\n{_SECTION_TWO}\n"


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


class _Clock:
    def __init__(self, monkeypatch, start):
        self.moment = start
        monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: self.moment)

    def advance(self, **delta):
        self.moment += timedelta(**delta)


def _seed_as_you_read(paths, *, brief_mode="as_you_read") -> str:
    clock = FrozenClock(datetime(2026, 10, 1, 9, 0, tzinfo=UTC))
    repo = Repository(paths.sqlite_path)
    registered = register_source_revision(
        repo, acquisition_kind="textfile", canonical_uri="file:///book.md", raw_bytes=_MD.encode(),
        original_uri="file:///book.md", clock=clock,
    )
    ir = markdown_to_ir(_MD, title="Book", extractor_name="text")
    request_hash = extraction_request_hash(
        revision_id=registered.revision_id, extractor="text", extractor_version="1", ir_schema_version=IR_SCHEMA_VERSION
    )
    repo.insert_extraction_run(
        id="ext_book", revision_id=registered.revision_id, extractor="text", extractor_version="1",
        extraction_request_hash=request_hash, ir_schema_version=IR_SCHEMA_VERSION, status="running", clock=clock,
    )
    repo.persist_document_ir("ext_book", ir)
    repo.complete_extraction_run("ext_book", extraction_result_hash=extraction_result_hash(request_hash, ir), clock=clock)
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO synthesis_manifests(id, manifest_hash, extraction_ids_json, brief_json, created_at) VALUES (?, ?, ?, ?, ?)",
            ("man_1", "hash_1", json.dumps(["ext_book"]), json.dumps({"practice_items": brief_mode}), "2026-10-01T09:00:00Z"),
        )
        connection.execute(
            "INSERT INTO synthesis_runs(id, manifest_id, mode, status, created_at, completed_at) VALUES ('run_1', 'man_1', 'bootstrap', 'completed', ?, ?)",
            ("2026-10-01T09:00:00Z", "2026-10-01T09:05:00Z"),
        )
        connection.commit()
    return "ext_book"


@pytest.fixture
def reading_vault(tmp_path):
    paths = create_daily_plan_vault(tmp_path / "vault")
    _seed_as_you_read(paths)
    return paths


def _ctx(root):
    ctx = SidecarContext()
    ctx.load(root)
    ctx.grading_provider_override = "manual"
    return ctx


def _sections(repo, extraction_id):
    from learnloop.reader.reader_guidance import extraction_sections

    rows, _blocks, _spans = extraction_sections(repo.load_document_ir(extraction_id))
    return rows


def test_only_as_you_read_imports_offer_reading_and_words_left_shrinks_with_progress(tmp_path):
    paths = create_daily_plan_vault(tmp_path / "upfront")
    _seed_as_you_read(paths, brief_mode="upfront")
    assert as_you_read_extraction_ids(Repository(paths.sqlite_path)) == []

    other = create_daily_plan_vault(tmp_path / "asyouread")
    extraction_id = _seed_as_you_read(other)
    repo = Repository(other.sqlite_path)
    target = next_reading_target(repo)
    first, second = _sections(repo, extraction_id)[:2]
    assert target.section_id == first["id"] and target.words_left >= 1200
    span_count = len(first["span_ids"])
    repo.upsert_reader_section_progress(extraction_id=extraction_id, section_id=first["id"], spans_seen=0, span_count=max(span_count, 2))
    # Half the spans seen: half the words left.
    repo.upsert_reader_section_progress(extraction_id=extraction_id, section_id=first["id"], spans_seen=1, span_count=2)
    assert next_reading_target(repo).words_left == pytest.approx(target.words_left / 2, abs=1)
    repo.upsert_reader_section_progress(extraction_id=extraction_id, section_id=first["id"], completed=True)
    assert next_reading_target(repo).section_id == second["id"]


def _reading_step(ctx, session_id):
    for _ in range(20):
        step = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
        if step["kind"] == "reading":
            return step
        if step["kind"] == "done":
            return step
        _call(ctx, "next_plan_item", {"sessionId": session_id, "skipPracticeItemId": step["practiceItemId"]})
    raise AssertionError("no reading step")


def test_a_typed_reading_step_opens_the_section_and_progress_and_completion_end_it(reading_vault, monkeypatch):
    clock = _Clock(monkeypatch, DAY1)
    ctx = _ctx(reading_vault.root)
    _call(ctx, "set_plan_minutes", {"minutes": 40})
    session_id = _call(ctx, "start_session", {"availableMinutes": 40})["sessionId"]
    step = _reading_step(ctx, session_id)
    assert step["kind"] == "reading"
    reading = step["reading"]
    first = _sections(Repository(reading_vault.sqlite_path), "ext_book")[0]
    assert reading["extractionId"] == "ext_book" and reading["sectionId"] == first["id"]
    assert reading["sectionTitle"] == first["label"]
    assert reading["startSpanId"]
    # The words-left estimate: 1200 words at 120 wpm is 10 minutes; the block
    # takes what the new lane has left and says so when that is only part.
    assert reading["fullMinutes"] == pytest.approx(10.0, abs=0.2)
    assert step["estMinutes"] <= reading["fullMinutes"] + 1e-6
    assert reading["partial"] is (step["estMinutes"] < reading["fullMinutes"] - 1e-6)
    # Reader progress while the block is current becomes reading_progress.
    clock.advance(minutes=4)
    _call(ctx, "reader.mark_section_progress", {"extractionId": "ext_book", "sectionId": reading["sectionId"], "spansSeen": 1, "spanCount": 2})
    plan = _call(ctx, "get_daily_plan", {"sessionId": session_id})["plan"]
    current = next(block for block in plan["blocks"] if block["reading"])
    assert current["status"] == "current" and current["reading"]["spansSeen"] == 1
    # Completing the section ends the block and the plan moves on.
    clock.advance(minutes=4)
    _call(ctx, "reader.mark_section_progress", {"extractionId": "ext_book", "sectionId": reading["sectionId"], "completed": True})
    after = _call(ctx, "next_plan_item", {"sessionId": session_id})
    block = next(block for block in after["plan"]["blocks"] if block["reading"])
    assert block["outcome"] == "section_completed" and block["status"] == "done"
    assert after["step"]["kind"] != "reading"
    # At most one reading block a day.
    assert sum(1 for b in after["plan"]["blocks"] if b["reading"]) == 1


@pytest.mark.parametrize("outcome", ["left_reader", "skipped"])
def test_leaving_or_skipping_ends_the_block_and_counts_its_estimate(reading_vault, monkeypatch, outcome):
    _Clock(monkeypatch, DAY1)
    ctx = _ctx(reading_vault.root)
    _call(ctx, "set_plan_minutes", {"minutes": 40})
    session_id = _call(ctx, "start_session", {"availableMinutes": 40})["sessionId"]
    step = _reading_step(ctx, session_id)
    assert step["kind"] == "reading"
    before = _call(ctx, "get_daily_plan", {})["plan"]
    ended = _call(ctx, "plan_reading_ended", {"outcome": outcome, "sessionId": session_id})
    block = next(b for b in ended["plan"]["blocks"] if b["reading"])
    assert block["outcome"] == outcome and block["status"] == "done"
    assert ended["plan"]["totals"]["plannedMinutes"] == pytest.approx(before["totals"]["plannedMinutes"])
    assert ended["step"]["kind"] in ("item", "done")


def test_a_partial_block_when_the_section_exceeds_the_minutes_left(tmp_path, monkeypatch):
    paths = create_daily_plan_vault(tmp_path / "vault")
    extraction_id = _seed_as_you_read(paths)
    repo = Repository(paths.sqlite_path)
    first = _sections(repo, extraction_id)[0]
    repo.upsert_reader_section_progress(extraction_id=extraction_id, section_id=first["id"], completed=True)
    _Clock(monkeypatch, DAY1)
    ctx = _ctx(paths.root)
    _call(ctx, "set_plan_minutes", {"minutes": 60})
    session_id = _call(ctx, "start_session", {"availableMinutes": 60})["sessionId"]
    step = _reading_step(ctx, session_id)
    assert step["kind"] == "reading"
    reading = step["reading"]
    second = _sections(repo, extraction_id)[1]
    assert reading["sectionId"] == second["id"] and reading["partial"] is True
    assert reading["fullMinutes"] == pytest.approx(25.0, abs=0.5)
    assert step["estMinutes"] <= 15.0 + 1e-6  # never more than a block, the lane or the plan


def test_an_interrupted_block_resumes_and_the_next_day_continues_the_section(reading_vault, monkeypatch):
    clock = _Clock(monkeypatch, DAY1)
    ctx = _ctx(reading_vault.root)
    _call(ctx, "set_plan_minutes", {"minutes": 40})
    session_id = _call(ctx, "start_session", {"availableMinutes": 40})["sessionId"]
    step = _reading_step(ctx, session_id)
    section_id = step["reading"]["sectionId"]
    _call(ctx, "reader.mark_section_progress", {"extractionId": "ext_book", "sectionId": section_id, "spansSeen": 1, "spanCount": 2})
    # The app closes; reopening the plan reopens the reader at that section.
    reopened = _ctx(reading_vault.root)
    again = _call(reopened, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    assert again["kind"] == "reading" and again["reading"]["sectionId"] == section_id
    # The day ends first: the plan is abandoned, the progress is kept, and the
    # next day's reading block continues the same section with the words left.
    clock.advance(days=1)
    tomorrow = _call(reopened, "get_daily_plan", {})
    repository = Repository(reading_vault.sqlite_path)
    with repository.connection() as connection:
        statuses = [row[0] for row in connection.execute("SELECT status FROM daily_plans ORDER BY created_at")]
    assert statuses[0] == "abandoned"
    session_two = _call(reopened, "start_session", {"availableMinutes": 40})["sessionId"]
    next_day = _reading_step(reopened, session_two)
    assert next_day["kind"] == "reading" and next_day["reading"]["sectionId"] == section_id
    assert next_day["reading"]["wordsLeft"] < step["reading"]["wordsLeft"]
    assert tomorrow["plan"]["kind"] == "normal"


def test_reading_blocks_switch_off(tmp_path, monkeypatch):
    paths = create_daily_plan_vault(tmp_path / "vault", plan_toml="[plan]\nreading_blocks = false\n")
    _seed_as_you_read(paths)
    _Clock(monkeypatch, DAY1)
    ctx = _ctx(paths.root)
    plan = _call(ctx, "set_plan_minutes", {"minutes": 60})["plan"]
    assert not any(block["reading"] for block in plan["blocks"])
    assert not any(row["readingTitle"] for row in plan["projected"])
