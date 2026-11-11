"""Daily-loop DL1 §6.10: reading blocks (as-you-read, no pre-questions in DL1).

The words-left estimate; a partial block when the section exceeds the minutes
left; each ``block_ended`` outcome advancing the plan and consuming the
estimate; ``reading_progress`` events from ``reader.mark_section_progress``;
resuming an interrupted block; the next day continuing the same section;
``next_plan_item`` returning a typed reading step.
"""

from __future__ import annotations

import pytest

import learnloop_sidecar.handlers  # noqa: F401
from learnloop.daily_plan.reading import as_you_read_extraction_ids, next_reading_target
from learnloop.db.repositories import Repository
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.helpers import create_daily_plan_vault
from tests.daily_plan_reading_helpers import DAY1, _Clock, _sections, _seed_as_you_read

def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


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
